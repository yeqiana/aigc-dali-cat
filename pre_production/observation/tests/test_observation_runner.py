#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Observation Runner tests.

The runner records one advisor run and syncs its lifecycle. Its hard promise is
failure isolation: it never raises and never returns anything that blocks
production, so an advisor/observation problem can never break the flow.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.observation import feedback as fb  # noqa: E402
from pre_production.observation import ledger, observation  # noqa: E402
from pre_production.tests.support import assert_no_scores  # noqa: E402


def sample_report(episode_id: str = "10-03") -> dict:
    return {
        "schema": "advisor_report",
        "schema_version": 1,
        "report_id": "PPA-" + episode_id + "-deadbeef",
        "episode_id": episode_id,
        "story_id": episode_id,
        "title": "雾中的另一座生活区",
        "decision": "WARNING",
        "risks": [],
        "evidence": [],
        "recommendations": [],
        "confidence": "MEDIUM",
        "source": {"story_lock_sha256": "a" * 64},
    }


class ObservationRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-runner-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger_path = self.root / "observation-ledger.jsonl"
        self.store = self.root / "advisor-feedback"

    def test_records_one_observation_and_waits_for_feedback(self):
        payload = observation.run_observation(advisor_report=sample_report(),
                                              ledger=self.ledger_path, feedback_store=self.store)
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertEqual(payload["observation_status"], "FEEDBACK_PENDING")
        self.assertEqual(payload["advisor_decision"], "WARNING")
        self.assertFalse(payload["blocks_production"])
        self.assertTrue(payload["advisory_only"])
        self.assertEqual(len(ledger.read_records(self.ledger_path)), 1)
        assert_no_scores(self, payload, "runner payload")

    def test_rerunning_is_idempotent(self):
        for _ in range(2):
            observation.run_observation(advisor_report=sample_report(),
                                        ledger=self.ledger_path, feedback_store=self.store)
        self.assertEqual(len(ledger.read_records(self.ledger_path)), 1)
        self.assertEqual(len(ledger.scan_ledger(self.ledger_path)[0]), 2)

    def test_completes_the_observation_when_feedback_exists(self):
        report = sample_report()
        saved = fb.save_feedback(fb.build_feedback(report, creator_decision="ACCEPT",
                                                   recommendation_result="USEFUL",
                                                   risk_acknowledged=True), store_dir=self.store)
        payload = observation.run_observation(advisor_report=report, ledger=self.ledger_path,
                                              feedback_store=self.store, production_outcome="shipped")
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertEqual(payload["observation_status"], "COMPLETED")
        record = ledger.find_record(self.ledger_path, payload["observation_id"])
        self.assertEqual(record["creator_feedback_reference"], str(saved.stem))
        self.assertEqual(record["production_outcome"], "shipped")

    def test_apply_feedback_closes_the_matching_observation(self):
        report = sample_report()
        observation.run_observation(advisor_report=report, ledger=self.ledger_path,
                                    feedback_store=self.store)
        record = fb.build_feedback(report, creator_decision="REVISE",
                                   recommendation_result="PARTIAL", risk_acknowledged=True)
        payload = observation.apply_feedback(record, ledger=self.ledger_path)
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertEqual(payload["observation_status"], "COMPLETED")
        self.assertFalse(payload["blocks_production"])

    def test_dry_run_writes_nothing(self):
        payload = observation.run_observation(advisor_report=sample_report(),
                                              ledger=self.ledger_path, dry_run=True)
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertFalse(self.ledger_path.exists())

    def test_never_raises_on_a_missing_episode(self):
        payload = observation.run_observation(self.root / "missing-episode",
                                              ledger=self.ledger_path)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["blocks_production"])
        self.assertTrue(payload["advisory_only"])
        self.assertTrue(payload["errors"])
        self.assertFalse(self.ledger_path.exists())

    def test_requires_a_report_or_an_episode(self):
        payload = observation.run_observation(ledger=self.ledger_path)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["blocks_production"])


if __name__ == "__main__":
    unittest.main()
