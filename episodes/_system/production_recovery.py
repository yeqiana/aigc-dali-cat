#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crash reconciliation for the Production Queue and Ledger.

``episode-state.json`` remains the only stage authority.  This module only
reconciles the two execution records around an image attempt.  It deliberately
does not call an image backend: a missing or still-running worker receipt is
unknown evidence, never permission to regenerate a frame.
"""
from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import production_ledger
from runtime_atomic_store import atomic_write_json, update_json

QUEUE_REL = Path("meta/production-queue.json")
LEDGER_REL = Path("meta/production-ledger.json")
JOURNAL_REL = Path("meta/runtime/production-commit-journal.json")
LIFECYCLE_DIR = Path("meta/image-workers")
READY_LEDGER_STATES = {"ORIGINAL_READY", "REPAIR_READY", "PASSED", "LOCKED"}
ACTIVE_LEDGER_STATES = {"GENERATING", "REPAIRING"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def lifecycle_rel(item: dict) -> Path:
    frame = int(item.get("frame") or 0)
    attempt = max(1, int(item.get("attempts") or 1))
    return LIFECYCLE_DIR / f"{frame:02d}-{item.get('id')}-a{attempt}.lifecycle.json"


def lifecycle_path(ep: Path, item: dict) -> Path:
    return Path(ep) / lifecycle_rel(item)


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _json_safe(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(row) for key, row in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(row) for row in value]
    return value


def _journal(ep: Path, transaction_id: str, phase: str, **details: object) -> None:
    """Write an append-only-by-id recovery journal using an atomic update."""
    path = Path(ep) / JOURNAL_REL

    def mutate(data: dict) -> None:
        data.setdefault("schema_version", 1)
        rows = data.setdefault("transactions", {})
        row = rows.setdefault(transaction_id, {"transaction_id": transaction_id, "created_at": now()})
        row.update({"phase": phase, "updated_at": now(), **details})
        # The journal is recovery evidence, not an unbounded second ledger.
        if len(rows) > 200:
            ordered = sorted(rows.items(), key=lambda pair: str(pair[1].get("updated_at") or ""))
            for key, _ in ordered[:-200]:
                rows.pop(key, None)

    update_json(path, dict, mutate)


def prepare_execution(ep: Path, item: dict) -> str:
    """Persist the pre-worker side of a queue/ledger transaction.

    Callers save the containing queue before invoking ``production_ledger
    begin``.  A crash at this point is provably pre-worker and can be retried.
    """
    existing = item.get("execution") or {}
    transaction_id = str(existing.get("transaction_id") or uuid.uuid4().hex)
    item["execution"] = {
        "transaction_id": transaction_id,
        "phase": "BEGIN_PREPARED",
        "prepared_at": now(),
        "expected_lifecycle": lifecycle_rel(item).as_posix(),
    }
    _journal(ep, transaction_id, "BEGIN_PREPARED", item_id=item.get("id"), frame=item.get("frame"))
    return transaction_id


def mark_worker_pending(ep: Path, item: dict) -> None:
    execution = item.setdefault("execution", {})
    transaction_id = str(execution.get("transaction_id") or uuid.uuid4().hex)
    execution.update({
        "transaction_id": transaction_id,
        "phase": "WORKER_PENDING",
        "worker_pending_at": now(),
        "expected_lifecycle": lifecycle_rel(item).as_posix(),
    })
    _journal(ep, transaction_id, "WORKER_PENDING", item_id=item.get("id"), frame=item.get("frame"))


def mark_terminal(ep: Path, item: dict, phase: str, **details: object) -> None:
    execution = item.setdefault("execution", {})
    transaction_id = str(execution.get("transaction_id") or "")
    if not transaction_id:
        return
    execution["phase"] = phase
    execution["updated_at"] = now()
    _journal(ep, transaction_id, phase, item_id=item.get("id"), frame=item.get("frame"), **details)


def write_lifecycle(ep: Path, item: dict, state: str, **details: object) -> dict:
    """Durably record worker evidence before and after a backend invocation."""
    execution = item.get("execution") or {}
    data = {
        "schema_version": 1,
        "transaction_id": execution.get("transaction_id"),
        "item_id": item.get("id"),
        "frame": int(item.get("frame") or 0),
        "attempt": max(1, int(item.get("attempts") or 1)),
        "state": state,
        "updated_at": now(),
        **_json_safe(details),
    }
    path = lifecycle_path(ep, item)
    old = _read(path)
    if old.get("started_at"):
        data["started_at"] = old["started_at"]
    elif state == "WORKER_STARTED":
        data["started_at"] = data["updated_at"]
    atomic_write_json(path, data)
    transaction_id = str(data.get("transaction_id") or "")
    if transaction_id:
        _journal(ep, transaction_id, state, item_id=item.get("id"), frame=item.get("frame"), lifecycle=lifecycle_rel(item).as_posix())
    return data


def _ledger_frame(ledger: dict, frame: int) -> dict:
    return ((ledger.get("frames") or {}).get(f"{frame:02d}") or {})


def _safe_output(ep: Path, raw: object) -> Path | None:
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = (Path(ep).parents[2] / path).resolve()
    try:
        path.relative_to(Path(ep).resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def _commit_success(ep: Path, item: dict, lifecycle: dict) -> tuple[bool, str]:
    """Commit a worker's durable success through the normal ledger verifier."""
    if lifecycle.get("transaction_id") != (item.get("execution") or {}).get("transaction_id"):
        return False, "lifecycle transaction does not match queue item"
    result = lifecycle.get("result") or {}
    if not isinstance(result, dict):
        return False, "lifecycle result is missing"
    policy = (result.get("payload") or {}).get("image_model") or {}
    if str(policy.get("model") or "") != str(item.get("model") or ""):
        return False, "lifecycle model does not match queue contract"
    if str(policy.get("quality") or "") != str(item.get("quality") or ""):
        return False, "lifecycle quality does not match queue contract"
    expected_sha = ((item.get("frame_contract") or {}).get("contract_sha256"))
    actual_sha = (((result.get("payload") or {}).get("frame_contract") or {}).get("contract_sha256"))
    if expected_sha and str(expected_sha).lower() != str(actual_sha or "").lower():
        return False, "lifecycle frame contract does not match queue contract"
    output = _safe_output(ep, result.get("output"))
    if output is None:
        return False, "lifecycle output is absent or outside the episode"
    receipt = (((result.get("payload") or {}).get("provider_receipt") or {}).get("path"))
    receipt_path = _safe_output(ep, receipt) if receipt else None
    if receipt and receipt_path is None:
        return False, "lifecycle provider receipt is absent or outside the episode"
    args = SimpleNamespace(
        episode_dir=str(ep), frame=f"{int(item['frame']):02d}", path=str(output),
        provider_receipt=str(receipt_path) if receipt_path else None,
    )
    try:
        production_ledger.cmd_success(args)
    except (SystemExit, OSError, ValueError) as exc:
        return False, str(exc)
    item["status"] = "generated"
    root = Path(ep).parents[2]
    item["output_path"] = output.relative_to(root).as_posix()
    item["completed_at"] = now()
    item["last_error"] = None
    item["prompt_package"] = result.get("prompt_package")
    if result.get("log"):
        log = Path(str(result["log"]))
        if log.is_file():
            item["log_path"] = log.resolve().relative_to(root).as_posix()
    mark_terminal(ep, item, "COMMITTED", recovery="worker_success_replayed")
    return True, "worker success committed"


