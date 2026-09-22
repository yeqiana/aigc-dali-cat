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
import runtime_workspace
import storage_config

from platform.repository.mysql.schema_v2 import DATABASE_NAME
from platform.repository.mysql.payload_policy import (
    document_reference,
    payload_bytes,
    payload_sha256,
)


META_TASK_TYPE = "RUNTIME_CHECKPOINT_META"
STEP_TASK_TYPE = "RUNTIME_CHECKPOINT_STEP"
RUNNER_EVENTS_REL = "meta/runtime/checkpoint-events"
RUNNER_EVENTS_PROJECTION = "RUNTIME_CHECKPOINT_EVENTS_REF"


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


def _runner_events_reference(ep: Path, events: list) -> dict:
    """Persist lifecycle events as an immutable external document.

    ``TB_TASK.PAYLOAD`` is a bounded query projection.  Runner events are
    append-only evidence and are therefore stored in the Runtime Workspace;
    the MySQL row keeps only a typed reference and content hashes.
    """
    digest = payload_sha256(events)
    rel = f"{RUNNER_EVENTS_REL}/{digest}.json"
    external = runtime_workspace.write_json(ep, rel, events)
    reference = document_reference(events, rel, bytes_size=external.stat().st_size)
    return {
        "projection_type": RUNNER_EVENTS_PROJECTION,
        "projection_version": 1,
        "event_count": len(events),
        "source_sha256": digest,
        "source_bytes": payload_bytes(events),
        "document": reference,
    }


def _meta_payload(ep: Path, data: dict) -> dict:
    result = deepcopy(data)
    result["_step_runs_present"] = "step_runs" in data
    result.pop("step_runs", None)
    events = result.pop("runner_events", None)
    if isinstance(events, list):
        result["runner_events_ref"] = _runner_events_reference(ep, events)
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
            meta = _meta_payload(ep, data)
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
        events_ref = meta.pop("runner_events_ref", None)
        if isinstance(events_ref, dict):
            document = events_ref.get("document")
            if not isinstance(document, dict):
                raise ValueError("runtime checkpoint runner_events document reference missing")
            events = runtime_workspace.read_json(ep, document.get("rel"), default=None)
            if not isinstance(events, list):
                raise ValueError("runtime checkpoint runner_events document missing")
            expected_sha = str(document.get("sha256") or events_ref.get("source_sha256") or "").lower()
            actual_sha = payload_sha256(events)
            if not expected_sha or actual_sha != expected_sha:
                raise ValueError("runtime checkpoint runner_events sha256 mismatch")
            if events_ref.get("event_count") is not None and int(events_ref["event_count"]) != len(events):
                raise ValueError("runtime checkpoint runner_events event_count mismatch")
            meta["runner_events"] = events
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
