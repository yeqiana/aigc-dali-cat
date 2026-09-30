#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""First-pass Production finding aggregation and one automatic repair wave."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import logical_asset_identity
import model_policy
import production_ledger
import production_recovery
import runtime_observability
import scheduler_core
import story_json

ROOT = Path(__file__).resolve().parents[2]
PLAN_REL = Path("meta/runtime/repair-wave-1.json")
MAX_AUTOMATIC_REPAIR_WAVES = 1


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _read(path: Path, default=None):
    return story_json.read_json(path, default=default)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_plan(ep: Path, plan: dict) -> None:
    target = ep / PLAN_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    story_json.write_json(target, plan)


def _repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _event(ep: Path, event_type: str, **fields) -> None:
    runtime_observability.safe_record_runtime_event(
        ep, event_type, episode_id=logical_asset_identity.episode_id(ep),
        step="PRODUCTION_REPAIR_WAVE", source="repair_aggregator", **fields)


def _queue_source(ep: Path, frame: int, generation_key: str, source_sha: str) -> dict:
    queue = scheduler_core.load_queue(ep)
    for row in queue.get("items") or []:
        if int(row.get("frame") or 0) != frame:
            continue
        key = production_recovery.generation_key_for_item(ep, row)
        if generation_key and key != generation_key:
            continue
        output = row.get("output_path")
        if output:
            path = Path(str(output))
            path = path if path.is_absolute() else (ROOT / path).resolve()
            if path.is_file() and _sha(path).lower() == source_sha.lower():
                return row
    return {}


def collect_first_pass_findings(ep: Path, *, attempt: int = 1, evidence: dict | None = None) -> dict:
    """Read only the complete, SHA-bound full-frame semantic candidate evidence."""
    ep = Path(ep).resolve()
    evidence_path = ep / "meta" / f"frame-semantic-candidate-attempt-{int(attempt)}.json"
    data = evidence if isinstance(evidence, dict) else _read(evidence_path, {})
    if data.get("review_scope") != "CANDIDATE_FULL_FRAME_SET" or not data.get("recorded_at"):
        raise ValueError("FIRST_PASS_REVIEW_NOT_COMPLETE")
    evidence_sha = _sha(evidence_path) if evidence_path.is_file() else hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    failed = {str(value).zfill(2) for value in data.get("failed_frames") or []}
    critic_rows = {
        str(row.get("frame") or "").zfill(2): row
        for row in ((data.get("critic_result") or {}).get("frames") or [])
        if isinstance(row, dict)
    }
    reviewed = {str(row.get("frame") or "").zfill(2): row
                for row in data.get("reviewed_assets") or [] if isinstance(row, dict)}
    ledger = production_ledger.load_authority(ep, default={}) or {}
    frames = ledger.get("frames") or {}
    findings = []
    for frame_id in sorted(failed, key=lambda value: int(value)):
        frame = int(frame_id)
        ledger_row = frames.get(frame_id) or {}
        reviewed_row = reviewed.get(frame_id) or {}
        candidate = ledger_row.get("current_candidate") or {}
        sha = str(reviewed_row.get("sha256") or "").lower()
        candidate_sha = str(candidate.get("sha256") or "").lower()
        current_path = candidate.get("path")
        if not sha or sha != candidate_sha or not current_path:
            stale = True
        else:
            artifact = Path(str(current_path))
            artifact = artifact if artifact.is_absolute() else (ROOT / artifact).resolve()
            stale = not artifact.is_file() or _sha(artifact).lower() != sha
        source_item = _queue_source(ep, frame, "", sha) if sha else {}
        generation_key = production_recovery.generation_key_for_item(ep, source_item) if source_item else ""
        critic = critic_rows.get(frame_id) or {}
        codes = [str(code).strip() for code in critic.get("issue_codes") or [] if str(code).strip()]
        ledger_status = str(ledger_row.get("status") or "")
        human_only = bool(critic.get("human_only") or critic.get("needs_user_only")) or ledger_status == "NEEDS_USER"
        remaining = 0
        if not stale and generation_key:
            asset_key = logical_asset_identity.frame_asset_key(ep, frame)
            remaining = int(__import__("generation_attempt_authority").remaining(ep, asset_key))
        repairable = bool(not stale and not human_only and codes and remaining > 0
                          and ledger_status == "REPAIR_AUTHORIZED")
        if stale:
            status = "STALE"
        elif human_only:
            status = "NEEDS_USER"
        elif remaining <= 0:
            status = "BUDGET_EXHAUSTED"
        elif not generation_key:
            status = "SOURCE_GENERATION_MISSING"
        elif repairable:
            status = "ELIGIBLE"
        else:
            status = "UNREPAIRABLE"
        findings.append({
            "logical_asset_key": logical_asset_identity.frame_asset_key(ep, frame),
            "frame_id": frame_id,
            "source_generation_key": generation_key,
            "source_artifact_sha256": sha,
            "source_artifact_path": str(current_path or ""),
            "failure_codes": codes,
            "failure_summary": str(critic.get("notes") or " ".join(codes))[:1000],
            "human_only": human_only,
            "stale": stale,
            "repairable": repairable,
            "remaining_generation_attempts": remaining,
            "repair_status": status,
            "source_item_id": str(source_item.get("id") or ""),
            "review_receipt_sha256": evidence_sha,
        })
    return {"episode_id": logical_asset_identity.episode_id(ep), "attempt": int(attempt),
            "evidence_sha256": evidence_sha, "findings": findings}


