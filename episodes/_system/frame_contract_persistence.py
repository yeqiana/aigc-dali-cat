from __future__ import annotations

import hashlib
import json
from pathlib import Path

import storage_config
import story_json


def _episode_id(ep: Path) -> str:
    state = story_json.read_json(Path(ep) / "meta/episode-state.json", default={})
    return str((state or {}).get("episode_id") or Path(ep).name)


def _source_sha(row: dict) -> str | None:
    material = row.get("hash_material")
    if not isinstance(material, dict) or not material:
        return None
    payload = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def persist(ep: Path, row: dict, *, status: str = "ACTIVE") -> dict:
    """Mirror a resolved Frame Contract when Episode metadata mode is ``dual``."""
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}

    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_frame_contract_repository import (
        MySqlFrameContractRepository,
    )
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    kwargs = storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    connection = MySqlConnection(**kwargs)
    try:
        saved = MySqlFrameContractRepository(connection).save_version(
            {
                "episode_id": _episode_id(Path(ep).resolve()),
                "frame_no": int(row["frame"]),
                "status": status,
                "sha256": row["contract_sha256"],
                "source_sha256": _source_sha(row),
                "payload": row,
            }
        )
        return {"mode": mode, "mysql_written": True, **saved}
    finally:
        connection.close()

