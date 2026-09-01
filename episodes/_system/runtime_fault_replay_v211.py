#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Story OS V2.1.1 R3.1 fault-path replay.

This executes the real critic-runtime and speculative eligibility/selection code against
a temporary Episode state while monkeypatching only external authority/image backends.
It validates state transitions; it does NOT claim real image latency.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import tempfile
from pathlib import Path

import critic_runtime_v211
import speculative_production


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _visual_lock_run(ep: Path, run_id: str, *, append: bool = False) -> None:
    p = ep / critic_runtime_v211.EP_PERF_REL
    if append and p.is_file():
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("stages", {}).setdefault("VISUAL_LOCK", {}).setdefault("runs", []).append({
            "run_id": run_id, "started_at": now(), "status": "RUNNING"
        })
    else:
        data = {"stages": {"VISUAL_LOCK": {"runs": [{
            "run_id": run_id, "started_at": now(), "status": "RUNNING"
        }]}}}
    write_json(p, data)


def run_fault_path() -> dict:
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        write_json(ep / "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        write_json(ep / "meta/story-gates.json", {
            "visual": {"calibration": {"items": [
                {"role": role, "decision": "candidate", "asset_path": f"media/{i}.png", "sha256": f"sha{i}"}
                for i, role in enumerate(("ordinary_baseline", "worst_capture_condition", "first_major_anomaly", "high_impact_admission"), 1)
            ]}}
        })
        prompt_dir = ep / "prompts"
        prompt_dir.mkdir()
        for i in range(1, 21):
            (prompt_dir / f"{i:02d}.txt").write_text(f"frame {i}\n", encoding="utf-8")

        _visual_lock_run(ep, "vl-r3-a")
        first = critic_runtime_v211.record_technical_failure(
            ep, issue_codes=["INPUT_IMAGES_UNAVAILABLE"], attempt=1, log="critic-a.log")
        second = critic_runtime_v211.record_technical_failure(
            ep, issue_codes=["INPUT_IMAGES_UNAVAILABLE"], attempt=2, log="critic-a.log")
        technical_is_not_content = (
            first.get("status") == "TECHNICAL_BLOCKED" and
            second.get("status") == "CIRCUIT_OPEN" and
            all(str(x.get("status") or "").startswith(("TECHNICAL", "CIRCUIT")) for x in second.get("events") or [])
        )

        # Only external/authority-heavy dependencies are stubbed. Eligibility and
        # selection are the real speculative_production functions under test.
        originals = {
            "handoff_verify": speculative_production.preproduction_handoff.verify,
            "calibration_assets": speculative_production.visual_lock_v21.calibration_assets,
            "discover_prompt_dir": speculative_production.discover_prompt_dir,
            "frame_count": speculative_production.frame_contract.frame_count,
            "ledger_state": speculative_production.image_scheduler.ledger_state,
            "directive_dependency": speculative_production.image_scheduler.directive_dependency,
        }
        try:
            speculative_production.preproduction_handoff.verify = lambda _ep: []
            speculative_production.visual_lock_v21.calibration_assets = lambda _ep: [
                {"role": role, "asset_path": f"media/{i}.png", "sha256": f"sha{i}"}
                for i, role in enumerate(("ordinary_baseline", "worst_capture_condition", "first_major_anomaly", "high_impact_admission"), 1)
            ]
            speculative_production.discover_prompt_dir = lambda _ep: prompt_dir
            speculative_production.frame_contract.frame_count = lambda _ep: 20
            speculative_production.image_scheduler.ledger_state = lambda _ep, _frame: "PENDING"
            # One real hard dependency: frame 6 needs frame 2. Narrative escalation is absent.
            speculative_production.image_scheduler.directive_dependency = lambda _ep, frame: [2] if frame == 6 else []

            eligible_now, eligible_reason = speculative_production.eligible(ep)
            selected = speculative_production.select_frames(ep, 6)

            _visual_lock_run(ep, "vl-r3-b", append=True)
            stale_eligible, stale_reason = speculative_production.eligible(ep)
        finally:
            speculative_production.preproduction_handoff.verify = originals["handoff_verify"]
            speculative_production.visual_lock_v21.calibration_assets = originals["calibration_assets"]
            speculative_production.discover_prompt_dir = originals["discover_prompt_dir"]
            speculative_production.frame_contract.frame_count = originals["frame_count"]
            speculative_production.image_scheduler.ledger_state = originals["ledger_state"]
            speculative_production.image_scheduler.directive_dependency = originals["directive_dependency"]

        result = {
            "fault_injected": ["INPUT_IMAGES_UNAVAILABLE", "REPEATED_CRITIC_TECHNICAL_FAILURE"],
            "state_path": [first.get("status"), second.get("status"), "SPECULATIVE_ELIGIBLE" if eligible_now else "SPECULATIVE_BLOCKED"],
            "technical_failure_content_isolation": technical_is_not_content,
            "circuit_opened": second.get("status") == "CIRCUIT_OPEN",
            "speculative_current_attempt_allowed": eligible_now,
            "speculative_current_attempt_reason": eligible_reason,
            "selected_frames": selected,
            "speculative_bound_respected": 0 < len(selected) <= speculative_production.MAX_SPECULATIVE_FRAMES,
            "stale_previous_attempt_allowed": stale_eligible,
            "stale_previous_attempt_reason": stale_reason,
            "global_stop": not eligible_now,
            "image_backend_invoked": False,
            "simulation_scope": "runtime state transitions + eligibility + dependency-safe selection",
        }
        result["passed"] = all([
            result["technical_failure_content_isolation"],
            result["circuit_opened"],
            result["speculative_current_attempt_allowed"],
            result["speculative_bound_respected"],
            result["stale_previous_attempt_allowed"] is False,
            result["global_stop"] is False,
        ])
        return result


def self_test() -> None:
    result = run_fault_path()
    assert result["passed"], json.dumps(result, ensure_ascii=False, indent=2)
    print("RUNTIME FAULT REPLAY V2.1.1 R3.1 PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run"); sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test":
        self_test(); return 0
    result = run_fault_path()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 2

if __name__ == "__main__": raise SystemExit(main())
