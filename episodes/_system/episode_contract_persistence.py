from __future__ import annotations

import re
import sys
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
                        return full
                else:
                    return payload
        except Exception:
            if mode == "mysql":
                raise
        if mode == "mysql":
            return None

    if legacy_path is not None:
        path = Path(legacy_path)
        if path.is_file():
            data = story_json.read_json(path, default=None)
            return data if isinstance(data, dict) else None
    return None


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
    return {"path": path, **db}
