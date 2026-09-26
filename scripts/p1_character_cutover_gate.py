#!/usr/bin/env python3
"""Fail-closed P1 Character Agent Production cutover gate.

This gate never performs the cutover. It only evaluates durable evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
import sys
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import storyos_config


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def execution_evidence(candidate: dict) -> dict:
    raw = candidate.get("model_execution") if isinstance(candidate, dict) else None
    raw = raw if isinstance(raw, dict) else {}
    required = (
        "real_model_execution",
        "wall_seconds",
        "input_tokens",
        "output_tokens",
        "repeated_reads",
        "failure",
        "timeout",
    )
    missing = [key for key in required if key not in raw]
    valid = (
        raw.get("real_model_execution") is True
        and isinstance(raw.get("wall_seconds"), (int, float))
        and not isinstance(raw.get("wall_seconds"), bool)
        and float(raw.get("wall_seconds")) >= 0
        and all(type(raw.get(key)) is int and raw.get(key) >= 0 for key in ("input_tokens", "output_tokens", "repeated_reads"))
        and all(isinstance(raw.get(key), bool) for key in ("failure", "timeout"))
    )
    return {
        "complete": not missing and valid,
        "missing": missing,
        "real_model_execution": raw.get("real_model_execution") is True,
        "wall_seconds": raw.get("wall_seconds"),
        "input_tokens": raw.get("input_tokens"),
        "output_tokens": raw.get("output_tokens"),
        "repeated_reads": raw.get("repeated_reads"),
        "failure": raw.get("failure"),
        "timeout": raw.get("timeout"),
        "provider": raw.get("provider"),
        "model": raw.get("model"),
        "telemetry_source": raw.get("telemetry_source"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", default="reports/p0-agent-acceptance-20260926.json")
    ap.add_argument("--p0-baseline", default="reports/p0-preimage-agent-baseline-20260926.json")
    ap.add_argument("--legacy-baseline", default="reports/p1-preimage-production-baseline-20260926.json")
    ap.add_argument("--shadow-probe", default="reports/p1-character-shadow-probe-20260926.json")
    ap.add_argument("--shadow-smoke", default="reports/p1-character-shadow-smoke-20260926.json")
    ap.add_argument("--shadow-candidate", default=".storyos/tmp/p1-character-shadow-candidate.json")
    ap.add_argument("--semantic-review", default="reports/p1-character-shadow-semantic-review-20260926.json")
    ap.add_argument("--paired-benchmark", default="reports/p1-character-paired-benchmark-20260926.json")
    ap.add_argument("--output", default="reports/p1-character-cutover-gate-20260926.json")
    args = ap.parse_args()

    p0 = read_json(ROOT / args.p0)
    p0_baseline = read_json(ROOT / args.p0_baseline)
    legacy = read_json(ROOT / args.legacy_baseline)
    probe = read_json(ROOT / args.shadow_probe)
    smoke = read_json(ROOT / args.shadow_smoke)
    candidate = read_json(ROOT / args.shadow_candidate)
    semantic = read_json(ROOT / args.semantic_review)
    paired = read_json(ROOT / args.paired_benchmark)

    cfg = storyos_config.load_config()
    shadow_enabled = storyos_config.get_path(
        cfg, "agent_runtime.adapters.character_finalize.shadow_enabled", False
    ) is True
    production_enabled = storyos_config.get_path(
        cfg, "agent_runtime.adapters.character_finalize.production_enabled", False
    ) is True

    blockers: list[str] = []
    checks = {}

    checks["p0_commit_gate"] = p0.get("commit_gate_ready") is True
    if not checks["p0_commit_gate"]:
        blockers.append("P0_COMMIT_GATE_NOT_READY")

    summary = p0_baseline.get("summary") or {}
    checks["clean_head_protocol_baseline"] = bool(
        p0_baseline.get("git_worktree_clean") is True
        and int(summary.get("successful_runs") or 0) >= 5
        and int(summary.get("failed_runs") or 0) == 0
    )
    if not checks["clean_head_protocol_baseline"]:
        blockers.append("P0_BASELINE_NOT_FROZEN")

    checks["shadow_enabled"] = shadow_enabled
    if not shadow_enabled:
        blockers.append("CHARACTER_SHADOW_DISABLED")
    checks["production_disabled_before_cutover"] = not production_enabled
    if production_enabled:
        blockers.append("CHARACTER_PRODUCTION_ALREADY_ENABLED_BEFORE_GATE")

    checks["authority_zero_regression"] = bool(
        probe.get("source_authority_unchanged") is True
        and smoke.get("authority_unchanged") is True
        and (probe.get("comparison") or {}).get("canonical_side_effect") is False
        and (smoke.get("comparison") or {}).get("canonical_side_effect") is False
    )
    if not checks["authority_zero_regression"]:
        blockers.append("AUTHORITY_ZERO_REGRESSION_NOT_PROVEN")

    checks["shadow_candidate_valid"] = bool(
        not (probe.get("verifier_errors") or [])
        and (probe.get("comparison") or {}).get("legacy_valid") is True
        and (probe.get("comparison") or {}).get("shadow_valid") is True
    )
    if not checks["shadow_candidate_valid"]:
        blockers.append("SHADOW_CANDIDATE_INVALID")

    comparison = probe.get("comparison") or {}
    domain_semantic_pass = ((comparison.get("domain_semantic") or {}).get("semantic_equivalent") is True)
    semantic_pass = semantic.get("status") == "PASS" and semantic.get("semantic_equivalent") is True
    checks["semantic_equivalence"] = bool(
        comparison.get("structural_equal") is True or domain_semantic_pass or semantic_pass
    )
    if not checks["semantic_equivalence"]:
        blockers.append("SEMANTIC_EQUIVALENCE_REVIEW_REQUIRED")

    paired_checks = paired.get("checks") or {}
    paired_pass = bool(
        paired.get("pass") is True
        and int(paired.get("schema_version") or 0) >= 2
        and int(paired.get("valid_run_count") or 0) >= 5
        and paired_checks.get("minimum_valid_runs") is True
        and paired_checks.get("all_valid_runs_semantic_equivalent") is True
        and paired_checks.get("telemetry_complete") is True
        and paired_checks.get("no_failure_timeout") is True
        and paired_checks.get("authority_zero_regression") is True
        and paired_checks.get("fixed_provider_model") is True
        and paired_checks.get("wall_regression_within_5pct") is True
        and paired_checks.get("token_regression_within_10pct") is True
    )
    shadow_execution = dict(paired.get("shadow_execution") or {}) if paired_pass else execution_evidence(candidate)
    checks["shadow_execution_telemetry"] = shadow_execution["complete"]
    if not checks["shadow_execution_telemetry"]:
        blockers.append("SHADOW_MODEL_EXECUTION_TELEMETRY_INCOMPLETE")

    checks["shadow_no_failure_timeout"] = bool(
        shadow_execution["complete"]
        and shadow_execution.get("failure") is False
        and shadow_execution.get("timeout") is False
    )
    if shadow_execution["complete"] and not checks["shadow_no_failure_timeout"]:
        blockers.append("SHADOW_FAILURE_TIMEOUT_NOT_CLEARED")

    checks["paired_performance_benchmark"] = paired_pass
    checks["legacy_performance_baseline"] = bool(
        paired_pass or legacy.get("performance_baseline_eligible") is True
    )
    if not checks["legacy_performance_baseline"]:
        blockers.append("LEGACY_PERFORMANCE_TELEMETRY_INCOMPLETE")

    status = "READY_FOR_PRODUCTION_CUTOVER_REVIEW" if not blockers else "BLOCKED"
    report = {
        "schema_version": 1,
        "kind": "p1_character_agent_cutover_gate",
        "generated_at": now(),
        "status": status,
        "production_cutover_performed": False,
        "checks": checks,
        "blockers": blockers,
        "adapter_state": {
            "shadow_enabled": shadow_enabled,
            "production_enabled": production_enabled,
        },
        "shadow_execution_evidence": shadow_execution,
        "evidence": {
            "p0": args.p0,
            "p0_baseline": args.p0_baseline,
            "legacy_baseline": args.legacy_baseline,
            "shadow_probe": args.shadow_probe,
            "shadow_smoke": args.shadow_smoke,
            "shadow_candidate": args.shadow_candidate,
            "semantic_review": args.semantic_review,
            "paired_benchmark": args.paired_benchmark,
        },
        "note": (
            "Gate is fail-closed. It never infers missing wall/token/read/failure/timeout evidence "
            "and never performs a producer cutover."
        ),
    }
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "READY_FOR_PRODUCTION_CUTOVER_REVIEW" else 3


if __name__ == "__main__":
    raise SystemExit(main())
