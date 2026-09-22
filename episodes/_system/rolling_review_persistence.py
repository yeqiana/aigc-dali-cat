from __future__ import annotations

from pathlib import Path

import episode_identity
import storage_config
import story_json


REL = Path("meta/runtime/rolling-reviews")
REVIEW_TYPE = "ROLLING"


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())


def _legacy_path(ep: Path, frame: int | str, attempt_no: int) -> Path:
    return Path(ep).resolve() / REL / f"{int(frame):02d}-{int(attempt_no)}.json"


def _record(ep: Path, payload: dict, attempt_no: int) -> dict:
    frame = int(payload.get("frame") or 0)
    if frame < 1:
        raise ValueError("rolling review requires frame")
    decision = str(payload.get("decision") or "").strip()
    if not decision:
        raise ValueError("rolling review requires decision")
    if int(attempt_no) < 1:
        raise ValueError("rolling review requires positive attempt_no")
    return {
        "episode_id": _episode_id(ep),
        "frame_no": frame,
        "review_type": REVIEW_TYPE,
        "attempt_no": int(attempt_no),
        "decision": decision,
        "asset_sha256": payload.get("asset_sha256"),
        "contract_sha256": payload.get("frame_contract_sha256"),
        "payload": payload,
    }


def persist(ep: Path, payload: dict, *, attempt_no: int) -> dict:
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_frame_review_repository import MySqlFrameReviewRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        saved = MySqlFrameReviewRepository(connection).upsert(_record(ep, payload, attempt_no))
        return {"mode": mode, "mysql_written": True, **saved}
    finally:
        connection.close()


def load(ep: Path, frame: int | str, attempt_no: int) -> dict | None:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_frame_review_repository import MySqlFrameReviewRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            row = MySqlFrameReviewRepository(connection).get_current(
                _episode_id(ep), int(frame), REVIEW_TYPE, int(attempt_no)
            )
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
    path = _legacy_path(ep, frame, attempt_no)
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
            result = [
                {"attempt_no": int(row.get("attempt_no") or 0), "payload": row["payload"]}
                for row in rows
                if row.get("review_type") == REVIEW_TYPE and isinstance(row.get("payload"), dict)
            ]
            if result:
                return sorted(result, key=lambda x: (int(x["payload"].get("frame") or 0), x["attempt_no"]))
        except Exception:
            if mode == "mysql":
                raise
        finally:
            if connection is not None:
                connection.close()
        if mode == "mysql":
            return []
    result = []
    root = ep / REL
    if root.is_dir():
        for path in sorted(root.glob("[0-9][0-9]-*.json")):
            try:
                frame_text, attempt_text = path.stem.split("-", 1)
                payload = story_json.read_json(path, default=None)
                if isinstance(payload, dict):
                    result.append({"attempt_no": int(attempt_text), "payload": payload})
            except (TypeError, ValueError):
                continue
    return result


def save(ep: Path, payload: dict, *, attempt_no: int, candidate_path: Path | None = None) -> dict:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    frame = int(payload.get("frame") or 0)
    if frame < 1:
        raise ValueError("rolling review save requires frame")
    path = _legacy_path(ep, frame, attempt_no)
    if mode != "mysql":
        path.parent.mkdir(parents=True, exist_ok=True)
        if candidate_path is not None and Path(candidate_path).resolve() == path.resolve() and path.is_file():
            pass
        else:
            story_json.write_json(path, payload)
    db = persist(ep, payload, attempt_no=attempt_no)
    if mode == "mysql" and candidate_path is not None:
        Path(candidate_path).unlink(missing_ok=True)
    return {"path": path, **db}
