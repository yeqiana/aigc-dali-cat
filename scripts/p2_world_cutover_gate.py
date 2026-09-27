#!/usr/bin/env python3
"""Fail-closed World Prepare pre-cutover evidence gate. This script never cuts over."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))
import storyos_config
import story_json


def read(path: Path) -> dict:
    value = story_json.read_json(path, default={})
    return value if isinstance(value, dict) else {}


def evaluate(*, p0: dict, smoke: dict, benchmark: dict, config: dict,
             quality_evidence: dict | None = None, recovery_evidence: dict | None = None) -> dict:
    adapters = storyos_config.get_path(config, "agent_runtime.adapters", {}) or {}
    world = adapters.get("world_prepare") or {}
    p0_ready = p0.get("commit_gate_ready") is True
    shadow_enabled = world.get("shadow_enabled") is True
    production_disabled = world.get("production_enabled") is False
    fallback = world.get("legacy_fallback_on_technical") is True
    smoke_checks = smoke.get("checks") or {}
    smoke_pass = smoke.get("status") == "PASS" and all((
        smoke_checks.get("agent_runtime_success") is True,
        smoke_checks.get("candidate_valid") is True,
        smoke_checks.get("semantic_pass") is True,
        smoke_checks.get("shadow_execution_type") is True,
        smoke_checks.get("shadow_identity") is True,
        smoke_checks.get("allowed_tools_empty") is True,
        smoke_checks.get("authority_zero_regression") is True,
        smoke_checks.get("image_generation_invoked") is False,
        smoke_checks.get("episode_state_unchanged") is True,
    ))
    checks = benchmark.get("checks") or {}
    benchmark_pass = bool(
        benchmark.get("pass") is True
        and int(benchmark.get("valid_run_count") or 0) >= 5
        and checks.get("minimum_valid_runs") is True
        and checks.get("telemetry_complete") is True
        and checks.get("all_valid_runs_semantic_equivalent") is True
        and checks.get("no_failure_timeout") is True
        and checks.get("authority_zero_regression") is True
        and checks.get("fixed_provider_model") is True
        and checks.get("wall_regression_within_5pct") is True
        and checks.get("token_regression_within_10pct") is True
    )
    medians = benchmark.get("medians") or {}
    wall_gain = medians.get("wall_regression_fraction")
    token_gain = medians.get("token_regression_fraction")
    speed_value = isinstance(wall_gain, (int, float)) and wall_gain <= -0.10
    token_value = isinstance(token_gain, (int, float)) and token_gain <= -0.20
    quality_value = (quality_evidence or {}).get("measurable_quality_improvement") is True
    recovery_value = (recovery_evidence or {}).get("measurable_recovery_improvement") is True
    value = any((speed_value, token_value, quality_value, recovery_value))
    checks_out = {
        "p0_commit_gate": p0_ready,
        "world_shadow_enabled": shadow_enabled,
        "world_production_disabled": production_disabled,
        "legacy_fallback_available": fallback,
        "world_real_model_shadow_smoke": smoke_pass,
        "candidate_valid_and_semantic": smoke_checks.get("candidate_valid") is True and smoke_checks.get("semantic_pass") is True,
        "real_model_telemetry_complete": benchmark.get("telemetry_complete") is True and checks.get("telemetry_complete") is True,
        "no_failure_timeout": checks.get("no_failure_timeout") is True,
        "minimum_five_valid_pairs": int(benchmark.get("valid_run_count") or 0) >= 5 and checks.get("minimum_valid_runs") is True,
        "paired_performance_safety": checks.get("wall_regression_within_5pct") is True and checks.get("token_regression_within_10pct") is True,
        "authority_zero_regression": benchmark.get("authority_zero_regression") is True and checks.get("authority_zero_regression") is True and smoke_checks.get("authority_zero_regression") is True,
        "measurable_value": value,
        "speed_value_ge_10pct": speed_value,
        "token_value_ge_20pct": token_value,
        "quality_value_evidence": quality_value,
        "recovery_value_evidence": recovery_value,
    }
    blockers = []
    names = {
        "p0_commit_gate": "P0_COMMIT_GATE_NOT_READY",
        "world_shadow_enabled": "WORLD_SHADOW_DISABLED",
        "world_production_disabled": "WORLD_PRODUCTION_ALREADY_ENABLED",
        "legacy_fallback_available": "WORLD_LEGACY_FALLBACK_UNAVAILABLE",
        "world_real_model_shadow_smoke": "WORLD_REAL_MODEL_SHADOW_SMOKE_MISSING_OR_FAILED",
        "candidate_valid_and_semantic": "WORLD_SEMANTIC_EQUIVALENCE_FAILED",
        "real_model_telemetry_complete": "WORLD_REAL_MODEL_TELEMETRY_INCOMPLETE",
        "no_failure_timeout": "WORLD_FAILURE_OR_TIMEOUT",
        "minimum_five_valid_pairs": "WORLD_MINIMUM_VALID_RUNS_NOT_MET",
        "paired_performance_safety": "WORLD_PERFORMANCE_REGRESSION_EXCEEDED",
        "authority_zero_regression": "WORLD_AUTHORITY_REGRESSION",
        "measurable_value": "WORLD_NO_MEASURABLE_AGENT_VALUE",
    }
    blockers.extend(names[key] for key, value in checks_out.items() if key in names and value is not True)
    return {
        "schema_version": 1,
        "kind": "p2_world_pre_cutover_gate",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "READY_FOR_PRODUCTION_CUTOVER" if not blockers else "BLOCKED",
        "production_cutover_performed": False,
        "checks": checks_out,
        "blockers": blockers,
        "adapter_state": {"shadow_enabled": shadow_enabled, "production_enabled": world.get("production_enabled"),
                          "legacy_fallback_on_technical": fallback},
        "paired_benchmark_medians": medians,
        "evidence": {
            "p0": "reports/p0-agent-acceptance-20260926.json",
            "real_model_shadow_smoke": "reports/p2-world-real-model-shadow-smoke-20260926.json",
            "paired_benchmark": "reports/p2-world-paired-benchmark-20260926.json",
        },
        "note": "Fail-closed evidence only. This gate never changes feature flags or performs production cutover.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p0", default="reports/p0-agent-acceptance-20260926.json")
    parser.add_argument("--smoke", default="reports/p2-world-real-model-shadow-smoke-20260926.json")
    parser.add_argument("--benchmark", default="reports/p2-world-paired-benchmark-20260926.json")
    parser.add_argument("--output", default="reports/p2-world-pre-cutover-gate-20260926.json")
    parser.add_argument("--quality-evidence")
    parser.add_argument("--recovery-evidence")
    args = parser.parse_args()
    report = evaluate(
        p0=read(ROOT / args.p0), smoke=read(ROOT / args.smoke),
        benchmark=read(ROOT / args.benchmark), config=storyos_config.load_config(),
        quality_evidence=read(ROOT / args.quality_evidence) if args.quality_evidence else None,
        recovery_evidence=read(ROOT / args.recovery_evidence) if args.recovery_evidence else None,
    )
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "READY_FOR_PRODUCTION_CUTOVER" else 3


if __name__ == "__main__":
    raise SystemExit(main())
