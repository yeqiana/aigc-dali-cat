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

import preproduction_handoff
import product_runtime_adapter
import runtime_execution
import runtime_router
import visual_lock_baseline_gate

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/runtime/next-action.json")
QUEUE_REL = Path("meta/production-queue.json")
HOST_REL = Path("meta/runtime/product-host-request.json")
REVIEW_DIR = Path("meta/runtime/reviews")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def state(ep: Path) -> str:
    return str(read_json(ep / "meta/episode-state.json").get("current_state") or "UNKNOWN")


def pending_product_review(ep: Path) -> dict | None:
    root = ep / REVIEW_DIR
    if not root.is_dir():
        return None
    rows = []
    for p in root.glob("*-request.json"):
        if "-attempt-" in p.name:
            continue
        d = read_json(p)
        if d.get("status") == "AWAITING_PRODUCT_REVIEW":
            rows.append((str(d.get("created_at") or ""), p, d))
    if not rows:
        return None
    _, path, data = sorted(rows, key=lambda x: (x[0], x[1].name))[0]
    return {"path": path.relative_to(ROOT).as_posix(), **data}


def queue_summary(ep: Path) -> dict:
    q = read_json(ep / QUEUE_REL)
    counts: dict[str, int] = {}
    queued_frames = []
    for row in q.get("items") or []:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        if status == "queued":
            queued_frames.append(int(row.get("frame") or 0))
    # Technical failures are attempt history, not automatically the current
    # production truth. A later successful candidate/commit must win over an
    # earlier backend timeout, otherwise a recovered frame can permanently
    # block the pipeline.
    tech_failed = []
    for row in q.get("items") or []:
        if not isinstance(row, dict) or row.get("status") != "tech_failed":
            continue
        attempts = row.get("attempts") or []
        if not isinstance(attempts, list):
            attempts = []
        recovered = any(isinstance(a, dict) and a.get("result") in {"success", "PASSED"} for a in attempts)
        # Some legacy queue entries only contain counters/ids instead of an
        # attempt list. They cannot prove recovery, so keep the technical retry
        # requirement for those entries.
        if not recovered:
            tech_failed.append(row)
    counts["tech_failed"] = len(tech_failed)
    return {"counts": counts, "queued_frames": sorted(x for x in queued_frames if x > 0), "raw": q}


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
    mode = runtime_execution.effective_mode(ep)
    cur = state(ep)
    review = pending_product_review(ep)
    try:
        product_runtime_adapter.reconcile(ep)
    except Exception:
        pass
    base = {
        "schema_version": 1,
        "derived_at": now(),
        "episode": ep.relative_to(ROOT).as_posix(),
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
    # Production queue recovery has priority over stale host requests.
    # A previous host request can remain after a worker failure; it must not
    # hide an automatic technical retry action.
    qs = queue_summary(ep)
    q = qs["raw"]
    if q:
        try:
            if visual_lock_baseline_gate.awaiting_review(ep, q):
                return {**base, "action": "REVIEW_ORDINARY_BASELINE", "executor": runtime, "blocking": True,
                        "frame": visual_lock_baseline_gate.baseline_frame(ep),
                        "reason": "Visual Lock baseline pixels must PASS before parallel-three generation"}
        except Exception:
            pass
        ledger=read_json(ep/"meta/production-ledger.json").get("frames") or {}
        ready_states={"ORIGINAL_READY","REPAIR_READY","PASSED","LOCKED"}
        satisfied={int(k) for k,v in ledger.items() if str(k).isdigit() and v.get("status") in ready_states}
        satisfied.update(int(x.get("frame") or 0) for x in q.get("items") or [] if x.get("status")=="generated")
        runnable=[int(x["frame"]) for x in q.get("items") or [] if x.get("status")=="queued"
                  and all(int(d) in satisfied for d in x.get("depends_on") or [])]
        if runnable:
            return action_result(action="GENERATE_IMAGES",executor="CODEX_IMAGE" if image_runtime=="CODEX" else runtime,
                frames=sorted(runnable),reason="independent ready frames can continue while other frames await repair/review")
        if qs["counts"].get("review_pending"):
            return {**base, "action": "REVIEW_GENERATED_IMAGES", "executor": runtime, "blocking": True,
                    "reason": "generated image batch awaits actual-pixel WORK review"}
        if qs["counts"].get("scout_repair"):
            return {**base, "action": "REPAIR_FAILED_IMAGES", "executor": runtime, "blocking": True,
                    "reason": "actual-pixel review authorized content repair"}
        if qs["counts"].get("tech_failed"):
            return action_result(action="RETRY_TECHNICAL_FAILURES", executor="CODEX_IMAGE",
                    reason="technical image failures remain; successful siblings must be reused")
        if qs["queued_frames"]:
            return action_result(action="GENERATE_IMAGES", executor="CODEX_IMAGE" if image_runtime == "CODEX" else runtime,
                    frames=qs["queued_frames"],
                    reason="production queue has ready/pending image work; scheduler enforces dependencies and concurrency")

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
    hard_stop_actions = {"REPAIR_STATE"}
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
        "REVIEW_GENERATED_IMAGES",
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
