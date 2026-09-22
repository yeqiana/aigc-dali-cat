from __future__ import annotations

from pathlib import Path
import hashlib
import json

import episode_identity
import storage_config
import story_json


REL = Path("meta/frame-reviews")
REVIEW_TYPE = "FINAL"


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())


def _legacy_path(ep: Path, frame: int | str) -> Path:
    return Path(ep).resolve() / REL / f"{int(frame):02d}.json"


def _record(ep: Path, payload: dict) -> dict:
    frame = int(payload.get("frame") or 0)
    if frame < 1:
        raise ValueError("frame review requires frame")
    decision = str(payload.get("decision") or "").strip()
    if not decision:
        raise ValueError("frame review requires decision")
    return {
        "episode_id": _episode_id(ep),
        "frame_no": frame,
        "review_type": REVIEW_TYPE,
        "attempt_no": 1,
        "decision": decision,
        "asset_sha256": payload.get("asset_sha256"),
        "contract_sha256": payload.get("frame_contract_sha256"),
        "payload": payload,
    }


def persist(ep: Path, payload: dict) -> dict:
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_frame_review_repository import MySqlFrameReviewRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        saved = MySqlFrameReviewRepository(connection).upsert(_record(ep, payload))
        return {"mode": mode, "mysql_written": True, **saved}
    finally:
        connection.close()


def load(ep: Path, frame: int | str) -> dict | None:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_frame_review_repository import MySqlFrameReviewRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME
        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            row = MySqlFrameReviewRepository(connection).get_current(_episode_id(ep), int(frame), REVIEW_TYPE, 1)
            if row and isinstance(row.get("payload"), dict):
                return row["payload"]
        except Exception:
            if mode == "mysql":
                raise
        finally:
            if connection is not None:
                connection.close()
        if mode == "mysql":
            return None
    path = _legacy_path(ep, frame)
    return story_json.read_json(path, default=None) if path.is_file() else None


def list_all(ep: Path) -> list[dict]:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_frame_review_repository import MySqlFrameReviewRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME
        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            rows = MySqlFrameReviewRepository(connection).list_episode(_episode_id(ep))
            payloads = [row["payload"] for row in rows
                        if row.get("review_type") == REVIEW_TYPE and isinstance(row.get("payload"), dict)]
            if payloads:
                return payloads
        except Exception:
            if mode == "mysql":
                raise
        finally:
            if connection is not None:
                connection.close()
        if mode == "mysql":
            return []
    out = []
    review_dir = ep / REL
    if review_dir.is_dir():
        for path in sorted(review_dir.glob("[0-9][0-9].json")):
            data = story_json.read_json(path, default=None)
            if isinstance(data, dict):
                out.append(data)
    return out


def evidence_digest(ep: Path) -> dict:
    """Return a deterministic, file-independent proof of the current FINAL review set."""
    rows = sorted(
        (row for row in list_all(ep) if isinstance(row, dict)),
        key=lambda row: int(row.get("frame") or 0),
    )
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "storage": "mysql" if storage_config.episode_meta_store_config()["mode"] == "mysql" else "compatible",
        "review_type": REVIEW_TYPE,
        "count": len(rows),
        "frames": [str(row.get("frame") or "").zfill(2) for row in rows],
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def save(ep: Path, payload: dict) -> dict:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    frame = payload.get("frame")
    if frame in (None, ""):
        raise ValueError("frame review save requires frame")
    path = _legacy_path(ep, frame)
    if mode != "mysql":
        path.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(path, payload)
    db = persist(ep, payload)
    return {"path": path, **db}
