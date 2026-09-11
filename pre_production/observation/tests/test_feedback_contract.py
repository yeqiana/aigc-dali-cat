#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisor Feedback contract tests.

Feedback is a human judgement of one advisor run: qualitative labels only, human
source only, bound to the exact advisor report revision, and it never edits the
advisor, the Story Lock or the production flow.
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.observation import feedback as fb  # noqa: E402
from pre_production.observation.schema import (  # noqa: E402
    AUTHORITY,
    CREATOR_DECISIONS,
    JUDGEMENT_SOURCE_HUMAN,
    RECOMMENDATION_RESULTS,
    validate_feedback,
)
from pre_production.tests.support import assert_no_scores  # noqa: E402


def sample_report(episode_id: str = "10-03", decision: str = "WARNING") -> dict:
    return {
        "schema": "advisor_report",
        "schema_version": 1,
        "report_id": "PPA-" + episode_id + "-deadbeef",
        "episode_id": episode_id,
        "story_id": episode_id,
        "title": "雾中的另一座生活区",
        "decision": decision,
        "risks": [],
        "evidence": ["SIM-1"],
        "recommendations": ["rework-anomaly"],
        "confidence": "MEDIUM",
        "source": {"story_lock_sha256": "a" * 64},
    }


def build(creator_decision="ACCEPT", recommendation_result="USEFUL", **extra):
    return fb.build_feedback(sample_report(), creator_decision=creator_decision,
                             recommendation_result=recommendation_result,
                             risk_acknowledged=True, **extra)


class AdvisorFeedbackContractTests(unittest.TestCase):
    def test_fresh_feedback_matches_contract(self):
        self.assertEqual(validate_feedback(build()), [])

    def test_enums_match_the_shadow_observation_spec(self):
        self.assertEqual(CREATOR_DECISIONS, ("ACCEPT", "REVISE", "IGNORE"))
        self.assertEqual(RECOMMENDATION_RESULTS, ("USEFUL", "PARTIAL", "NOT_USEFUL"))

    def test_every_enum_combination_is_valid(self):
        for decision in CREATOR_DECISIONS:
            for result in RECOMMENDATION_RESULTS:
                self.assertEqual(validate_feedback(build(decision, result)), [],
                                 decision + "/" + result)

    def test_unknown_creator_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            build(creator_decision="APPROVED")

    def test_unknown_recommendation_result_is_rejected(self):
        with self.assertRaises(ValueError):
            build(recommendation_result="63")

    def test_risk_acknowledged_must_be_boolean(self):
        with self.assertRaises(ValueError):
            fb.build_feedback(sample_report(), creator_decision="ACCEPT",
                              recommendation_result="USEFUL", risk_acknowledged="yes")

    def test_judgement_source_is_always_human(self):
        record = build()
        self.assertEqual(record["judgement_source"], JUDGEMENT_SOURCE_HUMAN)
        self.assertEqual(JUDGEMENT_SOURCE_HUMAN, "human")
        record["judgement_source"] = "model"
        self.assertTrue(validate_feedback(record))

    def test_feedback_is_advisory_only_and_never_blocks(self):
        record = build()
        self.assertTrue(record["advisory_only"])
        self.assertFalse(record["blocks_production"])
        self.assertEqual(record["authority"], AUTHORITY)

    def test_feedback_never_carries_a_score(self):
        assert_no_scores(self, build(), "advisor feedback")

    def test_feedback_binds_the_exact_report_revision(self):
        report = sample_report()
        record = fb.build_feedback(report, creator_decision="REVISE",
                                   recommendation_result="PARTIAL", risk_acknowledged=True)
        self.assertEqual(record["advisor_report_sha256"], fb.report_sha256(report))
        self.assertEqual(record["feedback_id"], "PFB-" + report["report_id"])
        self.assertEqual(record["episode_id"], "10-03")
        self.assertEqual(record["advisor_decision"], "WARNING")

    def test_building_feedback_never_edits_the_advisor_report(self):
        report = sample_report()
        before = copy.deepcopy(report)
        fb.build_feedback(report, creator_decision="IGNORE",
                          recommendation_result="NOT_USEFUL", risk_acknowledged=False)
        self.assertEqual(report, before)

    def test_missing_required_key_is_reported(self):
        record = build()
        del record["notes"]
        self.assertIn("advisor_feedback: missing required key 'notes'",
                      validate_feedback(record))

    def test_save_and_load_round_trip(self):
        import tempfile
        with tempfile.TemporaryDirectory(prefix="pp-fb-") as tmp:
            record = build()
            path = fb.save_feedback(record, store_dir=tmp)
            self.assertTrue(path.is_file())
            self.assertEqual(fb.load_feedback(path), record)
            self.assertEqual(fb.list_feedback(tmp), [path])


if __name__ == "__main__":
    unittest.main()
