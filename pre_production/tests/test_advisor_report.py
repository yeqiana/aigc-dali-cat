#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests: Advisor Report, risk assessment and Memory Adapter."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.advisor import (  # noqa: E402
    assess_hook_risk,
    assess_risks,
    assess_similarity_risks,
    build_recommendations,
    build_report,
    confidence_level,
    decide,
)
from pre_production.memory_adapter import MemoryAdapter  # noqa: E402
from pre_production.similarity_analysis.evidence import build_evidence  # noqa: E402
from pre_production.story_dna.validator import (  # noqa: E402
    validate_advisor_report,
    validate_review_reference,
)
from pre_production.tests.support import assert_no_scores, build_dna  # noqa: E402

DECIDED_DNA = build_dna("CUR-01", "当前故事",
                        anomaly__anomaly_type=["spatial_overlap_anomaly"],
                        series_fit__differentiation_evidence=["declared"])

HOOK_EVIDENCE = [{"field": "narrative.hook_type", "token": "observational_witness_hook",
                  "keyword": "看见", "anchor": "一句话故事", "snippet": "看见远处灯队"}]


def evidence(level="MEDIUM", related="HIS-01", dims=None) -> dict:
    dims = dims or ["anomaly"]
    return build_evidence(current_story_id="CUR-01", related_episode_id=related,
                          related_title="历史" + related, risk_level=level,
                          matched_dimensions=dims, matched_features=["spatial_overlap_anomaly"],
                          explanation="命中同一异常机制，属于结构性相似提示。")


class DecideTests(unittest.TestCase):
    def test_no_risk_is_pass(self):
        self.assertEqual(decide([], DECIDED_DNA), "PASS")

    def test_low_only_is_pass(self):
        self.assertEqual(decide([{"level": "LOW"}], DECIDED_DNA), "PASS")

    def test_medium_is_warning(self):
        self.assertEqual(decide([{"level": "MEDIUM"}], DECIDED_DNA), "WARNING")

    def test_high_with_declared_differentiation_is_warning(self):
        self.assertEqual(decide([{"level": "HIGH"}], DECIDED_DNA), "WARNING")

    def test_high_without_differentiation_needs_revision(self):
        plain = build_dna("CUR-02", "无差异")
        self.assertEqual(decide([{"level": "HIGH"}], plain), "NEEDS_REVISION")

    def test_confidence_reflects_history_and_anomaly_hit(self):
        self.assertEqual(confidence_level(0, []), "LOW")
        self.assertEqual(confidence_level(5, [evidence("LOW", dims=["emotion"])]), "MEDIUM")
        self.assertEqual(confidence_level(3, [evidence("MEDIUM", dims=["anomaly"])]), "HIGH")


class RiskAssessmentTests(unittest.TestCase):
    def test_low_evidence_is_not_a_risk(self):
        self.assertEqual(assess_similarity_risks([evidence("LOW", dims=["emotion"])]), [])

    def test_medium_and_high_become_traceable_risks(self):
        risks = assess_similarity_risks([evidence("MEDIUM"), evidence("HIGH", related="HIS-02")])
        self.assertEqual([r["level"] for r in risks], ["MEDIUM", "HIGH"])
        for risk in risks:
            self.assertTrue(risk["evidence"], "risk must keep its evidence record")
            self.assertEqual(risk["type"], "similarity")

    def test_hook_risk_from_observational_only_opening(self):
        dna = build_dna("CUR-01", "当前", narrative__hook_type=["observational_witness_hook"])
        dna["evidence"] = list(HOOK_EVIDENCE)
        risk = assess_hook_risk(dna)
        self.assertIsNotNone(risk)
        self.assertEqual(risk["level"], "MEDIUM")
        self.assertEqual(risk["type"], "hook")

    def test_hook_risk_downgraded_when_active_choice_present(self):
        dna = build_dna("CUR-01", "当前",
                        narrative__hook_type=["observational_witness_hook", "active_choice_hook"])
        dna["evidence"] = list(HOOK_EVIDENCE)
        risk = assess_hook_risk(dna)
        self.assertEqual(risk["level"], "LOW")

    def test_hook_without_evidence_is_skipped(self):
        dna = build_dna("CUR-01", "当前", narrative__hook_type=["observational_witness_hook"])
        self.assertIsNone(assess_hook_risk(dna))

    def test_assess_risks_is_sorted_high_first(self):
        dna = build_dna("CUR-01", "当前", narrative__hook_type=["observational_witness_hook"])
        dna["evidence"] = list(HOOK_EVIDENCE)
        risks = assess_risks(dna, [evidence("MEDIUM"), evidence("HIGH", related="HIS-02")])
        self.assertEqual([r["level"] for r in risks], ["HIGH", "MEDIUM", "MEDIUM"])


