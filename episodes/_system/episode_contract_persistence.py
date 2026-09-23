from __future__ import annotations

import re
import sys
import contextvars
import hashlib
import json
import threading
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_identity
import mysql_connection_cache
import runtime_workspace
import storage_config
import story_json

from platform.repository.mysql.payload_policy import (
    MAX_INLINE_PAYLOAD_BYTES,
    document_reference,
    payload_bytes,
    payload_sha256,
)
from platform.repository.mysql.schema_v2 import DATABASE_NAME


DOC_ROOT = Path("meta/runtime/contracts/episode")


class _OperationCache:
    """Thread-safe positive-result cache scoped to one compile/verify call."""

    def __init__(self):
        self._lock = threading.Lock()
        self._values: dict[tuple, dict] = {}
        self._inflight: dict[tuple, threading.Event] = {}
        self._epochs: dict[tuple[str, str | None], int] = {}

    def get_or_load(self, key: tuple, loader):
        while True:
            with self._lock:
                if key in self._values:
                    return deepcopy(self._values[key])
                event = self._inflight.get(key)
                if event is None:
                    event = threading.Event()
                    self._inflight[key] = event
                    owner = True
                    epoch_key = (key[0], key[3])
                    epoch = self._epochs.get(epoch_key, 0)
                else:
                    owner = False
            if not owner:
                event.wait()
                continue
            try:
                value, cacheable = loader()
                if cacheable and isinstance(value, dict):
                    with self._lock:
                        if self._epochs.get(epoch_key, 0) == epoch:
                            self._values[key] = deepcopy(value)
                return deepcopy(value)
            finally:
                with self._lock:
                    self._inflight.pop(key, None)
                    event.set()

    def invalidate(self, episode_path: Path, contract_type: str | None = None) -> None:
        resolved = str(Path(episode_path).resolve())
        with self._lock:
            wanted_type = _safe_type(contract_type) if contract_type is not None else None
            types = {
                key[3] for key in (*self._values.keys(), *self._inflight.keys())
                if key[0] == resolved and (wanted_type is None or key[3] == wanted_type)
            }
            if wanted_type is not None:
                types.add(wanted_type)
            for current_type in types:
                epoch_key = (resolved, current_type)
                self._epochs[epoch_key] = self._epochs.get(epoch_key, 0) + 1
            for key in list(self._values):
                if key[0] == resolved and (
                    wanted_type is None or key[3] == wanted_type
                ):
                    self._values.pop(key, None)


_operation_cache = contextvars.ContextVar("episode_contract_operation_cache", default=None)


@contextmanager
def operation_scope():
    """Reuse one cache through nested calls; discard it when the top call ends."""
    existing = _operation_cache.get()
    if existing is not None:
        yield existing
        return
    cache = _OperationCache()
    token = _operation_cache.set(cache)
    try:
        yield cache
    finally:
        _operation_cache.reset(token)


