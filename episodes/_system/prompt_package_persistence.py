from __future__ import annotations

from pathlib import Path

import episode_identity
import storage_config
import story_json
import runtime_workspace
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, document_reference, payload_bytes, payload_sha256


PACKAGE_TYPE = "IMAGE"
REL = Path("meta/runtime/prompt-packages")


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())


def persist(ep: Path, payload: dict) -> dict:
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_prompt_package_repository import MySqlPromptPackageRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    frame = int(payload.get("frame") or 0)
    sha = str(payload.get("package_sha256") or "")
    if frame < 1 or not sha:
        raise ValueError("prompt package requires frame and package_sha256")
    document_ref = None
    if payload_bytes(payload) > MAX_INLINE_PAYLOAD_BYTES:
        digest = payload_sha256(payload)
        document_ref = document_reference(payload, f"meta/runtime/prompt-packages/{frame:02d}-{digest}.json")
        external = runtime_workspace.write_json(ep, document_ref["rel"], payload)
        document_ref["bytes"] = external.stat().st_size
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        saved = MySqlPromptPackageRepository(connection).upsert({
            "episode_id": _episode_id(ep),
            "frame_no": frame,
            "package_type": PACKAGE_TYPE,
            "sha256": sha,
            "payload": payload,
            "payload_ref": document_ref,
        })
        return {"mode": mode, "mysql_written": True, **saved}
    finally:
        connection.close()


def load_latest(ep: Path, frame: int | str) -> dict | None:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_prompt_package_repository import MySqlPromptPackageRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            row = MySqlPromptPackageRepository(connection).get_latest(_episode_id(ep), int(frame), PACKAGE_TYPE)
            if row and isinstance(row.get("payload"), dict):
                payload = row["payload"]
                document = payload.get("document") if payload.get("projection_type") == "PROMPT_PACKAGE_REF" else None
                if isinstance(document, dict):
                    full = runtime_workspace.read_json(ep, document.get("rel"), default=None)
                    if isinstance(full, dict) and payload_sha256(full) == str(document.get("sha256") or "").lower():
                        return full
                else:
                    return payload
        except Exception:
            pass
        finally:
            if connection is not None:
                connection.close()
    rel = REL / f"{int(frame):02d}.json"
    path = runtime_workspace.resolve_read_path(ep, rel)
    if path.is_file():
        return story_json.read_json(path, default=None)
    return None
