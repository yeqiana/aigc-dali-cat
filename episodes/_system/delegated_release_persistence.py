from __future__ import annotations

from pathlib import Path

import episode_identity
import storage_config
import story_json
import runtime_workspace
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, document_reference, payload_bytes, payload_sha256


REL = Path("meta/delegated-release.json")
LEGACY_REL = Path("meta/DELEGATED_AUTO_REPORT.json")
RELEASE_TYPE = "DELEGATED_DELIVERY"
LEGACY_RELEASE_TYPE = "DELEGATED_AUTO_LEGACY"


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())


def _record(ep: Path, payload: dict, release_type: str) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("delegated release payload must be object")
    package = payload.get("package") or {}
    ready = isinstance(package, dict) and bool(package.get("path")) and bool(package.get("sha256"))
    return {
        "episode_id": _episode_id(ep),
        "release_type": release_type,
        "status": "READY" if ready else "RECORDED",
        "snapshot_sha256": package.get("sha256") if isinstance(package, dict) else None,
        "payload": payload,
    }


def persist(ep: Path, payload: dict, *, release_type: str = RELEASE_TYPE) -> dict:
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_release_record_repository import MySqlReleaseRecordRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        document_ref = None
        if payload_bytes(payload) > MAX_INLINE_PAYLOAD_BYTES:
            digest = payload_sha256(payload)
            document_ref = document_reference(payload, f"meta/runtime/releases/{release_type}-{digest}.json")
            external = runtime_workspace.write_json(ep, document_ref["rel"], payload)
            document_ref["bytes"] = external.stat().st_size
        record = _record(ep, payload, release_type)
        record["payload_ref"] = document_ref
        saved = MySqlReleaseRecordRepository(connection).upsert(record)
        return {"mode": mode, "mysql_written": True, **saved}
    finally:
        connection.close()


def load(ep: Path, *, release_type: str = RELEASE_TYPE) -> dict | None:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_release_record_repository import MySqlReleaseRecordRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            row = MySqlReleaseRecordRepository(connection).get_current(_episode_id(ep), release_type)
            if row and isinstance(row.get("payload"), dict):
                payload = row["payload"]
                document = payload.get("document") if payload.get("projection_type") == "RELEASE_RECORD_REF" else None
                if isinstance(document, dict):
                    full = runtime_workspace.read_json(ep, document.get("rel"), default=None)
                    if isinstance(full, dict) and payload_sha256(full) == str(document.get("sha256") or "").lower():
                        return full
                else:
                    return payload
        except Exception:
            if mode == "mysql":
                raise
        finally:
            if connection is not None:
                connection.close()
        if mode == "mysql":
            return None
    path = ep / (REL if release_type == RELEASE_TYPE else LEGACY_REL)
    return story_json.read_json(path, default=None) if path.is_file() else None


def exists(ep: Path) -> bool:
    return isinstance(load(ep), dict)


def save(ep: Path, payload: dict) -> dict:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    path = ep / REL
    if mode != "mysql":
        path.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(path, payload)
    db = persist(ep, payload)
    return {"path": path, **db}
