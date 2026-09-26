from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/p1_character_cutover_evidence.py"
spec = importlib.util.spec_from_file_location("p1_character_cutover_evidence", SCRIPT)
evidence = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(evidence)


def _sources():
    return {
        "p0": {"commit_gate_ready": True},
        "p0_baseline": {"git_worktree_clean": True, "summary": {"successful_runs": 5, "failed_runs": 0}},
        "probe": {"source_authority_unchanged": True, "comparison": {"legacy_valid": True, "shadow_valid": True, "canonical_side_effect": False}},
        "shadow_smoke": {"authority_unchanged": True, "comparison": {"structural_equal": True, "canonical_side_effect": False}},
        "paired": {
            "schema_version": 2, "pass": True, "valid_run_count": 5,
            "checks": {key: True for key in (
                "minimum_valid_runs", "all_valid_runs_semantic_equivalent", "telemetry_complete",
                "no_failure_timeout", "authority_zero_regression", "fixed_provider_model",
                "wall_regression_within_5pct", "token_regression_within_10pct",
            )},
        },
        "original_cutover_record": {
            "production_cutover_performed": True,
            "checks": {key: True for key in (
                "cutover_gate_ready", "paired_benchmark_pass", "paired_authority_zero_regression",
                "production_smoke_pass", "receipt_committed", "legacy_fallback_not_used",
            )},
        },
    }


def _post_state():
    return {"agent_runtime": {"adapters": {"character_finalize": {
        "production_enabled": True, "shadow_enabled": False, "legacy_fallback_on_technical": True,
    }}}}


def _health(gate, *, gate_hash="a" * 64, record_hash=None):
    return evidence.post_cutover_health(
        config=_post_state(),
        record={"production_cutover_performed": True, "status": "PRODUCTION_ENABLED"},
        pre_gate=gate,
        smoke={"pass": True, "receipt_status": "COMMITTED", "legacy_fallback_active": False},
        record_gate_sha256=record_hash or gate_hash,
        pre_gate_sha256=gate_hash,
    )


def test_shadow_phase_gate_recomputes_to_pass_from_prerequisite_evidence():
    gate = evidence.reconstruct_pre_cutover_gate(**_sources())
    assert gate["status"] == "PASS"
    assert gate["adapter_state_at_gate"] == {"shadow_enabled": True, "production_enabled": False}


def test_post_cutover_shadow_false_is_expected_and_health_passes():
    gate = evidence.reconstruct_pre_cutover_gate(**_sources())
    health = _health(gate)
    assert health["status"] == "PASS"
    assert health["checks"]["shadow_disabled_in_production"] is True


def test_health_output_is_separate_from_pre_cutover_gate(tmp_path):
    pre_path = tmp_path / "pre-cutover.json"
    health_path = tmp_path / "post-health.json"
    pre_path.write_text('{"status":"PASS"}\n', encoding="utf-8")
    before = hashlib.sha256(pre_path.read_bytes()).hexdigest()
    health_path.write_text(json.dumps(_health(evidence.reconstruct_pre_cutover_gate(**_sources()))), encoding="utf-8")
    assert hashlib.sha256(pre_path.read_bytes()).hexdigest() == before
    assert health_path.exists()


def test_production_record_must_reference_original_pass_gate_hash():
    gate = evidence.reconstruct_pre_cutover_gate(**_sources())
    assert _health(gate)["checks"]["record_references_pre_cutover_gate"] is True
    assert _health(gate, record_hash="wrong")["checks"]["record_references_pre_cutover_gate"] is False


def test_post_cutover_health_does_not_require_shadow_enabled():
    gate = evidence.reconstruct_pre_cutover_gate(**_sources())
    health = _health(gate)
    assert health["status"] == "PASS"
    assert health["adapter_state"]["shadow_enabled"] is False


def test_missing_original_cutover_evidence_fails_closed():
    sources = _sources()
    sources["original_cutover_record"] = {}
    gate = evidence.reconstruct_pre_cutover_gate(**sources)
    assert gate["status"] == "BLOCKED"
    assert "HISTORICAL_CUTOVER_GATE_WAS_READY" in gate["blockers"]


def test_immutable_pre_gate_cannot_be_overwritten(tmp_path):
    path = tmp_path / "pre-gate.json"
    evidence.write_immutable_pre_gate(path, {"status": "PASS"})
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        evidence.write_immutable_pre_gate(path, {"status": "BLOCKED"})
    except FileExistsError:
        pass
    else:
        raise AssertionError("pre-cutover evidence overwrite must fail closed")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