def classify_repairability(finding: dict) -> tuple[bool, str]:
    if finding.get("stale"):
        return False, "STALE_ARTIFACT"
    if finding.get("human_only"):
        return False, "NEEDS_USER"
    if int(finding.get("remaining_generation_attempts") or 0) <= 0:
        return False, "BUDGET_EXHAUSTED"
    if not finding.get("source_generation_key") or not finding.get("failure_codes"):
        return False, "UNREPAIRABLE"
    return True, "ELIGIBLE"


def build_repair_plan(ep: Path, findings: dict, *, policy: dict | None = None) -> dict:
    ep = Path(ep).resolve()
    bound = policy or model_policy.resolve("prompt.repair", episode=ep)
    wave_id = f"{logical_asset_identity.episode_id(ep)}/production/repair-wave-1"
    rows = []
    for raw in findings.get("findings") or []:
        row = dict(raw)
        eligible, status = classify_repairability(row)
        row["repairable"] = eligible
        row["repair_status"] = status
        row["repair_prompt_task_fingerprint"] = None
        row["repair_prompt_receipt"] = None
        row["repair_queue_item_id"] = None
        rows.append(row)
    eligible_count = sum(bool(row["repairable"]) for row in rows)
    return {
        "schema_version": 1,
        "episode_id": logical_asset_identity.episode_id(ep),
        "repair_wave_id": wave_id,
        "source_review_scope": "CANDIDATE_FULL_FRAME_SET",
        "source_review_receipts": [{"path": f"meta/frame-semantic-candidate-attempt-{findings['attempt']}.json",
                                     "sha256": findings["evidence_sha256"]}],
        "created_at": now(),
        "frames": rows,
        "policy_sha256": str(bound.get("model_policy_sha256") or ""),
        "policy_version": str(bound.get("policy_version") or ""),
        "status": "PLANNED" if eligible_count else "COMPLETED",
        "summary": {"total_failures": len(rows), "eligible_repairs": eligible_count,
                    "repaired_pass": 0, "still_failed": 0, "needs_user": sum(r["repair_status"] in {"NEEDS_USER", "BUDGET_EXHAUSTED", "STALE_ARTIFACT"} for r in rows),
                    "skipped_budget_exhausted": sum(r["repair_status"] == "BUDGET_EXHAUSTED" for r in rows)},
    }


