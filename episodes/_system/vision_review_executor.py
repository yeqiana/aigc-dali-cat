#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local isolated Codex Vision host-action executor.

This module owns only actual-pixel review actions. It never generates images,
rewrites Story/PREIMAGE authority, approves Release, or advances episode-state.
The surrounding WORK Runtime remains the orchestration/governance authority.
"""
from __future__ import annotations

from pathlib import Path

import auto_repair_enqueue
import baseline_candidate_pool
import frame_semantic_review
import production_batch_review
import runtime_router
import story_json
import runtime_timeout_policy
import visual_lock_baseline_gate
import visual_lock_candidate_pool
import visual_lock_v21
import visual_profile_review_persistence
import production_ledger

ALLOWED_ACTIONS = {
    "REVIEW_ORDINARY_BASELINE",
    "REVIEW_VISUAL_LOCK",
    "REVIEW_GENERATED_IMAGES",
    "REVIEW_FINAL_PRODUCTION",
    "REVIEW_FINAL_PATCH",
    "REVIEW_FINAL_EXCEPTION",
    "REVIEW_FINAL_CONTINUATION",
}


class VisionReviewError(RuntimeError):
    pass


def local_vision_action(action: dict) -> str | None:
    if not isinstance(action, dict):
        return None
    if str(action.get("executor") or "").upper() != "CODEX_VISION":
        return None
    name = str(action.get("action") or "")
    return name if name in ALLOWED_ACTIONS else None


def _require_capability() -> None:
    runtime, _ = runtime_router.vision_review_runtime()
    if runtime != "CODEX" or not runtime_router.local_codex_vision_allowed():
        raise VisionReviewError(f"Codex Vision review is not enabled: runtime={runtime}")


def execute(ep: Path, action: dict) -> dict:
    ep = Path(ep).resolve()
    name = local_vision_action(action)
    if name is None:
        raise VisionReviewError(f"not an auto-allowed Codex Vision action: {action}")
    _require_capability()

    if name == "REVIEW_ORDINARY_BASELINE":
        if visual_lock_baseline_gate.approved(ep):
            return {"status": "REUSED", "action": name, "runtime": "CODEX_VISION", "reason": "baseline review already valid"}
        frame = visual_lock_baseline_gate.baseline_frame(ep)
        attempt = int(action.get("attempt") or baseline_candidate_pool.review_attempt(ep))
        result = visual_lock_baseline_gate.run_codex_critic(
            ep,
            attempt=attempt,
            codex_raw=None,
            timeout=runtime_timeout_policy.seconds("visual_baseline_critic"),
        )
        status = str(result.get("status") or "FAIL").upper()
        if status == "PASS":
            import image_scheduler
            refreshed = image_scheduler.refresh_queued_visual_lock_references(ep)
            return {"status": status, "action": name, "runtime": "CODEX_VISION", "result": result, "attempt": attempt, "reference_refresh": refreshed}
        if status in {"TECHNICAL_FAILURE", "TECH_FAILED"}:
            return {"status": status, "action": name, "runtime": "CODEX_VISION", "result": result, "attempt": attempt}
        review = visual_lock_baseline_gate.read_json(ep / visual_lock_baseline_gate.REL)
        failed_checks = [
            str(key) for key, value in (review.get("checks") or {}).items()
            if str(value or "").upper() != "PASS"
        ]
        repair = auto_repair_enqueue.enqueue(
            ep,
            frame=frame,
            findings=failed_checks + ([str(review.get("note") or "")] if review.get("note") else []),
            source="VISUAL_BASELINE",
            review_note="Visual Lock ordinary baseline Codex Vision content FAIL",
        )
        if repair.get("status") in {"REPAIR_ENQUEUED", "REPAIR_ALREADY_PENDING"}:
            return {"status": "REPAIR_ENQUEUED", "action": name, "runtime": "CODEX_VISION", "result": result, "repair": repair, "attempt": attempt}
        if repair.get("status") == "NEEDS_USER":
            return {"status": "NEEDS_USER", "action": name, "runtime": "CODEX_VISION", "result": result, "repair": repair, "attempt": attempt}
        return {"status": "FAIL", "action": name, "runtime": "CODEX_VISION", "result": result, "repair": repair, "attempt": attempt}

    if name == "REVIEW_VISUAL_LOCK":
        try:
            visual_lock_v21.bind_from_queue(ep)
        except Exception as exc:
            raise VisionReviewError(f"Visual Lock bind-from-queue failed: {exc}") from exc
        errors = visual_lock_v21.verify(ep, metadata_only=False)
        if not errors:
            return {"status": "REUSED", "action": name, "runtime": "CODEX_VISION", "reason": "Visual Lock review already valid"}
        frames = [int(x) for x in (action.get("frames") or []) if int(x) > 0]
        attempt = int(action.get("attempt") or max(
            max([auto_repair_enqueue.review_attempt(ep, frame) for frame in frames] or [1]),
            visual_lock_candidate_pool.review_attempt(ep),
        ))
        rc = visual_lock_v21.run_critic(
            ep,
            attempt=attempt,
            codex_raw=None,
            timeout=runtime_timeout_policy.seconds("review_critic"),
        )
        if rc == 11:
            return {"status": "TECHNICAL_FAILURE", "action": name, "runtime": "CODEX_VISION", "returncode": rc, "attempt": attempt}
        if rc != 0:
            review = visual_profile_review_persistence.load(ep) or {}
            repairs = []
            for row in review.get("calibration") or []:
                checks = row.get("checks") or {}
                failed = row.get("issues") not in ([], None) or any(value is not True for value in checks.values())
                if not failed:
                    continue
                try:
                    frame = int(row.get("frame"))
                except Exception:
                    continue
                findings = [str(k) for k, v in checks.items() if v is not True]
                findings.extend(str(x) for x in (row.get("issues") or []))
                repair = auto_repair_enqueue.enqueue(
                    ep,
                    frame=frame,
                    findings=findings,
                    source="VISUAL_LOCK",
                    review_note="Phase5 Visual Lock critic failed actual-pixel admission",
                )
                repairs.append(repair)
            if repairs and all(r.get("status") in {"REPAIR_ENQUEUED", "REPAIR_ALREADY_PENDING", "NOT_REPAIRABLE"} for r in repairs):
                enqueued = [r for r in repairs if r.get("status") in {"REPAIR_ENQUEUED", "REPAIR_ALREADY_PENDING"}]
                if enqueued:
                    return {"status": "REPAIR_ENQUEUED", "action": name, "runtime": "CODEX_VISION", "returncode": rc, "repairs": repairs, "attempt": attempt}
            if any(r.get("status") == "NEEDS_USER" for r in repairs):
                return {"status": "NEEDS_USER", "action": name, "runtime": "CODEX_VISION", "returncode": rc, "repairs": repairs, "attempt": attempt}
            return {"status": "FAIL", "action": name, "runtime": "CODEX_VISION", "returncode": rc, "repairs": repairs, "attempt": attempt}
        errors = visual_lock_v21.verify(ep, metadata_only=False)
        return {"status": "PASS" if not errors else "FAIL", "action": name, "runtime": "CODEX_VISION", "errors": errors, "attempt": attempt}

    if name == "REVIEW_FINAL_CONTINUATION":
        frames = [str(x).zfill(2) for x in (action.get("frames") or []) if str(x)]
        if not frames:
            raise VisionReviewError("REVIEW_FINAL_CONTINUATION requires at least one frame")
        rc = frame_semantic_review.run_continuation_critic(
            ep,
            targets=frames,
            codex_raw=None,
            timeout=runtime_timeout_policy.seconds("deep_semantic_review"),
        )
        if rc == 0:
            return {"status": "PASS", "action": name, "runtime": "CODEX_VISION", "frames": frames}
        if rc in {2, 3}:
            return {"status": "FAIL", "action": name, "runtime": "CODEX_VISION", "frames": frames, "returncode": rc}
        return {"status": "TECHNICAL_FAILURE", "action": name, "runtime": "CODEX_VISION", "frames": frames, "returncode": rc}

    if name == "REVIEW_FINAL_EXCEPTION":
        frames = [str(x).zfill(2) for x in (action.get("frames") or []) if str(x)]
        if not frames:
            raise VisionReviewError("REVIEW_FINAL_EXCEPTION requires at least one frame")
        rc = frame_semantic_review.run_exception_critic(
            ep,
            targets=frames,
            codex_raw=None,
            timeout=runtime_timeout_policy.seconds("deep_semantic_review"),
        )
        if rc == 0:
            return {"status": "PASS", "action": name, "runtime": "CODEX_VISION", "attempt": 3, "frames": frames}
        if rc in {2, 3}:
            return {"status": "FAIL", "action": name, "runtime": "CODEX_VISION", "attempt": 3, "frames": frames, "returncode": rc}
        return {"status": "TECHNICAL_FAILURE", "action": name, "runtime": "CODEX_VISION", "attempt": 3, "frames": frames, "returncode": rc}

    if name == "REVIEW_FINAL_PRODUCTION":
        attempt = int(action.get("attempt") or 1)
        rc = frame_semantic_review.run_critic(
            ep,
            attempt=attempt,
            codex_raw=None,
            timeout=runtime_timeout_policy.seconds("deep_semantic_review"),
        )
        if rc == 0:
            return {"status": "PASS", "action": name, "runtime": "CODEX_VISION", "attempt": attempt}
        if rc not in {2, 3}:
            return {"status": "TECHNICAL_FAILURE", "action": name, "runtime": "CODEX_VISION", "attempt": attempt, "returncode": rc}
        evidence_path = ep / "meta" / f"frame-semantic-candidate-attempt-{attempt}.json"
        evidence = story_json.read_json(evidence_path, default={}) if evidence_path.is_file() else {}
        failed_frames = [str(x).zfill(2) for x in (evidence.get("failed_frames") or [])]
        critic_rows = {
            str(row.get("frame") or "").zfill(2): row
            for row in ((evidence.get("critic_result") or {}).get("frames") or [])
            if isinstance(row, dict)
        }
        repairs = []
        for key in failed_frames:
            row = critic_rows.get(key) or {}
            findings = [str(x) for x in (row.get("issue_codes") or [])]
            if row.get("notes"):
                findings.append(str(row.get("notes")))
            repairs.append(auto_repair_enqueue.enqueue(
                ep,
                frame=int(key),
                findings=findings,
                source="FINAL_SEMANTIC",
                review_note="Final Frame Semantic Codex Vision content FAIL",
            ))
        if repairs and any(r.get("status") in {"REPAIR_ENQUEUED", "REPAIR_ALREADY_PENDING"} for r in repairs):
            return {"status": "REPAIR_ENQUEUED", "action": name, "runtime": "CODEX_VISION", "attempt": attempt, "repairs": repairs}
        ledger = production_ledger.load_authority(ep, default={}) or {}
        needs_user = [
            str(key).zfill(2) for key, value in ((ledger.get("frames") or {}).items())
            if isinstance(value, dict) and value.get("status") == "NEEDS_USER"
        ]
        if needs_user:
            return {"status": "NEEDS_USER", "action": name, "runtime": "CODEX_VISION", "attempt": attempt, "frames": needs_user, "repairs": repairs}
        return {"status": "FAIL", "action": name, "runtime": "CODEX_VISION", "attempt": attempt, "returncode": rc, "repairs": repairs}

    if name == "REVIEW_FINAL_PATCH":
        frames = [str(x).zfill(2) for x in (action.get("frames") or []) if str(x)]
        if not frames:
            raise VisionReviewError("REVIEW_FINAL_PATCH requires at least one frame")
        attempt = int(action.get("attempt") or 2)
        rc = frame_semantic_review.run_patch_critic(
            ep,
            targets=frames,
            attempt=attempt,
            codex_raw=None,
            timeout=runtime_timeout_policy.seconds("deep_semantic_review"),
        )
        if rc == 0:
            return {"status": "PASS", "action": name, "runtime": "CODEX_VISION", "attempt": attempt, "frames": frames}
        if rc not in {2, 3}:
            return {"status": "TECHNICAL_FAILURE", "action": name, "runtime": "CODEX_VISION", "attempt": attempt, "frames": frames, "returncode": rc}
        ledger = production_ledger.load_authority(ep, default={}) or {}
        needs_user = [
            str(key).zfill(2) for key, value in ((ledger.get("frames") or {}).items())
            if isinstance(value, dict) and value.get("status") == "NEEDS_USER"
        ]
        return {
            "status": "NEEDS_USER" if needs_user else "FAIL",
            "action": name,
            "runtime": "CODEX_VISION",
            "attempt": attempt,
            "frames": needs_user or frames,
            "returncode": rc,
        }

    batch_ids = [str(x) for x in (action.get("batch_ids") or production_batch_review.pending(ep)) if str(x)]
    if not batch_ids:
        return {"status": "REUSED", "action": name, "runtime": "CODEX_VISION", "reason": "no pending generated batch review"}
    reviewed = []
    for batch_id in batch_ids:
        try:
            reviewed.append(production_batch_review.run_codex_review(
                ep,
                batch_id,
                attempt=int(action.get("attempt") or 1),
                codex_raw=None,
                timeout=runtime_timeout_policy.seconds("review_critic"),
            ))
        except Exception as exc:
            # A malformed or incomplete isolated critic response is a bounded
            # technical failure. Keep the resident Runner alive so the next
            # cycle can retry the review instead of losing the whole queue.
            return {
                "status": "TECHNICAL_FAILURE",
                "action": name,
                "runtime": "CODEX_VISION",
                "batch_ids": batch_ids,
                "reviewed": reviewed,
                "error": str(exc),
            }
    return {"status": "PASS", "action": name, "runtime": "CODEX_VISION", "batch_ids": batch_ids, "reviews": reviewed}
