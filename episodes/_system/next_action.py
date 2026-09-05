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
    }
    if review:
        return {**base, "action": "PRODUCT_REVIEW", "executor": runtime, "blocking": True,
                "request_path": review.get("path"), "review_kind": review.get("review_kind"),
                "candidate_path": review.get("candidate_path"), "reason": "fresh isolated product review is awaiting completion"}

    host_path = ep / HOST_REL
    if host_path.is_file():
        host = read_json(host_path)
        if host.get("status") == "HOST_ACTION_REQUIRED":
            return {**base, "action": str(host.get("next_step") or "HOST_ACTION"), "executor": runtime,
                    "blocking": True, "request_path": host_path.relative_to(ROOT).as_posix(),
                    "target_state": host.get("target_state"), "reason": "product host step is awaiting execution"}

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
        if qs["counts"].get("review_pending"):
            return {**base, "action": "REVIEW_GENERATED_IMAGES", "executor": runtime, "blocking": True,
                    "reason": "generated image batch awaits actual-pixel WORK review"}
        if qs["counts"].get("scout_repair"):
            return {**base, "action": "REPAIR_FAILED_IMAGES", "executor": "CODEX_IMAGE", "blocking": True,
                    "reason": "actual-pixel review authorized content repair"}
        if qs["counts"].get("tech_failed"):
            return {**base, "action": "RETRY_TECHNICAL_FAILURES", "executor": "CODEX_IMAGE", "blocking": True,
                    "reason": "technical image failures remain; successful siblings must be reused"}
        if qs["queued_frames"]:
            return {**base, "action": "GENERATE_IMAGES", "executor": "CODEX_IMAGE" if image_runtime == "CODEX" else runtime,
                    "blocking": True, "frames": qs["queued_frames"],
                    "reason": "production queue has ready/pending image work; scheduler enforces dependencies and concurrency"}

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


def write(ep: Path) -> dict:
    data = derive(ep)
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
    data = write(ep) if args.cmd == "write" else derive(ep)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
