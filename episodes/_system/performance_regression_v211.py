#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1.1 R3.1 performance regression.

Separates executable fault-path replay from target-budget math. Budget numbers are goals,
not simulated real completion times and never replace measured Episode telemetry.
"""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import json
from pathlib import Path

import runtime_fault_replay_v211
import speculative_production

ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIR = ROOT / "tests/performance/baselines"
REPLAY_DIR = ROOT / "tests/performance/replays"
REPORT = ROOT / "reports/performance-replay-v211.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _func_source(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            end = getattr(node, "end_lineno", node.lineno)
            return "\n".join(lines[node.lineno - 1:end])
    raise AssertionError(f"function not found: {name} in {path}")


def dependency_policy_check() -> dict:
    source = _func_source(ROOT / "episodes/_system/image_scheduler.py", "directive_dependency")
    ok = "generation_depends_on" in source and "escalation_from" not in source
    return {"passed": ok, "generation_depends_on_explicit": "generation_depends_on" in source,
            "escalation_from_removed_from_generation_dependency": "escalation_from" not in source}


def handoff_boundary_check() -> dict:
    source = _func_source(ROOT / "episodes/_system/preproduction_handoff.py", "stable_story_gate_subset")
    ok = '"calibration"' not in source and '"environment_contract"' in source and '"frame_directives"' in source
    return {"passed": ok, "runtime_calibration_excluded": '"calibration"' not in source}


def strict_speculative_input_check() -> dict:
    source = _func_source(ROOT / "episodes/_system/speculative_production.py", "visual_lock_candidates_ready")
    ok = "visual_lock_v21.calibration_assets" in source
    return {"passed": ok, "formal_visual_lock_validator_reused": ok}


def critical_path_telemetry_check() -> dict:
    source = _func_source(ROOT / "episodes/_system/episode_performance.py", "_critical_path_summary")
    ok = all(x in source for x in ("critical_path_seconds", "parallel_saved_seconds", "dependency_chain"))
    return {"passed": ok, "overlap_aware": "image_backend_union_wall_seconds" in source}


def run_replay(replay_path: Path) -> dict:
    replay = read_json(replay_path)
    baseline_id = replay["baseline_id"]
    matches = list(BASELINE_DIR.glob(f"{baseline_id}.json"))
    if not matches:
        raise ValueError(f"baseline missing: {baseline_id}")
    baseline = read_json(matches[0])

    target_budget_parts = replay.get("target_budget_seconds") or replay.get("budget_path_seconds") or {}
    target_budget = float(sum(float(v) for v in target_budget_parts.values()))
    baseline_seconds = float(baseline.get("image_continue_wall_seconds") or 0)
    reduction = ((baseline_seconds - target_budget) / baseline_seconds) if baseline_seconds else None

    fault = runtime_fault_replay_v211.run_fault_path()
    dep = dependency_policy_check()
    handoff = handoff_boundary_check()
    strict_input = strict_speculative_input_check()
    critical = critical_path_telemetry_check()
    acceptance = replay.get("acceptance") or {}
    bound_ok = speculative_production.MAX_SPECULATIVE_FRAMES == int(acceptance.get("speculative_max_frames") or 6)
    target_within_hard_budget = target_budget <= float(acceptance.get("critical_path_max_seconds") or 7200)

    checks = {
        "handoff_runtime_state_not_authority": handoff,
        "narrative_vs_generation_dependency": dep,
        "formal_visual_lock_validator_for_speculative": strict_input,
        "critical_path_telemetry_present": critical,
        "fault_path_replay": {"passed": bool(fault.get("passed")), **fault},
        "technical_failure_content_isolation": {"passed": bool(fault.get("technical_failure_content_isolation")),
                                                  "derived_from_fault_replay": True},
        "critic_attempt_freshness": {"passed": fault.get("stale_previous_attempt_allowed") is False,
                                     "derived_from_fault_replay": True},
        "bounded_speculative_production": {"passed": bound_ok and bool(fault.get("speculative_bound_respected")),
                                           "max_frames": speculative_production.MAX_SPECULATIVE_FRAMES},
        "global_blocking": {"passed": fault.get("global_stop") is False,
                            "expected": False, "derived_from_fault_replay": True},
        "target_budget_closure": {"passed": target_within_hard_budget,
                                  "target_budget_seconds": target_budget,
                                  "is_measurement": False},
    }
    passed = all(bool((v or {}).get("passed")) for v in checks.values())
    result = {
        "schema_version": 2,
        "generated_at": now(),
        "replay_id": replay.get("replay_id"),
        "baseline_id": baseline_id,
        "fault_path_executed": True,
        "image_backend_invoked": False,
        "baseline_image_continue_seconds": baseline_seconds,
        "baseline_image_continue_minutes": round(baseline_seconds / 60.0, 2),
        "target_budget_seconds": round(target_budget, 3),
        "target_budget_minutes": round(target_budget / 60.0, 2),
        "target_budget_parts_seconds": target_budget_parts,
        "target_budget_reduction_ratio_vs_baseline": round(reduction, 4) if reduction is not None else None,
        "target_budget_is_not_simulated_wall_clock": True,
        "checks": checks,
        "summary": {"passed": passed, "check_count": len(checks)},
        "note": "Fault-path checks execute runtime state/eligibility logic. The target budget is a release objective, not a measured or simulated real production duration.",
    }
    write_json(REPORT, result)
    return result


def self_test() -> None:
    assert speculative_production.MAX_SPECULATIVE_FRAMES == 6
    result = runtime_fault_replay_v211.run_fault_path()
    assert result["passed"]
    print("PERFORMANCE REGRESSION V2.1.1 R3.1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("replay"); p.add_argument("replay", nargs="?", default="PERF-REPLAY-V2.1.1-20260831-停电夜蜕壳")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return 0
    path = Path(a.replay)
    if not str(a.replay).lower().endswith(".json") and not path.is_absolute():
        path = REPLAY_DIR / f"{a.replay}.json"
    elif not path.is_absolute():
        path = (ROOT / path).resolve()
    result = run_replay(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["summary"]["passed"] else 2

if __name__ == "__main__": raise SystemExit(main())
