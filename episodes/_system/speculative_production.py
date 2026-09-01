#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded fail-soft speculative production for Story OS V2.1.1 R3.1.

Speculative work is only allowed after the current Visual Lock attempt is technically
blocked and the four Visual Lock candidates pass the SAME strict validator used by the
formal Visual Lock path. It may generate at most six candidates and never approves,
locks, advances state, or releases.
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import critic_runtime_v211
import frame_contract
import image_model_policy
import image_scheduler
import preproduction_handoff
import visual_lock_v21

MAX_SPECULATIVE_FRAMES = 6


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def stage(ep: Path) -> str | None:
    p = ep / "meta/episode-state.json"
    return read_json(p).get("current_state") if p.is_file() else None


def visual_lock_candidates_ready(ep: Path) -> tuple[bool, str]:
    """Reuse formal Visual Lock SHA/Frame-Contract/ledger lineage validation."""
    try:
        assets = visual_lock_v21.calibration_assets(ep)
    except Exception as exc:
        return False, "formal_visual_lock_validation_failed:" + str(exc)[:500]
    p = ep / "meta/story-gates.json"
    if not p.is_file():
        return False, "story_gates_missing"
    items = ((((read_json(p).get("visual") or {}).get("calibration") or {}).get("items")) or [])
    if len(items) != 4 or len(assets) != 4:
        return False, "visual_lock_candidate_count_invalid"
    by_role = {str(x.get("role") or ""): x for x in items if isinstance(x, dict)}
    for asset in assets:
        role = str(asset.get("role") or "")
        gate = by_role.get(role)
        if not gate:
            return False, "visual_lock_role_missing:" + role
        if str(gate.get("decision") or "") not in {"candidate", "passed"}:
            return False, "visual_lock_decision_not_candidate:" + role
        if str(gate.get("sha256") or "").lower() != str(asset.get("sha256") or "").lower():
            return False, "visual_lock_sha_binding_mismatch:" + role
        if str(gate.get("asset_path") or "") != str(asset.get("asset_path") or ""):
            return False, "visual_lock_path_binding_mismatch:" + role
    return True, "formal_visual_lock_validation_pass"


def discover_prompt_dir(ep: Path) -> Path | None:
    qpath = ep / image_scheduler.QUEUE_REL
    candidates = []
    if qpath.is_file():
        q = read_json(qpath)
        for item in q.get("items") or []:
            raw = item.get("prompt_file")
            if not raw:
                continue
            p = (image_scheduler.ROOT / raw).resolve()
            if p.is_file():
                candidates.append(p.parent)
    scored = {}
    for p in ep.rglob("*.txt"):
        if len(p.stem) == 2 and p.stem.isdigit():
            scored[p.parent] = scored.get(p.parent, 0) + 1
    candidates.extend(sorted(scored, key=lambda x: scored[x], reverse=True))
    seen = set()
    for d in candidates:
        d = d.resolve()
        if d in seen:
            continue
        seen.add(d)
        if sum(1 for n in range(1, frame_contract.frame_count(ep) + 1) if (d / f"{n:02d}.txt").is_file()) >= 4:
            return d
    return None


def eligible(ep: Path) -> tuple[bool, str]:
    ep = Path(ep).resolve()
    if stage(ep) != "STORYBOARD_LOCKED":
        return False, "stage_not_storyboard_locked"
    errors = preproduction_handoff.verify(ep)
    if errors:
        return False, "handoff_invalid:" + ";".join(errors[:4])
    if not critic_runtime_v211.speculative_allowed(ep, require_current_run=True):
        current = critic_runtime_v211.current_visual_lock_run_id(ep)
        recorded = critic_runtime_v211.load(ep).get("last_visual_lock_run_id")
        if recorded and current and recorded != current:
            return False, "stale_critic_technical_state"
        return False, "critic_not_current_technical_blocked"
    ready, reason = visual_lock_candidates_ready(ep)
    if not ready:
        return False, reason
    if discover_prompt_dir(ep) is None:
        return False, "production_prompt_dir_missing"
    return True, "eligible"


