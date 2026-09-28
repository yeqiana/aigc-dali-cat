from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "episodes/_system"))
sys.path.insert(0, str(ROOT / "episodes/_system/agents"))

from scripts import p3_preimage_semantic_critic_cutover_gate as gate
from scripts import p3_preimage_semantic_critic_repair_assessment as repair


def _read(root: Path, key: str) -> dict:
    return json.loads((root / gate.EVIDENCE[key]).read_text(encoding="utf-8"))


def _benchmark(root: Path) -> dict:
    return _read(root, "benchmark")


def test_repair_scope_precision_recall_f1_are_set_based():
    benchmark = {"cases": [
        {"sample_id": "one-of-two", "reference_label": "FAIL", "critic_decision": "REPAIR",
         "repair_scope_expected": ["A", "B"], "repair_scope_observed": ["A"]},
        {"sample_id": "extra", "reference_label": "FAIL", "critic_decision": "REPAIR",
         "repair_scope_expected": ["A"], "repair_scope_observed": ["A", "B"]},
        {"sample_id": "exact", "reference_label": "FAIL", "critic_decision": "REPAIR",
         "repair_scope_expected": ["A", "B"], "repair_scope_observed": ["A", "B"]},
        {"sample_id": "empty-label", "reference_label": "FAIL", "critic_decision": "REPAIR",
         "repair_scope_expected": [], "repair_scope_observed": []},
    ]}
    result = repair.assess(benchmark, benchmark_sha256="b" * 64, fixture_sha256="f" * 64)
    rows = {row["sample_id"]: row for row in result["samples"]}
    assert (rows["one-of-two"]["precision"], rows["one-of-two"]["recall"], rows["one-of-two"]["f1"]) == (1.0, 0.5, 2 / 3)
    assert (rows["extra"]["precision"], rows["extra"]["recall"], rows["extra"]["f1"]) == (0.5, 1.0, 2 / 3)
    assert (rows["exact"]["precision"], rows["exact"]["recall"], rows["exact"]["f1"]) == (1.0, 1.0, 1.0)
    assert "empty-label" not in rows


def test_existing_benchmark_repair_assessment_exposes_incomplete_scope():
    from scripts.p3_preimage_semantic_critic_cutover_gate import ROOT
    result = repair.assess(_benchmark(ROOT), benchmark_sha256="b" * 64)
    rows = {row["sample_id"]: row for row in result["samples"]}
    incomplete = rows["preimage-pov-continuity-conflict"]
    assert incomplete["precision"] == 1.0
    assert incomplete["recall"] == 0.5
    assert incomplete["f1"] == 2 / 3
    assert result["repair_scope_recall_median"] == 1.0
    assert result["minimum_repair_scope_recall"] == 0.5
    assert result["repair_value_v2"] is True
    assert result["repair_value_blocking"] is False


def test_issue_code_recall_is_not_comparable_without_taxonomy():
    from scripts.p3_preimage_semantic_critic_cutover_gate import ROOT
    result = repair.assess(_benchmark(ROOT), benchmark_sha256="b" * 64)
    assert result["issue_code_recall"] == "NOT_COMPARABLE"
    assert result["issue_code_taxonomy_mapping_available"] is False


def test_current_gate_is_conditional_when_real_episode_set_is_absent():
    from scripts.p3_preimage_semantic_critic_cutover_gate import ROOT
    result = gate.evaluate(ROOT)
    assert result["status"] == "CONDITIONAL"
    assert result["mandatory_checks"]
    assert all(result["mandatory_checks"].values())
    assert result["real_episode_candidate_count"] == 4
    assert result["real_episode_eligible_count"] == 0
    assert result["production_cutover_performed"] is False
    assert "NO_REAL_PREIMAGE_CANDIDATE_SET_SHADOW_EVIDENCE" in result["warnings"]


def test_gate_blocked_for_missing_benchmark_safety_or_quality_evidence():
    from scripts.p3_preimage_semantic_critic_cutover_gate import ROOT
    cases = {
        "minimum pairs": ("benchmark", lambda d: d.update(valid_pair_count=4)),
        "quality": ("benchmark", lambda d: d.update(quality_value=False)),
        "false reject": ("benchmark", lambda d: d.update(critic_false_reject_count=1)),
        "telemetry": ("benchmark", lambda d: d.update(telemetry_complete=False)),
        "authority": ("benchmark", lambda d: d.update(authority_zero_regression=False)),
        "smoke": ("smoke", lambda d: d.update(status="FAILED")),
    }
    for name, (key, mutate) in cases.items():
        override = {key: copy.deepcopy(_read(ROOT, key))}
        mutate(override[key])
        result = gate.evaluate(ROOT, evidence_overrides=override)
        assert result["status"] == "BLOCKED", name


def test_unexpected_production_or_shadow_off_fails_closed():
    from scripts.p3_preimage_semantic_critic_cutover_gate import ROOT
    cfg = gate.storyos_config._load(ROOT / "config/storyos.yaml")
    bad_production = copy.deepcopy(cfg)
    adapter = bad_production["agent_runtime"]["adapters"]["preimage_semantic_critic"]
    adapter["production_enabled"] = True
    assert gate.evaluate(ROOT, config_override=bad_production)["status"] == "BLOCKED"
    bad_shadow = copy.deepcopy(cfg)
    bad_shadow["agent_runtime"]["adapters"]["preimage_semantic_critic"]["shadow_enabled"] = False
    assert gate.evaluate(ROOT, config_override=bad_shadow)["status"] == "BLOCKED"


def test_changed_assessment_benchmark_sha_blocks_gate():
    from scripts.p3_preimage_semantic_critic_cutover_gate import ROOT
    assessment = _read(ROOT, "repair_assessment")
    assessment["source_benchmark"]["sha256"] = "0" * 64
    result = gate.evaluate(ROOT, evidence_overrides={"repair_assessment": assessment})
    assert result["status"] == "BLOCKED"
    assert result["mandatory_checks"]["repair_assessment_benchmark_sha_matches"] is False


def test_status_classifier_requires_real_episode_for_ready():
    assert gate.classify_status({"all_safety_checks": True}, real_episode_shadow_evidence=False) == "CONDITIONAL"
    assert gate.classify_status({"all_safety_checks": True}, real_episode_shadow_evidence=True) == "READY"
    assert gate.classify_status({"safety": False}, real_episode_shadow_evidence=True) == "BLOCKED"


def test_gate_report_write_is_immutable(tmp_path: Path):
    path = tmp_path / "gate.json"
    gate.write_immutable(path, {"status": "CONDITIONAL"})
    try:
        gate.write_immutable(path, {"status": "READY"})
    except FileExistsError:
        pass
    else:
        raise AssertionError("gate evidence was overwritten")
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "CONDITIONAL"
