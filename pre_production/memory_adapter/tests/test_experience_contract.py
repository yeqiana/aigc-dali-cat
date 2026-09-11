#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Experience Store contract tests.

The three entities must satisfy their contracts, stay advisory only, never
carry a score and never touch the advisor or the production state.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.memory_adapter import experience_schema as schema  # noqa: E402
from pre_production.memory_adapter import experience_store as store  # noqa: E402
from pre_production.tests.support import assert_no_scores  # noqa: E402


def sample_experience(**overrides) -> dict:
    kwargs = dict(
        episode_id="10-03",
        story_dna_reference="story_dna:10-03@deadbeef",
        advisor_report_reference="advisor_report:PPA-10-03-deadbeef",
        observation_reference="OBS-10-03-deadbeef",
        feedback_reference="PFB-PPA-10-03-deadbeef",
        production_outcome="published",
        audience_feedback={"platform": "douyin", "notes": "真实数据见 Phase 9.6.1"},
    )
    kwargs.update(overrides)
    return store.build_experience_record(**kwargs)


def sample_pattern(**overrides) -> dict:
    kwargs = dict(
        risk_type="similarity",
        pattern_description="mountain_environment + fog_anomaly + isolated_location",
        related_episode=["10-01", "10-02"],
        evidence=["SIM-10-03-0001"],
    )
    kwargs.update(overrides)
    return store.build_risk_pattern(**kwargs)


def sample_decision(**overrides) -> dict:
    kwargs = dict(
        episode_id="10-03",
        advisor_decision="WARNING",
        creator_action="REVISE",
        recommendation_result="USEFUL",
        final_assessment="按建议重做异常机制后与历史篇目差异明显",
        feedback_reference="PFB-PPA-10-03-deadbeef",
    )
    kwargs.update(overrides)
    return store.build_creator_decision_experience(**kwargs)


class ExperienceRecordContractTests(unittest.TestCase):
    def test_fresh_record_matches_contract(self):
        record = sample_experience()
        self.assertEqual(schema.validate_experience_record(record), [])

    def test_required_fields_are_present(self):
        record = sample_experience()
        for field in ("episode_id", "story_dna_reference", "advisor_report_reference",
                      "observation_reference", "feedback_reference", "production_outcome",
                      "audience_feedback"):
            self.assertIn(field, record)

    def test_record_kind_and_ids_are_stable(self):
        first = sample_experience()
        second = sample_experience()
        self.assertEqual(first["record_kind"], "episode_experience")
        self.assertEqual(first["experience_id"], second["experience_id"])
        self.assertTrue(first["experience_id"].startswith("EXP-10-03-"))

    def test_references_may_be_pending_but_keys_stay(self):
        record = sample_experience(observation_reference=None, feedback_reference=None,
                                   production_outcome=None, audience_feedback=None)
        self.assertEqual(schema.validate_experience_record(record), [])

    def test_missing_required_field_is_reported(self):
        record = sample_experience()
        del record["production_outcome"]
        self.assertIn("experience_record: missing required key 'production_outcome'",
                      schema.validate_experience_record(record))

    def test_record_is_advisory_only_and_never_blocks(self):
        record = sample_experience()
        self.assertTrue(record["advisory_only"])
        self.assertFalse(record["blocks_production"])
        self.assertEqual(record["authority"], "derived_non_authority")
        self.assertEqual(schema.AUTHORITY, "derived_non_authority")

    def test_record_never_carries_a_score(self):
        assert_no_scores(self, sample_experience(), "experience_record")

    def test_score_like_key_is_rejected(self):
        record = sample_experience()
        record["similarity_score"] = 0.87
        self.assertTrue(schema.validate_experience_record(record))


class RiskPatternContractTests(unittest.TestCase):
    def test_fresh_pattern_matches_contract(self):
        self.assertEqual(schema.validate_risk_pattern(sample_pattern()), [])

    def test_pattern_describes_tokens_not_a_rule(self):
        record = sample_pattern(risk_level="HIGH")
        self.assertEqual(record["pattern_description"],
                         "mountain_environment + fog_anomaly + isolated_location")
        self.assertEqual(record["risk_type"], "similarity")
        self.assertEqual(record["related_episode"], ["10-01", "10-02"])
        self.assertEqual(record["evidence"], ["SIM-10-03-0001"])
        self.assertTrue(record["pattern_id"].startswith("PAT-similarity-"))

    def test_pattern_without_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            sample_pattern(evidence=[])

    def test_pattern_without_episode_is_rejected(self):
        with self.assertRaises(ValueError):
            sample_pattern(related_episode=[])

    def test_unknown_risk_type_is_rejected(self):
        with self.assertRaises(ValueError):
            sample_pattern(risk_type="vibe")

    def test_pattern_has_no_score_or_threshold(self):
        record = sample_pattern(risk_level="MEDIUM")
        assert_no_scores(self, record, "risk_pattern")
        record["threshold"] = 0.8
        self.assertTrue(schema.validate_risk_pattern(record))


class CreatorDecisionContractTests(unittest.TestCase):
    def test_fresh_decision_matches_contract(self):
        self.assertEqual(schema.validate_creator_decision_experience(sample_decision()), [])

    def test_every_enum_combination_is_valid(self):
        for action in schema.CREATOR_ACTIONS:
            for result in schema.RECOMMENDATION_RESULTS:
                for decision in schema.ADVISOR_DECISIONS:
                    record = sample_decision(creator_action=action, recommendation_result=result,
                                             advisor_decision=decision)
                    self.assertEqual(schema.validate_creator_decision_experience(record), [])

    def test_enum_vocabularies_match_the_feedback_model(self):
        self.assertEqual(schema.CREATOR_ACTIONS, ("ACCEPT", "REVISE", "IGNORE"))
        self.assertEqual(schema.RECOMMENDATION_RESULTS, ("USEFUL", "PARTIAL", "NOT_USEFUL"))
        self.assertEqual(schema.ADVISOR_DECISIONS, ("PASS", "WARNING", "NEEDS_REVISION"))

    def test_unknown_creator_action_is_rejected(self):
        with self.assertRaises(ValueError):
            sample_decision(creator_action="APPROVED")

    def test_final_assessment_is_free_text(self):
        record = sample_decision(final_assessment="")
        self.assertEqual(schema.validate_creator_decision_experience(record), [])
        self.assertIsInstance(record["final_assessment"], str)

    def test_decision_never_carries_a_score(self):
        assert_no_scores(self, sample_decision(), "creator_decision_experience")


if __name__ == "__main__":
    unittest.main()
