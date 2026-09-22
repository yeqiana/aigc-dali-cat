from __future__ import annotations

import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_identity
import runtime_workspace
import storage_config
import story_json

from platform.repository.mysql.payload_policy import (
    MAX_INLINE_PAYLOAD_BYTES,
    document_reference,
    payload_bytes,
    payload_sha256,
)


REL = Path("meta/runtime-request.json")
DOCUMENT_ROOT = Path("meta/runtime/requests")


def compatibility_path(ep: Path) -> Path:
    return Path(ep).resolve() / REL


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())


def _document_rel(payload: dict) -> Path:
    request_id = str(payload.get("request_id") or "runtime-request")
    digest = payload_sha256(payload)
    return DOCUMENT_ROOT / f"{request_id}-{digest}.json"


def _externalize_if_needed(ep: Path, payload: dict) -> dict | None:
    if payload_bytes(payload) <= MAX_INLINE_PAYLOAD_BYTES:
        return None
    rel = _document_rel(payload)
    path = runtime_workspace.write_json(Path(ep).resolve(), rel, payload)
    return document_reference(payload, rel.as_posix(), bytes_size=path.stat().st_size)


def _repository(ep: Path):
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_runtime_request_repository import (
        MySqlRuntimeRequestRepository,
    )
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return connection, MySqlRuntimeRequestRepository(connection)


def persist(ep: Path, payload: dict, *, status: str = "BOUND") -> dict:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    payload_ref = _externalize_if_needed(ep, payload)
    connection, repository = _repository(ep)
    try:
        request_id = str(payload.get("request_id") or "").strip()
        if not request_id:
            # Historical Runtime Requests predate request_id. Keep the payload
            # byte-for-byte equivalent while giving the DB row a deterministic
            # identity derived from its canonical fingerprint.
            request_id = "RR_MIG_" + payload_sha256(payload)[:48]
        saved = repository.upsert(
            {
                "runtime_request_id": request_id,
                "episode_id": _episode_id(ep),
                "request_type": str(payload.get("mode") or "UNKNOWN")[:32],
                "status": str(status)[:32],
                "fingerprint": payload_sha256(payload),
                "payload": payload,
                "payload_ref": payload_ref,
            }
        )
        return {
            "mode": mode,
            "mysql_written": True,
            "document_ref": payload_ref,
            **saved,
        }
    finally:
        connection.close()


def _resolve_payload(ep: Path, row: dict) -> dict | None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    if payload.get("projection_type") != "RUNTIME_REQUEST_REF":
        return payload
    document = payload.get("document")
    if not isinstance(document, dict):
        raise ValueError("runtime request projection missing document reference")
    full = runtime_workspace.read_json(ep, document.get("rel"), default=None)
    if not isinstance(full, dict):
        raise ValueError("runtime request authority document missing")
    if payload_sha256(full) != str(document.get("sha256") or "").lower():
        raise ValueError("runtime request authority document sha256 mismatch")
    return full


def load(ep: Path, request_id: str | None = None) -> dict | None:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        connection = None
        try:
            connection, repository = _repository(ep)
            row = (
                repository.get_by_id(str(request_id))
                if request_id
                else repository.get_latest(_episode_id(ep))
            )
            if row:
                resolved = _resolve_payload(ep, row)
                if isinstance(resolved, dict):
                    return resolved
        except Exception:
            if mode == "mysql":
                raise
        finally:
            if connection is not None:
                connection.close()
        if mode == "mysql":
            return None
    path = compatibility_path(ep)
    return story_json.read_json(path, default=None) if path.is_file() else None