def _prompt_task_input(ep: Path, row: dict, plan: dict) -> dict:
    frame = int(row["frame_id"])
    contract = _read(ep / "meta/runtime/contracts/frames" / f"{frame:02d}.json", {})
    material = contract.get("hash_material") or {}
    source_item = _queue_source(ep, frame, row["source_generation_key"], row["source_artifact_sha256"])
    prompt_path = Path(str(source_item.get("prompt_file") or "")) if source_item else Path()
    if not prompt_path.is_absolute():
        prompt_path = (ROOT / prompt_path).resolve()
    original_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else ""
    return {
        "logical_asset_key": row["logical_asset_key"],
        "source_generation_key": row["source_generation_key"],
        "source_artifact_sha256": row["source_artifact_sha256"],
        "review_receipt_sha256": row["review_receipt_sha256"],
        "failure_codes": row["failure_codes"],
        "failure_summary": row["failure_summary"],
        "current_artifact_sha256": row["source_artifact_sha256"],
        "original_production_prompt": original_prompt,
        "frame_contract": contract,
        "continuity_tags": material.get("continuity_tags") or material.get("continuity_group") or {},
        "policy_sha256": plan["policy_sha256"],
        "repair_wave_id": plan["repair_wave_id"],
    }


def _materialize_item(ep: Path, plan: dict, row: dict, *, prompt_runner=None, add_item_fn=None) -> dict:
    import image_model_policy
    import image_scheduler

    prompt_runner = prompt_runner or __import__("scoped_codex_worker").run_repair_prompt_task
    add_item_fn = add_item_fn or image_scheduler.add_item
    capture_id = f"repair-wave-1-{int(row['frame_id']):02d}"
    queue = scheduler_core.load_queue(ep)
    existing = next((item for item in queue.get("items") or [] if item.get("capture_id") == capture_id), None)
    if existing:
        if (existing.get("scope") != "repair"
                or str(existing.get("source_generation_key") or row["source_generation_key"]) != row["source_generation_key"]
                or str(existing.get("source_artifact_sha256") or row["source_artifact_sha256"]).lower() != row["source_artifact_sha256"].lower()):
            raise ValueError("REPAIR_WAVE_ITEM_IDENTITY_CONFLICT")
        existing.update({"repair_wave_id":plan["repair_wave_id"],
                         "source_generation_key":row["source_generation_key"],
                         "source_artifact_sha256":row["source_artifact_sha256"],
                         "repair_prompt_task_fingerprint":row.get("repair_prompt_task_fingerprint")})
        with scheduler_core.queue_transaction(ep):
            latest=scheduler_core.load_queue(ep)
            for queued in latest.get("items") or []:
                if str(queued.get("id") or "")==str(existing.get("id") or ""):
                    queued.update({"repair_wave_id":plan["repair_wave_id"],
                        "source_generation_key":row["source_generation_key"],
                        "source_artifact_sha256":row["source_artifact_sha256"],
                        "repair_prompt_task_fingerprint":row.get("repair_prompt_task_fingerprint")})
                    break
            scheduler_core.save_queue(ep,latest)
        row["repair_queue_item_id"] = str(existing.get("id") or "")
        row["repair_status"] = "ENQUEUED" if existing.get("status") not in {"generated", "review_pending"} else "GENERATED"
        return {"status": "ALREADY_MATERIALIZED", "item": existing}
    task_input = _prompt_task_input(ep, row, plan)
    _event(ep,"REPAIR_PROMPT_STARTED",repair_wave_id=plan["repair_wave_id"],
           logical_asset_key=row["logical_asset_key"],generation_key=row["source_generation_key"],status="started")
    task = prompt_runner(ep, task_input=task_input)
    row["repair_prompt_task_fingerprint"] = task.get("fingerprint")
    row["repair_prompt_receipt"] = task.get("receipt_path")
    if task.get("status") not in {"SUCCESS", "REUSED"}:
        row["repair_status"] = "PROMPT_TECH_FAILED"
        return {"status": "PROMPT_TECH_FAILED", "frame": row["frame_id"]}
    prompt_path = Path(task["prompt_path"])
    if not prompt_path.is_absolute():
        prompt_path = (ROOT / prompt_path).resolve()
    if not prompt_path.is_file():
        raise ValueError("repair prompt task output is missing")
    _event(ep,"REPAIR_PROMPT_FINISHED",repair_wave_id=plan["repair_wave_id"],
           logical_asset_key=row["logical_asset_key"],generation_key=row["source_generation_key"],
           model_policy_sha256=plan["policy_sha256"],status=task.get("status"),
           evidence_ref=str(task.get("receipt_path") or ""))
    if add_item_fn is image_scheduler.add_item:
        refs = image_scheduler.contract_references(ep, int(row["frame_id"]), scope="repair")
    else:
        refs = []
    source_item = _queue_source(ep, int(row["frame_id"]), row["source_generation_key"], row["source_artifact_sha256"])
    policy = image_model_policy.for_episode(ep)
    item = add_item_fn(ep, frame=int(row["frame_id"]), kind="repair", prompt_file=prompt_path,
        scope="repair", references=refs, capture_id=capture_id, model=policy["model"],
        quality=policy["quality"], strict_model=bool(policy.get("strict_model")),
        depends_on=[int(value) for value in (source_item.get("depends_on") or [])], replace=True)
    item.update({"repair_wave_id": plan["repair_wave_id"],
                 "source_generation_key": row["source_generation_key"],
                 "source_artifact_sha256": row["source_artifact_sha256"],
                 "repair_prompt_task_fingerprint": row["repair_prompt_task_fingerprint"]})
    with scheduler_core.queue_transaction(ep):
        latest = scheduler_core.load_queue(ep)
        for queued in latest.get("items") or []:
            if str(queued.get("id") or "") == str(item.get("id") or ""):
                queued.update({"repair_wave_id": plan["repair_wave_id"],
                    "source_generation_key": row["source_generation_key"],
                    "source_artifact_sha256": row["source_artifact_sha256"],
                    "repair_prompt_task_fingerprint": row["repair_prompt_task_fingerprint"]})
                break
        scheduler_core.save_queue(ep,latest)
    row["repair_queue_item_id"] = str(item.get("id") or "")
    row["repair_status"] = "ENQUEUED"
    _event(ep,"REPAIR_ENQUEUED",repair_wave_id=plan["repair_wave_id"],
           logical_asset_key=row["logical_asset_key"],source_generation_key=row["source_generation_key"],
           failure_codes=row["failure_codes"],remaining_attempts=row["remaining_generation_attempts"],
           model_policy_sha256=plan["policy_sha256"],queue_name="repair",status="queued",
           evidence_ref=str(item.get("id") or ""))
    return {"status": "ENQUEUED", "item": item}