def operation_cached(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with operation_scope():
            return function(*args, **kwargs)
    return wrapped


def invalidate(ep: Path, contract_type: str | None = None) -> None:
    cache = _operation_cache.get()
    if cache is not None:
        cache.invalidate(Path(ep), contract_type)


def _cache_key(ep: Path, mode: str, contract_type: str, legacy_path) -> tuple | None:
    try:
        kwargs = storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
        fingerprint = hashlib.sha256(
            json.dumps(kwargs, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    except Exception:
        return None
    legacy = str(Path(legacy_path).resolve()) if legacy_path is not None else ""
    return (str(ep.resolve()), mode, fingerprint, _safe_type(contract_type), legacy)


def _mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]


def _safe_type(contract_type: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(contract_type).strip())
    if not value:
        raise ValueError("contract_type required")
    return value[:64]


def _repository():
    from platform.repository.mysql.mysql_episode_contract_repository import (
        MySqlEpisodeContractRepository,
    )

    # A reused connection, not a fresh TCP handshake per read.  Callers must not
    # close it.  See mysql_connection_cache.
    connection = mysql_connection_cache.shared_connection(
        storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return connection, MySqlEpisodeContractRepository(connection)


def _externalize(ep: Path, contract_type: str, payload: dict) -> dict | None:
    if payload_bytes(payload) <= MAX_INLINE_PAYLOAD_BYTES:
        return None
    digest = payload_sha256(payload)
    rel = (DOC_ROOT / _safe_type(contract_type) / f"{digest}.json").as_posix()
    ref = document_reference(payload, rel)
    path = runtime_workspace.write_json(ep, rel, payload)
    ref["bytes"] = path.stat().st_size
    return ref


def persist(
    ep: Path,
    contract_type: str,
    payload: dict,
    *,
    status: str = "ACTIVE",
    source_sha256: str | None = None,
) -> dict:
    ep = Path(ep).resolve()
    mode = _mode()
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    if not isinstance(payload, dict):
        raise ValueError("episode contract payload must be object")
    _connection, repository = _repository()
    ref = _externalize(ep, contract_type, payload)
    saved = repository.save_version({
        "episode_id": episode_identity.storage_episode_id(ep),
        "contract_type": _safe_type(contract_type),
        "status": str(status),
        "sha256": payload_sha256(payload),
        "source_sha256": source_sha256,
        "payload": payload,
        "payload_ref": ref,
    })
    invalidate(ep, contract_type)
    return {
        "mode": mode,
        "mysql_written": True,
        "document_ref": ref,
        **saved,
    }


def load_latest(
    ep: Path,
    contract_type: str,
    *,
    legacy_path: str | Path | None = None,
) -> dict | None:
    ep = Path(ep).resolve()
    mode = _mode()
    cache = _operation_cache.get()
    key = _cache_key(ep, mode, contract_type, legacy_path) if cache is not None else None
    if cache is not None and key is not None:
        return cache.get_or_load(
            key,
            lambda: _load_latest_uncached(ep, contract_type, mode, legacy_path),
        )
    return _load_latest_uncached(ep, contract_type, mode, legacy_path)[0]


def _load_latest_uncached(
    ep: Path,
    contract_type: str,
    mode: str,
    legacy_path: str | Path | None,
) -> tuple[dict | None, bool]:
    if mode in {"dual", "mysql"}:
        try:
            _connection, repository = _repository()
            row = repository.get_latest(
                episode_identity.storage_episode_id(ep),
                _safe_type(contract_type),
            )
            if row and isinstance(row.get("payload"), dict):
                payload = row["payload"]
                document = (
                    payload.get("document")
                    if payload.get("projection_type") == "EPISODE_CONTRACT_REF"
                    else None
                )
                if isinstance(document, dict):
                    full = runtime_workspace.read_json(
                        ep, document.get("rel"), default=None
                    )
                    if (
                        isinstance(full, dict)
                        and payload_sha256(full)
                        == str(document.get("sha256") or "").lower()
                        and payload_sha256(full)
                        == str(row.get("sha256") or "").lower()
                    ):
                        return full, True
                else:
                    return payload, True
        except Exception:
            if mode == "mysql":
                raise
        if mode == "mysql":
            return None, False

    if legacy_path is not None:
        path = Path(legacy_path)
        if path.is_file():
            data = story_json.read_json(path, default=None)
            return (data, False) if isinstance(data, dict) else (None, False)
    return None, False


def save(
    ep: Path,
    contract_type: str,
    legacy_rel: str | Path,
    payload: dict,
    *,
    status: str = "ACTIVE",
    source_sha256: str | None = None,
) -> dict:
    ep = Path(ep).resolve()
    mode = _mode()
    db = persist(
        ep,
        contract_type,
        payload,
        status=status,
        source_sha256=source_sha256,
    )
    path = ep / Path(legacy_rel)
    if mode != "mysql":
        story_json.write_json(path, payload)
    invalidate(ep, contract_type)
    return {"path": path, **db}
