#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive the single next Story OS runtime action without creating a second state machine.

The only Episode stage authority remains meta/episode-state.json. This file is a
runtime convenience for Work/ChatGPT host loops so they do not need to rescan the
repository after every model/image action.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import baseline_candidate_pool
import character_visual_contract
import frame_contract
import image_blocked_recovery
import preproduction_handoff
import production_batch_review
import production_ledger
import product_runtime_adapter
import runtime_execution
import runtime_router
import visual_lock_baseline_gate
import visual_lock_candidate_pool
import visual_lock_v21
import story_json

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/runtime/next-action.json")
QUEUE_REL = Path("meta/production-queue.json")
HOST_REL = Path("meta/runtime/product-host-request.json")
REVIEW_DIR = Path("meta/runtime/reviews")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    return story_json.read_json(path, default={})


def state(ep: Path) -> str:
    return str(read_json(ep / "meta/episode-state.json").get("current_state") or "UNKNOWN")


def pending_product_review(ep: Path, *, current_state: str | None = None) -> dict | None:
    root = ep / REVIEW_DIR
    if not root.is_dir():
        return None
    rows = []
    for p in root.glob("*-request.json"):
        if "-attempt-" in p.name:
            continue
        d = read_json(p)
        kind = str(d.get("review_kind") or "")
        # Actual-pixel authority now belongs to CODEX_VISION. Historical WORK
        # product-review requests for visual tasks are compatibility residue and
        # must never steal routing back from the vision lane.
        vision_runtime, _ = runtime_router.vision_review_runtime()
        if vision_runtime == "CODEX" and (
            kind in {"visual-lock-baseline", "visual-lock", "visual-profile-legacy", "frame-semantic"}
            or kind.startswith("production-batch-")
            or kind.startswith("caption-image-audit-v2-")
        ):
            continue
        # Episode stage is the canonical authority. Once Visual Lock has already
        # advanced to VISUAL_CALIBRATED (or beyond), an older unfinished product
        # review request for that same gate is stale runtime residue and must not
        # pull the DAG backwards into PRODUCT_REVIEW.
        if current_state in {"VISUAL_CALIBRATED", "PRODUCTION_PASSED", "PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"} and kind in {
            "visual-lock-baseline", "visual-lock", "visual-profile-legacy"
        }:
            continue
        if d.get("status") == "AWAITING_PRODUCT_REVIEW":
            rows.append((str(d.get("created_at") or ""), p, d))
    if not rows:
        return None
    _, path, data = sorted(rows, key=lambda x: (x[0], x[1].name))[0]
    return {"path": path.resolve().relative_to(ROOT.resolve()).as_posix(), **data}