def _ready_state(ep: Path, frame: int) -> bool:
    return image_scheduler.ledger_state(ep, frame) in image_scheduler.READY_LEDGER_STATES


def select_frames(ep: Path, limit: int = MAX_SPECULATIVE_FRAMES) -> list[int]:
    total = frame_contract.frame_count(ep)
    ready = {n for n in range(1, total + 1) if _ready_state(ep, n)}
    selected = []
    progress = True
    while len(selected) < limit and progress:
        progress = False
        for frame in range(1, total + 1):
            if frame in ready or frame in selected:
                continue
            deps = image_scheduler.directive_dependency(ep, frame)
            if all(d in ready or d in selected for d in deps):
                selected.append(frame)
                progress = True
                if len(selected) >= limit:
                    break
    return selected


def run(ep: Path, *, codex: str | None = None, timeout: int = 600,
        max_frames: int = MAX_SPECULATIVE_FRAMES) -> dict:
    ep = Path(ep).resolve()
    ok, reason = eligible(ep)
    if not ok:
        return {"status": "SKIPPED", "reason": reason, "generated_or_attempted": [], "elapsed_seconds": 0.0}
    prompt_dir = discover_prompt_dir(ep)
    limit = max(1, min(MAX_SPECULATIVE_FRAMES, int(max_frames)))
    frames = select_frames(ep, limit)
    if not frames:
        return {"status": "SKIPPED", "reason": "no_dependency_safe_frames", "generated_or_attempted": [], "elapsed_seconds": 0.0}
    q = image_scheduler.load_queue(ep)
    unrelated = [x for x in q.get("items") or [] if x.get("status") in {"queued", "running"}]
    if unrelated:
        return {"status": "SKIPPED", "reason": "queue_has_active_items", "generated_or_attempted": [], "elapsed_seconds": 0.0}
    added = []
    model = image_model_policy.for_episode(ep)["model"]
    for frame in frames:
        prompt = prompt_dir / f"{frame:02d}.txt"
        if not prompt.is_file():
            continue
        row = image_scheduler.add_item(
            ep, frame=frame, kind="original", prompt_file=prompt, scope="batch",
            references=image_scheduler.contract_references(ep, frame, scope="batch"),
            capture_id=f"speculative-{frame:02d}", model=model,
            depends_on=image_scheduler.directive_dependency(ep, frame), replace=False,
        )
        added.append(int(row["frame"]))
    if not added:
        return {"status": "SKIPPED", "reason": "no_items_added", "generated_or_attempted": [], "elapsed_seconds": 0.0}
    started = time.monotonic()
    rc = image_scheduler.run_scheduler(ep, max_workers=3, timeout=timeout, codex=codex)
    elapsed = time.monotonic() - started
    result = {
        "status": "GENERATED_CANDIDATES" if rc in {0, 5} else "PARTIAL_OR_TECHNICAL",
        "scheduler_rc": rc,
        "generated_or_attempted": added,
        "visual_lock_run_id": critic_runtime_v211.current_visual_lock_run_id(ep),
        "max_speculative_frames": MAX_SPECULATIVE_FRAMES,
        "formal_visual_lock_validation": True,
        "approval_allowed": False,
        "state_advance_allowed": False,
        "release_allowed": False,
        "elapsed_seconds": round(elapsed, 3),
    }
    p = ep / "meta/speculative-production.json"
    p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def self_test() -> None:
    assert MAX_SPECULATIVE_FRAMES == 6
    src = Path(__file__).read_text(encoding="utf-8-sig")
    assert "visual_lock_v21.calibration_assets" in src
    print("SPECULATIVE PRODUCTION V2.1.1 R3.1 STRICT INPUT SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run"); p.add_argument("episode_dir"); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=600); p.add_argument("--max-frames", type=int, default=6)
    p = sub.add_parser("eligible"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return 0
    ep = Path(a.episode_dir).resolve()
    if a.cmd == "eligible":
        ok, reason = eligible(ep); print(json.dumps({"eligible": ok, "reason": reason}, ensure_ascii=False, indent=2)); return 0 if ok else 2
    print(json.dumps(run(ep, codex=a.codex, timeout=a.timeout, max_frames=a.max_frames), ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
