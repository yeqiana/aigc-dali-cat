from __future__ import annotations

from pathlib import Path

import episode_identity
import runtime_workspace
import storage_config
import story_json


REL = Path("meta/runtime/host-requests")


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())


def request_rel(request_id: str) -> Path:
    return REL / f"{str(request_id)}.json"


def compatibility_path(ep: Path, request_id: str) -> Path:
    return runtime_workspace.workspace_path(Path(ep).resolve(), request_rel(request_id))


def _request_type(payload: dict) -> str:
    request_id = str(payload.get("request_id") or "")
    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    return str(
        payload.get("next_step")
        or task.get("task_type")
        or payload.get("request_type")
        or request_id.partition("-")[0]
        or "HOST"
    )[:64]


def _record(ep: Path, payload: dict) -> dict:
    request_id = str(payload.get("request_id") or "").strip()
    if not request_id:
        raise ValueError("host request requires request_id")
    return {
        "host_request_id": request_id,
        "episode_id": _episode_id(ep),
        "request_type": _request_type(payload),
        "status": str(payload.get("status") or "UNKNOWN"),
        "worker_id": payload.get("worker_id"),
        "fingerprint": payload.get("request_fingerprint"),
        "start_time": payload.get("started_at"),
        "end_time": payload.get("finished_at") or payload.get("finalized_at") or payload.get("completed_at"),
        "payload": payload,
    }


def save(ep: Path, payload: dict) -> dict:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    request_id = str(payload.get("request_id") or "").strip()
    path = compatibility_path(ep, request_id)
    if mode != "mysql":
        path = runtime_workspace.write_json(ep, request_rel(request_id), payload)
    mysql_written = False
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_host_request_repository import MySqlHostRequestRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
        try:
            MySqlHostRequestRepository(connection).upsert(_record(ep, payload))
            mysql_written = True
        finally:
            connection.close()
    return {"mode": mode, "mysql_written": mysql_written, "path": path}


def load(ep: Path, request_id: str) -> dict | None:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_host_request_repository import MySqlHostRequestRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            row = MySqlHostRequestRepository(connection).get_by_id(str(request_id))
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
    for path in runtime_workspace.read_candidates(ep, request_rel(request_id)):
        if path.is_file():
            data = story_json.read_json(path, default=None)
            if isinstance(data, dict):
                return data
    return None


def list_all(ep: Path) -> list[dict]:
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    rows: dict[str, dict] = {}
    if mode in {"dual", "mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_host_request_repository import MySqlHostRequestRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = None
        try:
            connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
            for row in MySqlHostRequestRepository(connection).list_by_episode(_episode_id(ep)):
                payload = row.get("payload")
                if isinstance(payload, dict) and payload.get("request_id"):
                    rows[str(payload["request_id"])] = payload
        except Exception:
            if mode == "mysql":
                raise
        finally:
            if connection is not None:
                connection.close()
        if mode == "mysql":
            return list(rows.values())
    for history in runtime_workspace.read_candidates(ep, REL):
        if not history.is_dir():
            continue
        for path in sorted(history.glob("*.json")):
            data = story_json.read_json(path, default=None)
            if isinstance(data, dict) and data.get("request_id"):
                rows.setdefault(str(data["request_id"]), data)
    return list(rows.values())
