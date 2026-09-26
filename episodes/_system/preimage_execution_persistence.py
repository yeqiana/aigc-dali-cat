"""Durable PREIMAGE Agent execution eligibility and commit receipts.

Runtime evidence only. Canonical creative authority remains in existing StoryOS
authority documents and authority_commit.py.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import episode_identity
import runtime_atomic_store as atomic
import storage_config

from platform.repository.mysql.schema_v2 import DATABASE_NAME

REL = Path("meta/runtime/preimage-executions.json")
TASK_TYPE = "PREIMAGE_AGENT_EXECUTION"
SCHEMA_VERSION = 1

ELIGIBLE = {"ACTIVE", "CANDIDATE_READY", "PREPARED"}
TERMINAL = {"COMMITTED", "SUPERSEDED", "DUPLICATE_REJECTED", "SHADOW_COMPLETED", "SHADOW_FAILED"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")


def mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]


def workflow_run_id(ep: Path, snapshot_id: str) -> str:
    episode_id = episode_identity.storage_episode_id(Path(ep).resolve())
    raw = f"preimage-agent|{episode_id}|{snapshot_id}".encode("utf-8")
    return "WR_PRE_" + hashlib.sha256(raw).hexdigest()[:48]


def record_id(task_id: str, execution_id: str) -> str:
    raw = f"{task_id}|{execution_id}".encode("utf-8")
    return "TASK_PRE_EXEC_" + hashlib.sha256(raw).hexdigest()[:64]


def _json_path(ep: Path) -> Path:
    return Path(ep).resolve() / REL


def _json_default(snapshot_id: str | None = None) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "records": [],
        "updated_at": now(),
    }


def _mysql_repositories():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_task_repository import MySqlTaskRepository
    from platform.repository.mysql.mysql_workflow_run_repository import MySqlWorkflowRunRepository

    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return connection, MySqlWorkflowRunRepository(connection), MySqlTaskRepository(connection)


def _decode_task_row(row: dict) -> dict:
    payload = dict(row.get("payload") or {})
    payload.setdefault("status", row.get("status"))
    payload.setdefault("attempt", int(row.get("attempt_no") or 1))
    payload.setdefault("execution_id", row.get("owner_id"))
    return payload


def _load_mysql(ep: Path, snapshot_id: str) -> list[dict]:
    connection = None
    try:
        connection, _runs, tasks = _mysql_repositories()
        rows = tasks.list_run(workflow_run_id(ep, snapshot_id))
        return [
            _decode_task_row(row)
            for row in rows
            if row.get("task_type") == TASK_TYPE and isinstance(row.get("payload"), dict)
        ]
    finally:
        if connection is not None:
            connection.close()


def load_records(ep: Path, snapshot_id: str) -> list[dict]:
    ep = Path(ep).resolve()
    current_mode = mode()
    if current_mode in {"mysql", "dual"}:
        try:
            rows = _load_mysql(ep, snapshot_id)
            if rows or current_mode == "mysql":
                return rows
        except Exception:
            if current_mode == "mysql":
                raise
    data = atomic.read_json(_json_path(ep), _json_default(snapshot_id))
    if not isinstance(data, dict) or data.get("snapshot_id") not in {None, snapshot_id}:
        return []
    return [dict(x) for x in (data.get("records") or []) if isinstance(x, dict)]


def _persist_mysql(ep: Path, snapshot_id: str, record: dict) -> None:
    connection = None
    try:
        connection, runs, tasks = _mysql_repositories()
        run_id = workflow_run_id(ep, snapshot_id)
        episode_id = episode_identity.storage_episode_id(ep)
        with connection.transaction():
            runs.upsert(
                {
                    "workflow_run_id": run_id,
                    "episode_id": episode_id,
                    "runtime_type": "AGENT",
                    "run_reason": "PREIMAGE_AGENT_EXECUTION",
                    "status": "CURRENT",
                    "start_time": record.get("started_at"),
                    "end_time": None,
                }
            )
            tasks.upsert(
                {
                    "task_id": record_id(record["task_id"], record["execution_id"]),
                    "episode_id": episode_id,
                    "workflow_run_id": run_id,
                    "task_type": TASK_TYPE,
                    "status": record["status"],
                    "attempt_no": int(record["attempt"]),
                    "owner_id": record["execution_id"],
                    "start_time": record.get("started_at"),
                    "end_time": record.get("finished_at"),
                    "payload": record,
                }
            )
    finally:
        if connection is not None:
            connection.close()


def _persist_json(ep: Path, snapshot_id: str, record: dict) -> None:
    path = _json_path(ep)

    def mutate(data: dict) -> dict:
        if data.get("snapshot_id") != snapshot_id:
            data.clear()
            data.update(_json_default(snapshot_id))
        rows = data.setdefault("records", [])
        rid = (record["task_id"], record["execution_id"])
        existing = next(
            (
                row
                for row in rows
                if (row.get("task_id"), row.get("execution_id")) == rid
            ),
            None,
        )
        if existing is None:
            rows.append(dict(record))
        else:
            existing.clear()
            existing.update(dict(record))
        data["updated_at"] = now()
        return dict(record)

    atomic.update_json(path, lambda: _json_default(snapshot_id), mutate)


def save_record(ep: Path, snapshot_id: str, record: dict) -> dict:
    ep = Path(ep).resolve()
    current_mode = mode()
    if current_mode != "mysql":
        _persist_json(ep, snapshot_id, record)
    if current_mode in {"mysql", "dual"}:
        _persist_mysql(ep, snapshot_id, record)
    return dict(record)


def find_by_idempotency(ep: Path, snapshot_id: str, idempotency_key: str) -> dict | None:
    return next(
        (
            row
            for row in reversed(load_records(ep, snapshot_id))
            if row.get("idempotency_key") == idempotency_key
        ),
        None,
    )


def find_execution(ep: Path, snapshot_id: str, task_id: str, execution_id: str) -> dict | None:
    return next(
        (
            row
            for row in reversed(load_records(ep, snapshot_id))
            if row.get("task_id") == task_id and row.get("execution_id") == execution_id
        ),
        None,
    )


def begin_execution(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    attempt: int,
    idempotency_key: str,
    shadow: bool = False,
    trace_id: str | None = None,
) -> dict:
    ep = Path(ep).resolve()
    attempt = int(attempt)
    if attempt < 1:
        raise ValueError("PREIMAGE execution attempt must be >= 1")
    replay = find_by_idempotency(ep, snapshot_id, idempotency_key)
    if replay is not None:
        return replay
    rows = [
        row for row in load_records(ep, snapshot_id)
        if row.get("task_id") == task_id and bool(row.get("shadow")) == bool(shadow)
    ]
    committed = next((row for row in rows if row.get("status") == "COMMITTED"), None)
    prepared = next((row for row in rows if row.get("status") == "PREPARED"), None)
    if prepared is not None:
        return {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "shadow": bool(shadow),
            "status": "COMMIT_IN_PROGRESS",
            "eligible": False,
            "reason": "prepared commit must resolve before a newer attempt may start",
            "started_at": now(),
            "updated_at": now(),
        }
    if committed is not None:
        return {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "shadow": bool(shadow),
            "status": "ALREADY_COMMITTED",
            "eligible": False,
            "reason": "task already committed for this snapshot",
            "started_at": now(),
            "updated_at": now(),
        }
    same_attempt = next((row for row in rows if int(row.get("attempt") or 0) == attempt), None)
    if same_attempt is not None:
        return {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "shadow": bool(shadow),
            "status": "DUPLICATE_REJECTED",
            "eligible": False,
            "reason": "attempt already owned by another execution",
            "started_at": now(),
            "updated_at": now(),
        }
    max_attempt = max((int(row.get("attempt") or 0) for row in rows), default=0)
    if attempt < max_attempt:
        return {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "shadow": bool(shadow),
            "status": "SUPERSEDED",
            "eligible": False,
            "reason": f"newer attempt already exists: {max_attempt}",
            "started_at": now(),
            "updated_at": now(),
        }
    if attempt > max_attempt:
        for old in rows:
            if old.get("status") in ELIGIBLE:
                old["status"] = "SUPERSEDED"
                old["eligible"] = False
                old["finished_at"] = now()
                old["updated_at"] = now()
                save_record(ep, snapshot_id, old)
    stamp = now()
    record = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "task_id": task_id,
        "execution_id": execution_id,
        "attempt": attempt,
        "idempotency_key": idempotency_key,
        "shadow": bool(shadow),
        "trace_id": trace_id,
        "status": "ACTIVE",
        "eligible": not bool(shadow),
        "started_at": stamp,
        "updated_at": stamp,
        "finished_at": None,
        "commit_receipt": None,
    }
    return save_record(ep, snapshot_id, record)


def mark_candidate_ready(
    ep: Path, *, snapshot_id: str, task_id: str, execution_id: str
) -> dict:
    record = find_execution(ep, snapshot_id, task_id, execution_id)
    if record is None:
        raise ValueError("PREIMAGE execution not found")
    if record.get("status") != "ACTIVE":
        raise ValueError(f"execution not ACTIVE: {record.get('status')}")
    record["status"] = "CANDIDATE_READY"
    record["updated_at"] = now()
    return save_record(ep, snapshot_id, record)


def mark_shadow_completed(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    candidate_sha256: str,
    comparison_status: str | None = None,
    execution_evidence: dict | None = None,
) -> dict:
    record = find_execution(ep, snapshot_id, task_id, execution_id)
    if record is None:
        raise ValueError("PREIMAGE shadow execution not found")
    if record.get("shadow") is not True:
        raise ValueError("mark_shadow_completed requires shadow execution")
    if record.get("status") not in {"ACTIVE", "CANDIDATE_READY", "SHADOW_COMPLETED"}:
        raise ValueError(f"shadow execution not completable: {record.get('status')}")
    record["status"] = "SHADOW_COMPLETED"
    record["eligible"] = False
    record["shadow_result"] = {
        "candidate_sha256": str(candidate_sha256),
        "comparison_status": comparison_status,
        "execution_evidence": dict(execution_evidence or {}),
    }
    record["finished_at"] = record.get("finished_at") or now()
    record["updated_at"] = now()
    return save_record(ep, snapshot_id, record)


def mark_execution_failed(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    reason: str,
    failure_kind: str = "TECHNICAL",
) -> dict:
    record = find_execution(ep, snapshot_id, task_id, execution_id)
    if record is None:
        raise ValueError("PREIMAGE execution not found")
    if record.get("status") in {"COMMITTED", "PREPARED"}:
        raise ValueError(f"cannot fail execution in {record.get('status')} state")
    record["status"] = "FAILED"
    record["eligible"] = False
    record["failure_kind"] = str(failure_kind)
    record["failure_reason"] = str(reason)
    record["finished_at"] = record.get("finished_at") or now()
    record["updated_at"] = now()
    return save_record(ep, snapshot_id, record)


def mark_shadow_failed(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    reason: str,
) -> dict:
    record = find_execution(ep, snapshot_id, task_id, execution_id)
    if record is None:
        raise ValueError("PREIMAGE shadow execution not found")
    if record.get("shadow") is not True:
        raise ValueError("mark_shadow_failed requires shadow execution")
    record["status"] = "SHADOW_FAILED"
    record["eligible"] = False
    record["failure_reason"] = str(reason)
    record["finished_at"] = record.get("finished_at") or now()
    record["updated_at"] = now()
    return save_record(ep, snapshot_id, record)


def eligibility(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    attempt: int,
    idempotency_key: str,
) -> dict:
    record = find_execution(ep, snapshot_id, task_id, execution_id)
    if record is None:
        return {"eligible": False, "status": "MISSING"}
    matches = (
        int(record.get("attempt") or 0) == int(attempt)
        and record.get("idempotency_key") == idempotency_key
    )
    return {
        "eligible": bool(matches and record.get("eligible") and record.get("status") in ELIGIBLE),
        "status": record.get("status"),
        "record": record,
    }


def prepare_commit(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    attempt: int,
    idempotency_key: str,
    input_sha: str,
    output_sha: str,
) -> dict:
    state = eligibility(
        ep,
        snapshot_id=snapshot_id,
        task_id=task_id,
        execution_id=execution_id,
        attempt=attempt,
        idempotency_key=idempotency_key,
    )
    if not state["eligible"]:
        raise PermissionError(f"PREIMAGE execution not eligible: {state['status']}")
    record = dict(state["record"])
    existing = record.get("commit_receipt")
    if isinstance(existing, dict) and existing.get("status") in {"PREPARED", "COMMITTED"}:
        if existing.get("input_sha") != input_sha or existing.get("output_sha") != output_sha:
            raise ValueError("commit receipt SHA plan mismatch")
        return record
    receipt = {
        "status": "PREPARED",
        "idempotency_key": idempotency_key,
        "execution_id": execution_id,
        "attempt": int(attempt),
        "input_sha": input_sha,
        "output_sha": output_sha,
        "prepared_at": now(),
        "committed_at": None,
        "commit_id": None,
    }
    record["status"] = "PREPARED"
    record["commit_receipt"] = receipt
    record["updated_at"] = now()
    return save_record(ep, snapshot_id, record)


def mark_committed(
    ep: Path,
    *,
    snapshot_id: str,
    task_id: str,
    execution_id: str,
    commit_id: str,
) -> dict:
    record = find_execution(ep, snapshot_id, task_id, execution_id)
    if record is None:
        raise ValueError("PREIMAGE execution not found")
    receipt = dict(record.get("commit_receipt") or {})
    if receipt.get("status") not in {"PREPARED", "COMMITTED"}:
        raise ValueError("PREIMAGE commit receipt not prepared")
    receipt["status"] = "COMMITTED"
    receipt["commit_id"] = commit_id
    receipt["committed_at"] = receipt.get("committed_at") or now()
    record["commit_receipt"] = receipt
    record["status"] = "COMMITTED"
    record["eligible"] = False
    record["finished_at"] = record.get("finished_at") or now()
    record["updated_at"] = now()
    return save_record(ep, snapshot_id, record)


def replay_state(
    ep: Path,
    *,
    snapshot_id: str,
    idempotency_key: str,
    actual_authority_sha: str | None,
) -> dict:
    record = find_by_idempotency(ep, snapshot_id, idempotency_key)
    if record is None:
        return {"status": "NONE", "record": None}
    receipt = record.get("commit_receipt")
    if not isinstance(receipt, dict):
        return {"status": "NONE", "record": record}
    planned_output = receipt.get("output_sha")
    planned_input = receipt.get("input_sha")
    if receipt.get("status") == "COMMITTED":
        if actual_authority_sha == planned_output:
            return {"status": "REPLAYED", "record": record}
        return {"status": "DIVERGED", "record": record}
    if receipt.get("status") == "PREPARED":
        if actual_authority_sha == planned_output:
            recovered = mark_committed(
                ep,
                snapshot_id=snapshot_id,
                task_id=record["task_id"],
                execution_id=record["execution_id"],
                commit_id=receipt.get("commit_id") or "RECOVERED_AFTER_WRITE",
            )
            return {"status": "REPLAYED_RECOVERED", "record": recovered}
        if actual_authority_sha == planned_input:
            return {"status": "RESUME_WRITE", "record": record}
        return {"status": "DIVERGED", "record": record}
    return {"status": "NONE", "record": record}
