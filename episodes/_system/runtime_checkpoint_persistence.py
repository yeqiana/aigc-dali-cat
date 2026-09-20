from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_identity
import storage_config

from platform.repository.mysql.schema_v2 import DATABASE_NAME


META_TASK_TYPE = "RUNTIME_CHECKPOINT_META"
STEP_TASK_TYPE = "RUNTIME_CHECKPOINT_STEP"


def mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]


def projection_run_id(ep: Path) -> str:
    episode_id = episode_identity.storage_episode_id(Path(ep).resolve())
    digest = hashlib.sha256(
        f"runtime-checkpoint|{episode_id}".encode("utf-8")
    ).hexdigest()[:48]
    return "WR_CP_" + digest


def _task_id(run_id: str, kind: str, seq: int, payload: dict) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    raw = f"{run_id}|{kind}|{int(seq)}|{canonical}".encode("utf-8")
    return "TASK_CP_" + hashlib.sha256(raw).hexdigest()[:64]


def _repositories():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_task_repository import MySqlTaskRepository
    from platform.repository.mysql.mysql_workflow_run_repository import (
        MySqlWorkflowRunRepository,
    )

    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return (
        connection,
        MySqlWorkflowRunRepository(connection),
        MySqlTaskRepository(connection),
    )


def _meta_payload(data: dict) -> dict:
    result = deepcopy(data)
    result["_step_runs_present"] = "step_runs" in data
    result.pop("step_runs", None)
    return result


def persist(ep: Path, data: dict) -> dict:
    ep = Path(ep).resolve()
    current_mode = mode()
    if current_mode == "json":
        return {"mode": current_mode, "mysql_written": False}
    episode_id = episode_identity.storage_episode_id(ep)
    run_id = projection_run_id(ep)
    rows = [
        row for row in (data.get("step_runs") or [])
        if isinstance(row, dict)
    ][-200:]
    first_start = next(
        (row.get("started_at") for row in rows if row.get("started_at")),
        data.get("updated_at"),
    )
    connection, runs, tasks = _repositories()
    try:
        with connection.transaction():
            runs.upsert({
                "workflow_run_id": run_id,
                "episode_id": episode_id,
                "runtime_type": str(data.get("runtime") or "CHECKPOINT"),
                "run_reason": "RECOVERY_PROJECTION",
                "status": "CURRENT",
                "start_time": first_start,
                "end_time": None,
            })
            tasks.delete_run_projection(run_id)
            meta = _meta_payload(data)
            tasks.upsert({
                "task_id": _task_id(run_id, META_TASK_TYPE, 0, meta),
                "episode_id": episode_id,
                "workflow_run_id": run_id,
                "task_type": META_TASK_TYPE,
                "status": "CURRENT",
                "attempt_no": 1,
                "owner_id": "runtime_checkpoint",
                "start_time": first_start,
                "end_time": data.get("updated_at"),
                "payload": {"_checkpoint_seq": 0, **meta},
            })
            for seq, row in enumerate(rows, 1):
                payload = {"_checkpoint_seq": seq, **deepcopy(row)}
                tasks.upsert({
                    "task_id": _task_id(run_id, STEP_TASK_TYPE, seq, payload),
                    "episode_id": episode_id,
                    "workflow_run_id": run_id,
                    "task_type": STEP_TASK_TYPE,
                    "status": str(row.get("status") or "UNKNOWN"),
                    "attempt_no": max(1, int(row.get("attempt") or 1)),
                    "owner_id": "runtime_checkpoint",
                    "start_time": row.get("started_at"),
                    "end_time": row.get("finished_at"),
                    "payload": payload,
                })
    finally:
        connection.close()
    return {
        "mode": current_mode,
        "mysql_written": True,
        "workflow_run_id": run_id,
        "step_count": len(rows),
    }


def _load_mysql(ep: Path) -> dict | None:
    ep = Path(ep).resolve()
    run_id = projection_run_id(ep)
    connection = None
    try:
        connection, runs, tasks = _repositories()
        if runs.get(run_id) is None:
            return None
        rows = tasks.list_run(run_id)
        meta = None
        steps = []
        for row in rows:
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            if row.get("task_type") == META_TASK_TYPE:
                meta = dict(payload)
                meta.pop("_checkpoint_seq", None)
            elif row.get("task_type") == STEP_TASK_TYPE:
                item = dict(payload)
                seq = int(item.pop("_checkpoint_seq", 0) or 0)
                steps.append((seq, item))
        if meta is None:
            return None
        step_runs_present = bool(meta.pop("_step_runs_present", False))
        rebuilt_steps = [row for _seq, row in sorted(steps, key=lambda x: x[0])][-200:]
        if step_runs_present or rebuilt_steps:
            meta["step_runs"] = rebuilt_steps
        return meta
    finally:
        if connection is not None:
            connection.close()


def load(ep: Path) -> dict | None:
    ep = Path(ep).resolve()
    current_mode = mode()
    if current_mode in {"dual", "mysql"}:
        try:
            data = _load_mysql(ep)
            if isinstance(data, dict):
                return data
        except Exception:
            if current_mode == "mysql":
                raise
        if current_mode == "mysql":
            return None
    return None