class RecommendationTests(unittest.TestCase):
    def test_high_similarity_maps_to_mechanism_space_and_visual(self):
        risks = [{"type": "similarity", "level": "HIGH",
                  "matched_dimensions": ["anomaly", "setting", "visual_pattern"]}]
        self.assertEqual(build_recommendations(risks, DECIDED_DNA),
                         ["redesign_anomaly_mechanism", "avoid_repeated_spatial_expression",
                          "change_visual_pattern"])

    def test_medium_similarity_maps_to_increase_differentiation(self):
        risks = [{"type": "similarity", "level": "MEDIUM", "matched_dimensions": ["anomaly"]}]
        self.assertEqual(build_recommendations(risks, DECIDED_DNA),
                         ["increase_mechanism_differentiation"])

    def test_hook_risk_maps_to_first_frame_conflict(self):
        risks = [{"type": "hook", "level": "MEDIUM", "matched_dimensions": ["narrative.hook_type"]}]
        self.assertEqual(build_recommendations(risks, DECIDED_DNA),
                         ["strengthen_first_frame_conflict"])

    def test_low_risk_produces_no_recommendation(self):
        risks = [{"type": "similarity", "level": "LOW", "matched_dimensions": ["emotion"]}]
        self.assertEqual(build_recommendations(risks, DECIDED_DNA), [])


class AdvisorReportContractTests(unittest.TestCase):
    def setUp(self):
        self.evidence_items = [evidence("MEDIUM"), evidence("HIGH", related="HIS-02")]
        self.risks = assess_similarity_risks(self.evidence_items)
        self.report = build_report(
            episode_id="CUR-01", dna=DECIDED_DNA, evidence=self.evidence_items, risks=self.risks,
            recommendations=build_recommendations(self.risks, DECIDED_DNA), history_size=5,
            created_at="2026-09-11T00:00:00+08:00")

    def test_report_satisfies_its_contract(self):
        self.assertEqual(validate_advisor_report(self.report), [])

    def test_report_is_advisory_and_non_blocking(self):
        self.assertTrue(self.report["advisory_only"])
        for key, value in self.report["boundaries"].items():
            self.assertFalse(value, key + " must stay false in shadow mode")

    def test_report_has_no_score_like_keys(self):
        assert_no_scores(self, self.report, "advisor_report")

    def test_report_carries_decision_risks_evidence_recommendations_confidence(self):
        self.assertEqual(self.report["decision"], "WARNING")
        self.assertTrue(self.report["risks"])
        self.assertTrue(self.report["evidence"])
        self.assertTrue(self.report["recommendations"])
        self.assertIn(self.report["confidence"], ["LOW", "MEDIUM", "HIGH"])
        self.assertTrue(self.report["report_id"].startswith("PPA-"))

    def test_report_id_is_stable_for_the_same_source(self):
        again = build_report(episode_id="CUR-01", dna=DECIDED_DNA, evidence=[],
                             risks=[], recommendations=[], history_size=0,
                             created_at="2026-11-01T00:00:00+08:00")
        self.assertEqual(again["report_id"], self.report["report_id"])


class MemoryAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-memory-")
        self.addCleanup(self.tmp.cleanup)
        self.adapter = MemoryAdapter(repo_root=REPO_ROOT, store_dir=Path(self.tmp.name))

    def _report(self):
        items = [evidence("MEDIUM")]
        return build_report(episode_id="CUR-01", dna=DECIDED_DNA, evidence=items,
                            risks=assess_similarity_risks(items),
                            recommendations=["increase_mechanism_differentiation"],
                            history_size=2, created_at="2026-09-11T00:00:00+08:00")

    def test_build_review_reference_is_valid_and_non_committal(self):
        ref = self.adapter.build_review_reference(self._report())
        self.assertEqual(validate_review_reference(ref), [])
        self.assertEqual(ref["creator_decision"], "pending")
        self.assertEqual(ref["advisor_decision"], "WARNING")

    def test_save_review_reference_round_trips(self):
        report = self._report()
        path = self.adapter.save_review_reference(report, feedback="先按建议改机制")
        self.assertTrue(path.is_file())
        self.assertEqual(path.parent, Path(self.tmp.name) / "review-references")
        loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["review_id"], "PPR-" + report["report_id"])
        self.assertEqual(self.adapter.list_review_references(), [path])
        self.assertEqual(self.adapter.read_review_reference(loaded["review_id"]), loaded)

    def test_read_missing_reference_returns_none(self):
        self.assertIsNone(self.adapter.read_review_reference("PPR-does-not-exist"))


if __name__ == "__main__":
    unittest.main()