def materialize_wave(ep: Path, *, attempt: int = 1, findings: dict | None = None,
                     prompt_runner=None, add_item_fn=None, policy: dict | None = None) -> dict:
    """Persist one canonical plan, then idempotently fill its repair work items."""
    ep = Path(ep).resolve()
    path = ep / PLAN_REL
    if path.is_file():
        plan = _read(path, {})
        if plan.get("repair_wave_id") and plan.get("status") in {"PLANNED", "STARTED", "COMPLETED"}:
            if isinstance(findings, dict) and "findings" in findings and "evidence_sha256" in findings:
                source = findings
            else:
                # Resume callers often pass the persisted semantic receipt itself.
                # Recompute its file-bound SHA instead of treating it as a new wave.
                source = collect_first_pass_findings(ep, attempt=attempt, evidence=findings)
            source_sha = str((plan.get("source_review_receipts") or [{}])[0].get("sha256") or "")
            if source_sha != str(source.get("evidence_sha256") or ""):
                _event(ep, "REPAIR_WAVE_DENIED_SECOND_WAVE", repair_wave_id=plan["repair_wave_id"], status="DENIED",
                       failure_class="SECOND_AUTOMATIC_REPAIR_WAVE_FORBIDDEN")
                return {"status": "SECOND_AUTOMATIC_REPAIR_WAVE_FORBIDDEN", "plan": plan}
            if plan.get("status") == "COMPLETED":
                return {"status": "ALREADY_COMPLETED", "plan": plan}
            for row in plan.get("frames") or []:
                if row.get("repairable") and row.get("repair_status") in {"ELIGIBLE", "PROMPT_TECH_FAILED"}:
                    result = _materialize_item(ep, plan, row, prompt_runner=prompt_runner, add_item_fn=add_item_fn)
                    _write_plan(ep, plan)
            return {"status": plan.get("status"), "plan": plan, "resumed": True}
    source = (findings if isinstance(findings, dict) and "findings" in findings
              else collect_first_pass_findings(ep, attempt=attempt, evidence=findings))
    plan = build_repair_plan(ep, source, policy=policy)
    _write_plan(ep, plan)
    _event(ep, "FIRST_PASS_REVIEW_COMPLETE", status="COMPLETE", evidence_ref=_repo_ref(path))
    _event(ep, "REPAIR_WAVE_PLANNED", repair_wave_id=plan["repair_wave_id"], status=plan["status"],
           queue_depth=len([row for row in plan["frames"] if row["repairable"]]))
    if plan["status"] == "COMPLETED":
        _event(ep, "REPAIR_WAVE_COMPLETED", repair_wave_id=plan["repair_wave_id"], status="COMPLETED")
        _write_plan(ep, plan)
        return {"status": "COMPLETED", "plan": plan}
    plan["status"] = "STARTED"
    _event(ep, "REPAIR_WAVE_STARTED", repair_wave_id=plan["repair_wave_id"], status="STARTED")
    for row in plan["frames"]:
        if not row.get("repairable"):
            continue
        result = _materialize_item(ep, plan, row, prompt_runner=prompt_runner, add_item_fn=add_item_fn)
        _write_plan(ep, plan)
        if result.get("status") == "PROMPT_TECH_FAILED":
            continue
    return {"status": plan["status"], "plan": plan}


