from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/p1_character_cutover_apply.py"
spec = importlib.util.spec_from_file_location("p1_character_cutover_apply", SCRIPT)
cutover = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cutover)


def _gate():
    return {
        "kind": "p1_character_pre_cutover_gate",
        "immutable": True,
        "status": "PASS",
        "production_cutover_performed": False,
        "blockers": [],
        "generated_at": "2026-09-26T19:00:00+08:00",
        "adapter_state_at_gate": {
            "shadow_enabled": True,
            "production_enabled": False,
        },
        "checks": {
            "p0_commit_gate": True,
            "clean_head_protocol_baseline": True,
            "shadow_probe_valid": True,
            "shadow_smoke_valid": True,
            "paired_benchmark_pass": True,
            "historical_cutover_gate_was_ready": True,
            "historical_production_smoke_pass": True,
        },
        "proof": {"method": "recomputed_from_preserved_prerequisite_evidence"},
        "source_evidence": {
            "fixture": {
                "path": "reports/p0-agent-acceptance-20260926.json",
                "sha256": cutover.sha256_file(ROOT / "reports/p0-agent-acceptance-20260926.json"),
            },
            "paired": {
                "path": "reports/p1-character-paired-benchmark-20260926.json",
                "sha256": cutover.sha256_file(ROOT / "reports/p1-character-paired-benchmark-20260926.json"),
            },
        },
    }


def _benchmark(valid_runs=5):
    return {
        "schema_version": 2,
        "generated_at": "2026-09-26T18:59:00+08:00",
        "valid_run_count": valid_runs,
        "pass": True,
        "checks": {
            "minimum_valid_runs": valid_runs >= 5,
            "all_valid_runs_semantic_equivalent": True,
            "telemetry_complete": True,
            "no_failure_timeout": True,
            "authority_zero_regression": True,
            "fixed_provider_model": True,
            "wall_regression_within_5pct": True,
            "token_regression_within_10pct": True,
        },
    }


def _state(shadow=True, production=False):
    return {
        "shadow_enabled": shadow,
        "production_enabled": production,
        "legacy_fallback_on_technical": True,
    }


def test_preflight_accepts_only_ready_shadow_state_with_formal_series():
    assert cutover.validate_preflight(_gate(), _benchmark(), _state()) == []


def test_preflight_rejects_less_than_five_valid_runs():
    errors = cutover.validate_preflight(_gate(), _benchmark(4), _state())
    assert any("fewer than five valid runs" in item for item in errors)
    assert any("minimum_valid_runs" in item for item in errors)


def test_preflight_rejects_already_enabled_production():
    errors = cutover.validate_preflight(
        _gate(), _benchmark(), _state(shadow=False, production=True)
    )
    assert any("shadow enabled before apply" in item for item in errors)
    assert any("production disabled before apply" in item for item in errors)


def test_preflight_rejects_gate_older_than_benchmark():
    gate = _gate()
    gate["generated_at"] = "2026-09-26T18:58:00+08:00"
    errors = cutover.validate_preflight(gate, _benchmark(), _state())
    assert any("generated after the paired benchmark" in item for item in errors)


def test_preflight_rejects_missing_immutable_pre_cutover_evidence():
    gate = _gate()
    gate["source_evidence"] = {}
    errors = cutover.validate_preflight(gate, _benchmark(), _state())
    assert any("source evidence is missing or changed" in item for item in errors)


def test_transition_changes_only_character_flags():
    source = """agent_runtime:
  adapters:
    character_finalize:
      shadow_enabled: true
      production_enabled: false
      legacy_fallback_on_technical: true
    world_prepare:
      shadow_enabled: false
      production_enabled: false
runtime:
  preferred_runtime: WORK
"""
    updated = cutover.transition_config_text(
        source, shadow_enabled=False, production_enabled=True
    )
    assert "character_finalize:\n      shadow_enabled: false\n      production_enabled: true" in updated
    assert "world_prepare:\n      shadow_enabled: false\n      production_enabled: false" in updated
    assert "legacy_fallback_on_technical: true" in updated
    assert "preferred_runtime: WORK" in updated