def _mark_technical_failure(ep: Path, item: dict, code: str, message: str) -> None:
    args = SimpleNamespace(
        episode_dir=str(ep), frame=f"{int(item['frame']):02d}", code=code, message=message[:1000]
    )
    try:
        production_ledger.cmd_tech_fail(args)
    except (SystemExit, OSError, ValueError) as exc:
        item["status"] = "interrupted_unknown"
        item["last_error"] = f"RECOVERY_LEDGER_CLOSE_FAILED: {exc}"
        mark_terminal(ep, item, "RECONCILE_PENDING", reason=item["last_error"])
        return
    item["status"] = "tech_failed"
    item["completed_at"] = now()
    item["last_error"] = message[:1000]
    mark_terminal(ep, item, "TECH_FAILED", code=code)


def reconcile_locked(ep: Path, queue: dict) -> dict:
    """Reconcile interrupted queue rows while the scheduler lock is held.

    The result is execution evidence only.  Unknown rows remain non-runnable;
    no path here calls a provider or changes an Episode stage.
    """
    ep = Path(ep).resolve()
    ledger = _read(ep / LEDGER_REL)
    report = {"schema_version": 1, "reconciled_at": now(), "rows": []}
    for item in queue.get("items") or []:
        if not isinstance(item, dict) or item.get("status") not in {"running", "generated", "interrupted_unknown"}:
            continue
        frame = int(item.get("frame") or 0)
        frame_row = _ledger_frame(ledger, frame)
        ledger_status = str(frame_row.get("status") or "PENDING")
        lifecycle = _read(lifecycle_path(ep, item))
        lifecycle_state = str(lifecycle.get("state") or "MISSING")
        outcome = "UNCHANGED"

        if ledger_status in READY_LEDGER_STATES:
            candidate = frame_row.get("current_candidate") or {}
            candidate_path = _safe_output(ep, candidate.get("path"))
            if candidate_path:
                item["status"] = "generated"
                item["output_path"] = candidate_path.relative_to(ep.parents[2]).as_posix()
                item["completed_at"] = item.get("completed_at") or now()
                item["last_error"] = None
                mark_terminal(ep, item, "COMMITTED", recovery="ledger_ready_replayed")
                outcome = "LEDGER_READY_REPLAYED"
            else:
                item["status"] = "interrupted_unknown"
                item["last_error"] = "RECOVERY_LEDGER_READY_CANDIDATE_MISSING"
                mark_terminal(ep, item, "RECONCILE_PENDING", reason=item["last_error"])
                outcome = "LEDGER_READY_CANDIDATE_MISSING"
        elif ledger_status == "TECH_FAILED":
            item["status"] = "tech_failed"
            item["last_error"] = item.get("last_error") or "RECOVERY_LEDGER_TECH_FAILED"
            mark_terminal(ep, item, "TECH_FAILED", recovery="ledger_tech_failed_replayed")
            outcome = "LEDGER_TECH_FAILED_REPLAYED"
        elif ledger_status in ACTIVE_LEDGER_STATES:
            if lifecycle_state == "SUCCEEDED":
                ok, note = _commit_success(ep, item, lifecycle)
                if ok:
                    outcome = "WORKER_SUCCESS_REPLAYED"
                else:
                    item["status"] = "interrupted_unknown"
                    item["last_error"] = f"RECOVERY_SUCCESS_EVIDENCE_INVALID: {note}"
                    mark_terminal(ep, item, "RECONCILE_PENDING", reason=item["last_error"])
                    outcome = "SUCCESS_EVIDENCE_INVALID"
            elif lifecycle_state == "FAILED":
                failure = str(lifecycle.get("error") or "worker failed before scheduler commit")
                _mark_technical_failure(ep, item, "WORKER_INTERRUPTED_FAILURE", failure)
                outcome = "WORKER_FAILURE_REPLAYED"
            elif lifecycle_state == "MISSING" and str((item.get("execution") or {}).get("phase") or "") in {"BEGIN_PREPARED", "WORKER_PENDING"}:
                _mark_technical_failure(ep, item, "SCHEDULER_INTERRUPTED_BEFORE_WORKER", "scheduler stopped before worker lifecycle began")
                outcome = "PRE_WORKER_INTERRUPTION_RETRYABLE"
            else:
                item["status"] = "interrupted_unknown"
                item["last_error"] = "RECOVERY_UNKNOWN_RUNNING_WORKER: lifecycle has no terminal receipt"
                mark_terminal(ep, item, "RECONCILE_PENDING", reason=item["last_error"])
                outcome = "UNKNOWN_RUNNING_WORKER"
        elif ledger_status == "PENDING" and str((item.get("execution") or {}).get("phase") or "") == "BEGIN_PREPARED" and lifecycle_state == "MISSING":
            item["status"] = "queued"
            item.pop("execution", None)
            item["last_error"] = None
            outcome = "PRE_BEGIN_PREPARATION_REPLAYED"
        else:
            item["status"] = "interrupted_unknown"
            item["last_error"] = f"RECOVERY_QUEUE_LEDGER_MISMATCH: queue={item.get('status')} ledger={ledger_status} lifecycle={lifecycle_state}"
            mark_terminal(ep, item, "RECONCILE_PENDING", reason=item["last_error"])
            outcome = "QUEUE_LEDGER_MISMATCH"
        report["rows"].append({"item_id": item.get("id"), "frame": frame, "outcome": outcome,
                               "ledger_status": ledger_status, "lifecycle_state": lifecycle_state})
        ledger = _read(ep / LEDGER_REL)
    atomic_write_json(ep / "meta/runtime/production-reconciliation.json", report)
    return report
