"""Audited PREIMAGE candidate recovery after bounded Codex TIMEOUT receipts.

A TIMEOUT is never reclassified as a successful model call. Only a verified
candidate bound to the frozen PREIMAGE snapshot can be reused as an artifact.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import codex_user_runner
import preimage_authority_snapshot
import preimage_task_contract as tasks
import story_json

MANIFEST_REL = Path("meta/runtime/preimage-timeout-candidate-recovery.json")
RECEIPTS_REL = Path("meta/provider-receipts/model-executions")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(ep: Path, snapshot: dict, rows: list[dict]) -> dict:
    """Read-only, fail-closed preflight; no model dispatch, state or gate writes."""
    ep = Path(ep).resolve()
    state = story_json.read_json(ep / tasks.STATE_REL, default={}) or {}
    if state.get("snapshot_id") != snapshot.get("snapshot_id"):
        return {"status": "NOT_ELIGIBLE", "reason": "snapshot_id drift"}
    if preimage_authority_snapshot.stale_owned(ep, snapshot):
        return {"status": "NOT_ELIGIBLE", "reason": "owned authority changed"}
    try:
        inflight = codex_user_runner.runner_health().get("inflight_request_ids")
    except Exception:
        return {"status": "NOT_ELIGIBLE", "reason": "runner health unavailable"}
    if not isinstance(inflight, list) or inflight:
        return {"status": "NOT_ELIGIBLE", "reason": "runner requests still in flight"}
    if not rows or len(rows) != len(tasks.TASK_TYPES):
        return {"status": "NOT_ELIGIBLE", "reason": "incomplete PREIMAGE task set"}
    receipts_dir = ep / RECEIPTS_REL
    reports = []
    recovered_count = 0
    for task in rows:
        task_type = str(task.get("task_type") or "")
        state_row = (state.get("tasks") or {}).get(task_type) or {}
        if state_row.get("task_id") != task.get("task_id"):
            return {"status": "NOT_ELIGIBLE", "reason": f"{task_type}: task_id drift"}
        candidate_path = ep / str(task.get("candidate_output"))
        if not candidate_path.is_file():
            return {"status": "NOT_ELIGIBLE", "reason": f"{task_type}: candidate missing"}
        candidate = tasks.read_candidate(ep, task)
        errors = tasks.verify_candidate(candidate or {}, task)
        if errors:
            return {"status": "NOT_ELIGIBLE", "reason": f"{task_type}: " + "; ".join(errors[:3])}
        original_status = str(state_row.get("status") or "")
        original_reason = str(state_row.get("reason") or "")
        if original_status in {"COMPLETED", "REUSED"}:
            required_model_status = "SUCCESS"
        elif original_status == "FAILED" and original_reason == "worker rc=124":
            required_model_status = "TIMEOUT"
            recovered_count += 1
        else:
            return {"status": "NOT_ELIGIBLE", "reason": f"{task_type}: unsafe status {original_status}"}
        step = tasks.canonical_step(task_type)
        matches = []
        for p in receipts_dir.glob("*.json"):
            try:
                receipt = story_json.read_json(p, default={}) or {}
            except Exception:
                continue
            if (receipt.get("step") == step
                    and receipt.get("status") == required_model_status
                    and receipt.get("call_id") == p.stem
                    and receipt.get("requested_model") == "gpt-6-luna"
                    and receipt.get("reasoning_effort") == "high"
                    and receipt.get("model_binding_source") == "EPISODE_BOUND_MODEL_POLICY"):
                matches.append((str(receipt.get("finished_at") or ""), p, receipt))
        if not matches:
            return {"status": "NOT_ELIGIBLE", "reason": f"{task_type}: authentic {required_model_status} receipt missing"}
        _date, receipt_path, receipt = max(matches, key=lambda x: x[0])
        reports.append({
            "task_type": task_type,
            "task_id": task["task_id"],
            "source_snapshot_id": snapshot["snapshot_id"],
            "candidate_path": str(task["candidate_output"]),
            "candidate_sha256": _sha(candidate_path),
            "model_execution_status": receipt["status"],
            "receipt_path": str(receipt_path.relative_to(ep)).replace("\\", "/"),
            "receipt_sha256": _sha(receipt_path),
            "receipt_call_id": receipt["call_id"],
            "was_timeout": required_model_status == "TIMEOUT",
            "recovery_basis": "verified_candidate_same_snapshot_and_real_timeout_receipt"
                              if required_model_status == "TIMEOUT"
                              else "already_completed_and_success_receipt",
        })
    if recovered_count == 0:
        return {"status": "NOT_ELIGIBLE", "reason": "no genuine timeout to recover"}
    return {"status": "ELIGIBLE", "schema_version": 1,
            "snapshot_id": snapshot["snapshot_id"],
            "not_model_success": True, "model_timeout_count": recovered_count,
            "tasks": reports}


def recheck_unchanged(ep: Path, proof: dict) -> bool:
    """Guard against a candidate/receipt changed since preflight."""
    ep=Path(ep).resolve()
    for row in proof.get("tasks") or []:
        p=ep/row["candidate_path"]
        q=ep/row["receipt_path"]
        if not p.is_file() or not q.is_file():
            return False
        if _sha(p)!=row["candidate_sha256"] or _sha(q)!=row["receipt_sha256"]:
            return False
    return True