def queue_summary(ep: Path) -> dict:
    q = read_json(ep / QUEUE_REL)
    counts: dict[str, int] = {}
    queued_frames = []
    items = [row for row in (q.get("items") or []) if isinstance(row, dict)]
    for row in items:
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        if status == "queued":
            queued_frames.append(int(row.get("frame") or 0))

    # Technical failures are attempt history only when a *later* success for the
    # same frame supersedes them. An older original success must not hide a newer
    # repair failure (the exact failure mode that previously routed back to a
    # stale WORK review instead of RETRY_TECHNICAL_FAILURES).
    ledger = read_json(ep / "meta/production-ledger.json").get("frames") or {}
    tech_failed = []
    for idx, row in enumerate(items):
        if row.get("status") != "tech_failed":
            continue
        frame = int(row.get("frame") or 0)
        later_success = any(
            int(other.get("frame") or 0) == frame and other.get("status") == "generated"
            for other in items[idx + 1:]
        )
        if later_success:
            continue
        ledger_row = ledger.get(f"{frame:02d}") or ledger.get(str(frame)) or {}
        current = ledger_row.get("current_candidate") if isinstance(ledger_row, dict) else None
        if ledger_row.get("status") in production_ledger.READY_LEDGER_STATES and isinstance(current, dict):
            failed_at = str(row.get("completed_at") or row.get("started_at") or row.get("queued_at") or "")
            recorded_at = str(current.get("recorded_at") or "")
            if failed_at and recorded_at and recorded_at >= failed_at:
                continue
        tech_failed.append(row)
    counts["tech_failed"] = len(tech_failed)

    # ``interrupted_unknown`` is also execution history, not necessarily the
    # current production truth. A later ledger candidate (or an approved asset)
    # for the same frame supersedes an older interrupted row.  Keep the queue row
    # for audit, but only count unresolved interruptions whose queued time is
    # newer than the current ledger candidate and which therefore still need
    # recovery evidence.
    unresolved_interrupted = []
    for row in items:
        if row.get("status") != "interrupted_unknown":
            continue
        frame_no = int(row.get("frame") or 0)
        frame = ledger.get(f"{frame_no:02d}") or ledger.get(str(frame_no)) or {}
        approved = frame.get("approved_asset") if isinstance(frame, dict) else None
        if isinstance(approved, dict) and approved.get("sha256"):
            continue
        current = frame.get("current_candidate") if isinstance(frame, dict) else None
        if isinstance(current, dict) and current.get("sha256"):
            row_output = str(row.get("output_path") or "")
            current_path = str(current.get("path") or current.get("asset_path") or "")
            if row_output and current_path and row_output == current_path:
                continue
            queued_at = str(row.get("queued_at") or "")
            recorded_at = str(current.get("recorded_at") or "")
            if queued_at and recorded_at and recorded_at >= queued_at:
                continue
        unresolved_interrupted.append(row)
    counts["interrupted_unknown"] = len(unresolved_interrupted)

    # ``blocked`` rows are non-regenerating technical failures.  Like
    # ``tech_failed``, an older blocked attempt becomes audit history when a
    # later candidate for the same frame has already committed.  Only the
    # unresolved tail may influence routing.
    unresolved_blocked = []
    for idx, row in enumerate(items):
        if row.get("status") != "blocked":
            continue
        frame_no = int(row.get("frame") or 0)
        later_success = any(
            int(other.get("frame") or 0) == frame_no and other.get("status") == "generated"
            for other in items[idx + 1:]
        )
        if later_success:
            continue
        frame = ledger.get(f"{frame_no:02d}") or ledger.get(str(frame_no)) or {}
        current = frame.get("current_candidate") if isinstance(frame, dict) else None
        if isinstance(current, dict) and current.get("sha256"):
            failed_at = str(row.get("completed_at") or row.get("started_at") or row.get("queued_at") or "")
            recorded_at = str(current.get("recorded_at") or "")
            if failed_at and recorded_at and recorded_at >= failed_at:
                continue
        unresolved_blocked.append(row)
    counts["blocked"] = len(unresolved_blocked)

    return {
        "counts": counts,
        "queued_frames": sorted(x for x in queued_frames if x > 0),
        "blocked_items": unresolved_blocked,
        "raw": q,
    }


def _expected_frames(ep: Path) -> int:
    try:
        return int(frame_contract.frame_count(ep))
    except Exception:
        return 0


def _represented_original_frames(q: dict) -> set[int]:
    return {
        int(row.get("frame") or 0)
        for row in (q.get("items") or [])
        if isinstance(row, dict)
        and row.get("kind") == "original"
        and str(row.get("scope") or "") in {"visual_lock", "batch"}
        and int(row.get("frame") or 0) > 0
        and row.get("status") != "superseded"
    }


def _final_semantic_attempt(ep: Path) -> int:
    first = ep / "meta/frame-semantic-candidate-attempt-1.json"
    if first.is_file():
        data = read_json(first)
        if data.get("failed_frames"):
            return 2
    return 1


def _handoff_valid(ep: Path) -> bool:
    p = ep / "meta/preproduction-handoff.json"
    if not p.is_file():
        return False
    try:
        return not preproduction_handoff.verify(ep)
    except Exception:
        return False


