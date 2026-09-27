from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("p2_world_cutover_gate", ROOT / "scripts/p2_world_cutover_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
benchmark_spec = importlib.util.spec_from_file_location(
    "p2_world_paired_benchmark", ROOT / "scripts/p2_world_paired_benchmark.py"
)
benchmark = importlib.util.module_from_spec(benchmark_spec)
benchmark_spec.loader.exec_module(benchmark)


def _config():
    return {"agent_runtime": {"adapters": {"world_prepare": {
        "shadow_enabled": True, "production_enabled": False,
        "legacy_fallback_on_technical": True,
    }}}}


def _smoke():
    return {"status": "PASS", "checks": {
        "agent_runtime_success": True, "candidate_valid": True, "semantic_pass": True,
        "shadow_execution_type": True, "shadow_identity": True, "allowed_tools_empty": True,
        "authority_zero_regression": True, "image_generation_invoked": False,
        "episode_state_unchanged": True,
    }}


def _benchmark():
    return {"pass": True, "valid_run_count": 5, "telemetry_complete": True,
            "authority_zero_regression": True,
            "checks": {"minimum_valid_runs": True, "telemetry_complete": True,
                       "all_valid_runs_semantic_equivalent": True, "no_failure_timeout": True,
                       "authority_zero_regression": True, "fixed_provider_model": True,
                       "wall_regression_within_5pct": True, "token_regression_within_10pct": True},
            "medians": {"wall_regression_fraction": -0.11, "token_regression_fraction": -0.03}}


def test_cutover_gate_requires_all_evidence_and_measurable_value():
    report = gate.evaluate(p0={"commit_gate_ready": True}, smoke=_smoke(),
                           benchmark=_benchmark(), config=_config())
    assert report["status"] == "READY_FOR_PRODUCTION_CUTOVER"
    assert report["production_cutover_performed"] is False


def test_cutover_gate_fails_closed_on_missing_preconditions():
    report = gate.evaluate(p0={}, smoke={}, benchmark={}, config=_config())
    assert report["status"] == "BLOCKED"
    assert "P0_COMMIT_GATE_NOT_READY" in report["blockers"]
    assert "WORLD_REAL_MODEL_TELEMETRY_INCOMPLETE" in report["blockers"]
    assert "WORLD_NO_MEASURABLE_AGENT_VALUE" in report["blockers"]


def test_cutover_gate_does_not_accept_equivalence_as_agent_value():
    benchmark = _benchmark()
    benchmark["medians"]["wall_regression_fraction"] = 0.0
    benchmark["medians"]["token_regression_fraction"] = 0.0
    report = gate.evaluate(p0={"commit_gate_ready": True}, smoke=_smoke(),
                           benchmark=benchmark, config=_config())
    assert report["status"] == "BLOCKED"
    assert "WORLD_NO_MEASURABLE_AGENT_VALUE" in report["blockers"]


def test_benchmark_uses_medians_and_omits_percentiles_for_five_pairs():
    manifest = {"episode": "episode", "snapshot_id": "snap", "provider": "provider",
                "model": "model", "reasoning_effort": "medium", "authority_scope": ["scope"]}
    rows = []
    for index, wall in enumerate((10, 20, 30, 40, 50), 1):
        rows.append({
            "pair_index": index, "valid": True,
            "checks": {"telemetry_complete": True, "semantic_equivalent": True,
                       "no_failure_timeout": True, "authority_zero_regression": True,
                       "fixed_provider_model_reasoning": True},
            "legacy": {"wall_seconds": wall, "input_tokens": 100, "output_tokens": 20},
            "agent": {"wall_seconds": wall - 1, "input_tokens": 100, "output_tokens": 20},
        })
    report = benchmark.summarize(manifest, rows)
    assert report["valid_run_count"] == 5
    assert report["medians"]["legacy_wall_seconds"] == 30
    assert report["medians"]["agent_wall_seconds"] == 29
    assert "p90" not in report and "p95" not in report


def test_benchmark_counts_only_valid_pairs():
    manifest = {"episode": "episode", "snapshot_id": "snap", "provider": "provider",
                "model": "model", "reasoning_effort": "medium", "authority_scope": []}
    report = benchmark.summarize(manifest, [{"pair_index": 1, "valid": False,
        "checks": {"telemetry_complete": False, "semantic_equivalent": False,
                   "no_failure_timeout": False, "authority_zero_regression": False,
                   "fixed_provider_model_reasoning": False},
        "legacy": {}, "agent": {}}])
    assert report["valid_run_count"] == 0
    assert report["pass"] is False
