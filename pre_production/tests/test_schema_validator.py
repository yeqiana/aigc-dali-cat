#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests: schema + validator behaviour for every artifact type."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.story_dna.schema import (  # noqa: E402
    DIMENSIONS,
    empty_dna,
    load_contract,
    missing_subfields,
)
from pre_production.story_dna.validator import (  # noqa: E402
    require_valid,
    validate_advisor_report,
    validate_dna,
    validate_review_reference,
    validate_similarity_evidence,
    validate_similarity_report,
)
from pre_production.similarity_analysis.evidence import build_evidence  # noqa: E402

REQUIRED_DIMENSIONS = ["setting", "relationship", "character", "anomaly",
                       "emotion", "narrative", "visual_pattern"]


def sample_evidence(**overrides) -> dict:
    payload = dict(
        current_story_id="CUR-01",
        related_episode_id="HIS-01",
        related_title="历史故事",
        risk_level="MEDIUM",
        matched_dimensions=["anomaly"],
        matched_features=["spatial_overlap_anomaly"],
        explanation="命中同一异常机制。",
    )
    payload.update(overrides)
    return build_evidence(**payload)


class ContractFileTests(unittest.TestCase):
    def test_required_dimensions_are_declared(self):
        for dim in REQUIRED_DIMENSIONS:
            self.assertIn(dim, DIMENSIONS, "story dna must declare dimension " + dim)

    def test_story_dna_contract_declares_policy_and_forbidden_keys(self):
        contract = load_contract("story_dna.schema.json")
        self.assertTrue(contract["policy"]["scoring"])
        self.assertTrue(contract["forbidden_key_patterns"])
        self.assertIn("score", contract["forbidden_key_patterns"])

    def test_similarity_contract_declares_three_levels_only(self):
        contract = load_contract("similarity_evidence.schema.json")
        self.assertEqual(sorted(contract["risk_levels"]), ["HIGH", "LOW", "MEDIUM"])
        self.assertTrue(contract["policy"]["no_numeric_similarity"])

    def test_advisor_contract_declares_three_decisions(self):
        contract = load_contract("advisor_report.schema.json")
        self.assertEqual(contract["decisions"], ["PASS", "WARNING", "NEEDS_REVISION"])
        self.assertTrue(contract["risk_required"])


class StoryDnaValidatorTests(unittest.TestCase):
    def test_empty_dna_is_valid(self):
        self.assertEqual(validate_dna(empty_dna("X-01", "标题")), [])

    def test_missing_subfield_is_reported(self):
        dna = empty_dna("X-01")
        del dna["setting"]["location"]
        self.assertIn("setting.location", missing_subfields(dna))
        self.assertTrue(any("setting.location" in issue for issue in validate_dna(dna)))

    def test_missing_required_top_level_is_reported(self):
        dna = empty_dna("X-01")
        del dna["anomaly"]
        self.assertTrue(any("'anomaly'" in issue for issue in validate_dna(dna)))

    def test_forbidden_score_key_is_rejected(self):
        dna = empty_dna("X-01")
        dna["similarity_score"] = 87
        issues = validate_dna(dna)
        self.assertTrue(any("forbidden key" in issue for issue in issues))

    def test_non_string_list_item_is_rejected(self):
        dna = empty_dna("X-01")
        dna["emotion"]["primary_emotion"] = [1]
        self.assertTrue(any("must be strings" in issue for issue in validate_dna(dna)))

    def test_non_mapping_root_is_rejected(self):
        self.assertEqual(validate_dna(["not", "a", "mapping"]),
                         ["story_dna: root must be a mapping"])


class SimilarityValidatorTests(unittest.TestCase):
    def test_well_formed_evidence_is_valid(self):
        self.assertEqual(validate_similarity_evidence(sample_evidence()), [])

    def test_bad_risk_level_is_rejected(self):
        bad = sample_evidence(risk_level="CRITICAL")
        self.assertTrue(any("risk_level" in issue for issue in validate_similarity_evidence(bad)))

    def test_high_risk_without_features_is_rejected(self):
        bad = sample_evidence(risk_level="HIGH", matched_features=[], explanation="")
        issues = validate_similarity_evidence(bad)
        self.assertTrue(any("HIGH risk requires" in issue for issue in issues))

    def test_forbidden_similarity_score_key_is_rejected(self):
        bad = sample_evidence()
        bad["similarity_score"] = 0.87
        self.assertTrue(any("forbidden" in issue for issue in validate_similarity_evidence(bad)))

    def test_report_wrapper_requires_evidence_list(self):
        self.assertTrue(validate_similarity_report({"current_story_id": "X"}))
        report = {"current_story_id": "X", "evidence": [sample_evidence()]}
        self.assertEqual(validate_similarity_report(report), [])


class AdvisorAndReviewValidatorTests(unittest.TestCase):
    def _report(self):
        return {
            "report_id": "PPA-X-0001",
            "episode_id": "X-01",
            "decision": "WARNING",
            "risks": [{"type": "similarity", "level": "MEDIUM", "evidence": [sample_evidence()]}],
            "evidence": ["SE-X-HIS"],
            "recommendations": ["increase_mechanism_differentiation"],
            "confidence": "MEDIUM",
            "created_time": "2026-09-11T00:00:00+08:00",
        }

    def test_well_formed_report_is_valid(self):
        self.assertEqual(validate_advisor_report(self._report()), [])

    def test_unknown_decision_is_rejected(self):
        report = self._report()
        report["decision"] = "REJECT"
        self.assertTrue(any("decision" in issue for issue in validate_advisor_report(report)))

    def test_missing_required_key_is_rejected(self):
        report = self._report()
        del report["confidence"]
        self.assertTrue(any("confidence" in issue for issue in validate_advisor_report(report)))

    def test_risk_without_evidence_is_rejected(self):
        report = self._report()
        report["risks"][0]["evidence"] = []
        self.assertTrue(any("must carry evidence" in issue for issue in validate_advisor_report(report)))

    def test_review_reference_decision_values(self):
        good = {
            "review_id": "PPR-1", "advisor_report_id": "PPA-X-0001", "episode_id": "X-01",
            "creator_decision": "pending", "final_result": "", "feedback": "",
            "created_time": "2026-09-11T00:00:00+08:00",
        }
        self.assertEqual(validate_review_reference(good), [])
        bad = dict(good, creator_decision="approved")
        self.assertTrue(any("creator_decision" in issue for issue in validate_review_reference(bad)))

    def test_require_valid_raises_on_issues(self):
        require_valid([], "noop")
        with self.assertRaises(ValueError):
            require_valid(["boom"], "demo")


if __name__ == "__main__":
    unittest.main()