def derive(ep: Path) -> dict:
    ep = Path(ep).resolve()
    runtime, _ = runtime_router.detect()
    image_runtime, _ = runtime_router.image_execution_runtime()
    vision_runtime, _ = runtime_router.vision_review_runtime()
    mode = runtime_execution.effective_mode(ep)
    cur = state(ep)
    review = pending_product_review(ep, current_state=cur)
    try:
        product_runtime_adapter.reconcile(ep)
    except Exception:
        pass
    base = {
        "schema_version": 1,
        "derived_at": now(),
        "episode": ep.resolve().relative_to(ROOT.resolve()).as_posix(),
        "episode_state": cur,
        "execution_mode": mode,
        "authoring_runtime": runtime,
        "image_execution_runtime": image_runtime,
        "stage_authority": "meta/episode-state.json",
        "derived_runtime_only": True,
        "continue_without_user_prompt": True,
        "work_pending": False,
        "auto_recoverable": False,
        "hard_stop": False,
    }
    import scheduler_core
    base["progress"] = scheduler_core.progress(ep, read_json(ep / QUEUE_REL))
    def action_result(**kwargs):
        hard_stop = bool(kwargs.pop("hard_stop", False))
        auto = bool(kwargs.pop("auto_recoverable", True))
        pending = bool(kwargs.pop("work_pending", True))
        return {
            **base,
            "work_pending": pending,
            "auto_recoverable": auto,
            "hard_stop": hard_stop,
            "blocking": bool(hard_stop),
            **kwargs,
        }
    # A stale/missing PREIMAGE authority boundary invalidates every downstream
    # image request derived from it. This canonical freshness check must outrank
    # queue recovery, including AUTHORITY_REFRESH_AUTHORIZED, otherwise the host
    # loop can regenerate pixels against the very authority snapshot being
    # replaced. This is not "stale host request wins": next_host_step derives the
    # requirement from current authority/frame-contract/handoff evidence.
    if cur == "STORYBOARD_LOCKED" and not _handoff_valid(ep):
        try:
            preimage_step, _ = product_runtime_adapter.next_host_step(ep, mode)
        except Exception:
            preimage_step = "PREIMAGE_TASK_SET"
        if str(preimage_step).startswith("PREIMAGE_"):
            current_request = read_json(ep / HOST_REL) if (ep / HOST_REL).is_file() else {}
            return action_result(
                action="PREIMAGE_COMPILE",
                executor=runtime,
                preimage_step=preimage_step,
                request_path=current_request.get("request_path"),
                request_id=current_request.get("request_id"),
                reason="PREIMAGE authority/handoff is stale; refresh authority before any image generation or authority-refresh retry",
            )
    # Production queue recovery has priority over stale host requests.
    # A previous host request can remain after a worker failure; it must not
    # hide an automatic technical retry action.
    qs = queue_summary(ep)
    q = qs["raw"]
    if q:
        ledger_frames = read_json(ep / "meta/production-ledger.json").get("frames") or {}
        unresolved_blocked = list(qs.get("blocked_items") or [])
        if unresolved_blocked:
            plans = image_blocked_recovery.inspect(ep, unresolved_blocked)
            if plans and all(bool(row.get("auto_resolvable")) for row in plans):
                return action_result(
                    action="RESOLVE_IMAGE_NORMALIZATION",
                    executor="MACHINE",
                    frames=sorted({int(row.get("frame") or 0) for row in plans if int(row.get("frame") or 0) > 0}),
                    reason="preserved provider RAW can be deterministically normalized under the explicit provider-ratio exception; do not regenerate or review stale pixels",
                )
            return action_result(
                action="IMAGE_ATTEMPT_BLOCKED",
                executor=runtime,
                frames=sorted({int(row.get("frame") or 0) for row in unresolved_blocked if int(row.get("frame") or 0) > 0}),
                hard_stop=True,
                auto_recoverable=False,
                blocked=[{
                    "frame": int(row.get("frame") or 0),
                    "code": str(row.get("code") or ""),
                    "reason": str(row.get("reason") or "non-regenerating image failure requires explicit inspection"),
                } for row in plans],
                reason="non-regenerating image failure must be resolved before any pixel review or further generation",
            )
        authority_refresh_frames = sorted(
            int(key) for key, row in ledger_frames.items()
            if isinstance(row, dict) and row.get("status") == "AUTHORITY_REFRESH_AUTHORIZED"
        )
        if authority_refresh_frames:
            # Technical recovery still outranks authority regeneration: if the
            # freshly refreshed baseline failed at the provider, retry that exact
            # attempt before considering dependent admissions.
            if qs["counts"].get("external_blocked"):
                blocked_frames=sorted({int(x.get("frame") or 0) for x in q.get("items") or [] if x.get("status")=="external_blocked" and int(x.get("frame") or 0)>0})
                return {**base, "action":"EXTERNAL_IMAGE_PROVIDER_BLOCKED", "executor":"EXTERNAL",
                        "blocking":True, "work_pending":True, "auto_recoverable":False, "hard_stop":True,
                        "frames":blocked_frames, "reason":"image provider technical retry epoch exhausted"}
            if qs["counts"].get("tech_failed"):
                return action_result(action="RETRY_TECHNICAL_FAILURES", executor="CODEX_IMAGE",
                        reason="technical image failure must recover before authority-refresh dependents")
            try:
                baseline = int(visual_lock_baseline_gate.baseline_frame(ep))
            except Exception:
                baseline = None
            if baseline is not None and baseline not in authority_refresh_frames and character_visual_contract.pixel_master_required(ep):
                try:
                    master = character_visual_contract.pixel_master_reference(ep, allow_provisional=True)
                except Exception:
                    master = None
                if master is None:
                    return action_result(
                        action="REVIEW_ORDINARY_BASELINE",
                        executor="CODEX_VISION" if vision_runtime=="CODEX" else runtime,
                        frame=baseline,
                        reason="authority-refreshed baseline must PASS and establish the new Pixel Master before dependent frames regenerate",
                    )
            return action_result(
                action="REFRESH_AUTHORITY_IMAGES",
                executor="CODEX_IMAGE" if image_runtime=="CODEX" else runtime,
                frames=authority_refresh_frames,
                reason="upstream authority/Frame Contract changed; regenerate these frames without consuming content repair budget",
            )
        try:
            if visual_lock_baseline_gate.awaiting_review(ep, q):
                return action_result(action="REVIEW_ORDINARY_BASELINE",
                        executor="CODEX_VISION" if vision_runtime=="CODEX" else runtime,
                        frame=visual_lock_baseline_gate.baseline_frame(ep),
                        reason="Visual Lock baseline pixels must PASS before parallel-three generation")
        except Exception:
            pass
        visual_rows=[x for x in q.get("items") or [] if str(x.get("scope") or "")=="visual_lock"]
        visual_frames={int(x.get("frame") or 0) for x in visual_rows}
        if cur=="STORYBOARD_LOCKED":
            candidate_frames=visual_lock_candidate_pool.prepareable_frames(ep)
            if candidate_frames:
                return action_result(action="PREPARE_VISUAL_LOCK_CANDIDATES", executor="MACHINE",
                        frames=candidate_frames,
                        reason="Visual Lock admissions exhausted ordinary repair; prepare bounded independent candidates")
            exhausted=visual_lock_candidate_pool.exhausted_frames(ep)
            if exhausted:
                return {**base, "action":"USER_DECISION_REQUIRED", "executor":runtime,
                        "blocking":True, "work_pending":True, "auto_recoverable":False, "hard_stop":True,
                        "frames":exhausted,
                        "reason":"Visual Lock bounded admission candidate pool exhausted after real Codex Vision failures"}
        visual_repair_active=any(
            int(x.get("frame") or 0) in visual_frames and x.get("kind") in {"repair","baseline_candidate"}
            and x.get("status") in {"queued","running","tech_failed","external_blocked","interrupted_unknown"}
            for x in q.get("items") or []
        )
        if cur=="STORYBOARD_LOCKED" and not visual_repair_active and len(visual_rows)==4 and all(x.get("status")=="generated" for x in visual_rows):
            try:
                visual_errors=visual_lock_v21.verify(ep,metadata_only=False)
            except Exception as exc:
                visual_errors=[str(exc)]
            if visual_errors:
                dirty_frames = visual_lock_v21.dirty_admission_frames(ep)
                return action_result(action="REVIEW_VISUAL_LOCK",
                        executor="CODEX_VISION" if vision_runtime=="CODEX" else runtime,
                        frames=dirty_frames or sorted(int(x.get("frame") or 0) for x in visual_rows),
                        reason="dirty Visual Lock admissions require isolated actual-pixel review; valid SHA-bound PASS rows are reused")
            return action_result(action="FINALIZE_VISUAL_LOCK", executor="MACHINE",
                    frames=sorted(int(x.get("frame") or 0) for x in visual_rows),
                    reason="four-image Codex Vision evidence is valid; deterministic gate/approval/state finalization remains")

        if cur=="VISUAL_CALIBRATED":
            expected=_expected_frames(ep)
            represented=_represented_original_frames(q)
            if expected>0 and len(represented)<expected:
                return action_result(action="PREPARE_PRODUCTION_BATCH", executor="MACHINE",
                        represented_frames=sorted(represented), expected_frames=expected,
                        reason="Visual Lock is calibrated; deterministically materialize missing scene prompts and queue remaining original frames")
            try:
                batch_ids=production_batch_review.pending(ep)
            except Exception:
                batch_ids=[]
            if batch_ids:
                return action_result(action="REVIEW_GENERATED_IMAGES",
                        executor="CODEX_VISION" if vision_runtime=="CODEX" else runtime,
                        batch_ids=batch_ids,
                        reason="generated Production logical batch awaits isolated actual-pixel review")

        # Reuse the scheduler's dependency authority. In particular, Visual Lock
        # dependents must wait for baseline *approval*, not merely an older
        # generated Frame01 candidate. Duplicating dependency logic here caused
        # 05/16/17 to bypass the baseline gate after Frame01 entered repair.
        import image_scheduler
        scheduler_ready, _scheduler_blocked = image_scheduler.ready_items(ep, q)
        runnable=sorted({int(x["frame"]) for x in scheduler_ready})
        if runnable:
            return action_result(action="GENERATE_IMAGES",executor="CODEX_IMAGE" if image_runtime=="CODEX" else runtime,
                frames=runnable,reason="scheduler dependency authority reports runnable image work")
        production_review_pending=[
            x for x in q.get("items") or []
            if str(x.get("scope") or "")=="batch" and x.get("status")=="review_pending"
        ]
        if cur=="VISUAL_CALIBRATED" and production_review_pending:
            return action_result(action="REVIEW_GENERATED_IMAGES",
                    executor="CODEX_VISION" if vision_runtime=="CODEX" else runtime,
                    batch_ids=sorted({str(x.get("batch_id")) for x in production_review_pending if x.get("batch_id")}),
                    reason="Production batch review request remains pending isolated actual-pixel review")
        if qs["counts"].get("scout_repair"):
            return action_result(action="REPAIR_FAILED_IMAGES",
                    executor="CODEX_IMAGE" if image_runtime=="CODEX" else runtime,
                    reason="actual-pixel review authorized content repair")
        if qs["counts"].get("external_blocked"):
            blocked_frames=sorted({int(x.get("frame") or 0) for x in q.get("items") or [] if x.get("status")=="external_blocked" and int(x.get("frame") or 0)>0})
            return action_result(action="EXTERNAL_IMAGE_PROVIDER_BLOCKED", executor="EXTERNAL",
                    frames=blocked_frames,hard_stop=True,auto_recoverable=False,
                    reason="image provider technical retry budget is exhausted; content/candidate budgets are preserved")
        if qs["counts"].get("tech_failed"):
            return action_result(action="RETRY_TECHNICAL_FAILURES", executor="CODEX_IMAGE",
                    reason="technical image failures remain; successful siblings must be reused")
        if qs["counts"].get("interrupted_unknown"):
            return {**base, "action": "RECOVER_INTERRUPTED_IMAGES", "executor": runtime, "blocking": True,
                    "work_pending": True, "auto_recoverable": False, "hard_stop": True,
                    "reason": "an interrupted worker has no terminal receipt; inspect reconciliation evidence before retry"}
        # A stale `running` row after a host/process interruption must enter the
        # scheduler once so crash reconciliation can inspect lifecycle/ledger
        # evidence. This does not authorize regeneration by itself.
        running_frames=sorted({
            int(x.get("frame") or 0) for x in q.get("items") or []
            if x.get("status")=="running" and int(x.get("frame") or 0)>0
        })
        if running_frames:
            return action_result(action="GENERATE_IMAGES", executor="CODEX_IMAGE" if image_runtime == "CODEX" else runtime,
                    frames=running_frames,
                    reason="image attempt is marked running; scheduler must reconcile durable worker evidence before any retry")

        if cur=="VISUAL_CALIBRATED":
            expected=_expected_frames(ep)
            ledger_frames=read_json(ep/"meta/production-ledger.json").get("frames") or {}
            ready_statuses=set(production_ledger.READY_LEDGER_STATES) | set(production_ledger.ACCEPTED_LEDGER_STATES)
            complete_candidates=(
                expected>0 and len([k for k in ledger_frames if str(k).isdigit()])>=expected
                and all(
                    isinstance(ledger_frames.get(f"{frame:02d}"),dict)
                    and str(ledger_frames[f"{frame:02d}"].get("status") or "") in ready_statuses
                    for frame in range(1,expected+1)
                )
            )
            all_locked=complete_candidates and all(
                str(ledger_frames[f"{frame:02d}"].get("status") or "")=="LOCKED"
                for frame in range(1,expected+1)
            )
            if complete_candidates and not all_locked:
                return action_result(action="REVIEW_FINAL_PRODUCTION",
                        executor="CODEX_VISION" if vision_runtime=="CODEX" else runtime,
                        attempt=_final_semantic_attempt(ep),
                        frames=list(range(1,expected+1)),
                        reason="all production candidates exist; final SHA-bound semantic pixel review must PASS and lock every frame")
            if all_locked:
                reviews=read_json(ep/"meta/story-gates.json").get("reviews") or {}
                if reviews.get("production")!="passed" or reviews.get("continuity")!="passed" or reviews.get("authenticity")!="passed":
                    return action_result(action="FINALIZE_PRODUCTION_IMAGES", executor="MACHINE",
                            frames=list(range(1,expected+1)),
                            reason="all production frames are semantic-reviewed and LOCKED; deterministic image-production gate finalization remains")

    ledger_frames = read_json(ep / "meta/production-ledger.json").get("frames") or {}
    needs_user_frames = sorted(
        int(key) for key, value in ledger_frames.items()
        if str(key).isdigit() and isinstance(value, dict) and value.get("status") == "NEEDS_USER"
    )
    if needs_user_frames:
        # Visual Lock baseline is special: after the ordinary one-shot repair is
        # exhausted, full-auto may still try a bounded candidate competition.
        # This does not raise content_repairs_used and does not bypass Codex Vision.
        try:
            baseline = visual_lock_baseline_gate.baseline_frame(ep)
        except Exception:
            baseline = None
        if (
            cur == "STORYBOARD_LOCKED"
            and baseline is not None
            and int(baseline) in needs_user_frames
            and baseline_candidate_pool.can_prepare(ep)
        ):
            return action_result(
                action="PREPARE_BASELINE_CANDIDATE",
                executor="MACHINE",
                frame=int(baseline),
                used=baseline_candidate_pool.successful_candidate_slots(ep),
                max=baseline_candidate_pool.max_additional_candidates(),
                reason="ordinary baseline repair is exhausted; prepare the next bounded independent baseline candidate",
            )
        return action_result(
            action="USER_DECISION_REQUIRED",
            executor=runtime,
            frames=needs_user_frames,
            work_pending=True,
            auto_recoverable=False,
            hard_stop=True,
            reason="production frames exhausted automatic/authorized repair lanes and require an explicit user decision",
        )

    if review:
        return action_result(action="PRODUCT_REVIEW", executor=runtime,
                request_path=review.get("path"), review_kind=review.get("review_kind"),
                candidate_path=review.get("candidate_path"),
                reason="fresh isolated product review is awaiting completion")

    if cur == "IDEA_LOCKED":
        return {**base, "action": "CREATIVE_STORY", "executor": runtime, "blocking": True,
                "target_state": "STORYBOARD_LOCKED", "reason": "Story/Storyboard/critics are not yet locked"}
    if cur == "STORYBOARD_LOCKED":
        if not _handoff_valid(ep):
            return {**base, "action": "PREIMAGE_COMPILE", "executor": runtime, "blocking": True,
                    "reason": "preproduction handoff is missing or stale"}
        return {**base, "action": "VISUAL_LOCK", "executor": runtime, "blocking": True,
                "target_state": "VISUAL_CALIBRATED", "reason": "preimage evidence is valid; begin Visual Lock 1+3"}
    if cur == "VISUAL_CALIBRATED":
        return {**base, "action": "PRODUCTION", "executor": runtime, "blocking": True,
                "target_state": "PRODUCTION_PASSED", "reason": "Visual Lock passed; production remains"}
    if cur == "PRODUCTION_PASSED":
        return {**base, "action": "RELEASE", "executor": runtime, "blocking": True,
                "target_state": "PUBLISH_READY", "reason": "final release closure remains"}
    if cur in {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}:
        return {**base, "action": "COMPLETE", "executor": runtime, "blocking": False,
                "reason": f"runtime production goal already reached at {cur}"}
    return {**base, "action": "REPAIR_STATE", "executor": runtime, "blocking": True,
            "reason": f"unrecognized episode state: {cur}"}