def load_wave(ep: Path) -> dict:
    return _read(Path(ep).resolve() / PLAN_REL, {})


def finalize_wave(ep: Path, *, repair_reviews: dict[str, str] | None = None) -> dict:
    """Close Wave 1 from terminal repair review outcomes; never enqueue Wave 2."""
    ep = Path(ep).resolve()
    plan = load_wave(ep)
    if not plan:
        return {"status": "NO_WAVE"}
    if plan.get("status") == "COMPLETED":
        return {"status":"ALREADY_COMPLETED","plan":plan}
    outcomes = repair_reviews or {}
    for row in plan.get("frames") or []:
        if not row.get("repairable"):
            continue
        decision = str(outcomes.get(str(row["frame_id"]) or "")).upper()
        if decision in {"PASS", "FINALIZED"}:
            row["repair_status"] = "PASS"
            plan["summary"]["repaired_pass"] += 1
        elif decision in {"REPAIR_NEEDED", "NEEDS_USER", "TECH_FAILED"}:
            row["repair_status"] = "NEEDS_USER" if decision != "TECH_FAILED" else "TECH_BLOCKED"
            plan["summary"]["still_failed"] += 1
            if decision != "TECH_FAILED":
                plan["summary"]["needs_user"] += 1
        else:
            return {"status": "INCOMPLETE", "plan": plan}
    plan["status"] = "COMPLETED"
    _write_plan(ep, plan)
    _event(ep, "REPAIR_WAVE_COMPLETED", repair_wave_id=plan["repair_wave_id"], status="COMPLETED")
    return {"status": "COMPLETED", "plan": plan}