def apply_runtime_block_semantics(data: dict) -> dict:
    """V2.7: blocking no longer means every pending action is a hard stop.

    Runtime consumers need to know whether work exists, whether it can be
    recovered automatically, and whether a human decision is truly required.
    Keep legacy ``blocking`` for compatibility, but expose explicit semantics.
    """
    action = str(data.get("action") or "")
    hard_stop_actions = {"REPAIR_STATE", "RECOVER_INTERRUPTED_IMAGES", "USER_DECISION_REQUIRED", "EXTERNAL_IMAGE_PROVIDER_BLOCKED", "IMAGE_ATTEMPT_BLOCKED"}
    recoverable_actions = {
        "GENERATE_IMAGES",
        "RETRY_TECHNICAL_FAILURES",
        "REPAIR_FAILED_IMAGES",
        "PRODUCT_REVIEW",
        "HOST_ACTION",
        "PRODUCTION",
        "VISUAL_LOCK",
        "RELEASE",
        "CREATIVE_STORY",
        "PREIMAGE_COMPILE",
        "REVIEW_ORDINARY_BASELINE",
        "REVIEW_VISUAL_LOCK",
        "REVIEW_GENERATED_IMAGES",
        "REVIEW_FINAL_PRODUCTION",
        "PREPARE_BASELINE_CANDIDATE",
        "PREPARE_VISUAL_LOCK_CANDIDATES",
        "RESOLVE_IMAGE_NORMALIZATION",
        "FINALIZE_VISUAL_LOCK",
        "PREPARE_PRODUCTION_BATCH",
        "FINALIZE_PRODUCTION_IMAGES",
    }
    data["work_pending"] = action != "COMPLETE"
    data["auto_recoverable"] = action in recoverable_actions
    data["hard_stop"] = action in hard_stop_actions
    # Backward compatibility: blocking means there is pending work, not that
    # the whole workflow must stop.
    data["blocking"] = bool(data["work_pending"] and data["hard_stop"])
    return data


def write(ep: Path) -> dict:
    data = apply_runtime_block_semantics(derive(ep))
    path = Path(ep) / REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return data


def self_test() -> None:
    assert REL.as_posix() == "meta/runtime/next-action.json"
    print("NEXT ACTION V2.6.1 H1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("show", "write"):
        p = sub.add_parser(name); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    ep = Path(args.episode_dir).resolve()
    data = write(ep) if args.cmd == "write" else apply_runtime_block_semantics(derive(ep))
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
