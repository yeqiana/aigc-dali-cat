#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EP003 observation regression: an existing advisor report becomes a record.

EP003 (雾中的另一座生活区) is the frozen WARNING case. The Shadow Observation phase
must be able to record its advisor run, keep it advisory only, and leave the
production state (episode-state / story-gates) byte-for-byte untouched.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.observation import feedback as fb  # noqa: E402
from pre_production.observation import ledger, observation  # noqa: E402
from pre_production.observation.schema import validate_observation_record  # noqa: E402
from pre_production.shadow_mode import analyze_episode  # noqa: E402
from pre_production.tests.support import assert_no_scores, find_ep003_dir  # noqa: E402

EP003 = find_ep003_dir()
PRODUCTION_FILES = ("episode-state.json", "story-gates.json")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(EP003 is not None, "EP003 archive not present in this checkout")
class Ep003ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzed = analyze_episode(EP003)
        cls.report = cls.analyzed["advisor_report"]
        cls.evidence = cls.analyzed["similarity_report"]["evidence"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-ep003-obs-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger_path = self.root / "observation-ledger.jsonl"
        self.store = self.root / "advisor-feedback"

    def test_existing_advisor_report_is_a_warning_with_evidence(self):
        self.assertEqual(self.report["decision"], "WARNING")
        self.assertTrue(self.evidence, "EP003 must still produce similarity evidence")

    def test_creates_an_observation_record_from_the_advisor_report(self):
        payload = observation.run_observation(EP003, ledger=self.ledger_path,
                                              feedback_store=self.store)
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertFalse(payload["blocks_production"])
        self.assertEqual(payload["advisor_decision"], "WARNING")
        self.assertEqual(payload["observation_status"], "FEEDBACK_PENDING")

        record = ledger.find_record(self.ledger_path, payload["observation_id"])
        self.assertEqual(validate_observation_record(record), [])
        self.assertEqual(record["episode_id"], "10-03")
        self.assertFalse(record["blocks_production"])
        assert_no_scores(self, record, "EP003 observation record")

    def test_human_feedback_closes_the_ep003_observation(self):
        saved = fb.save_feedback(fb.build_feedback(
            self.report, creator_decision="REVISE", recommendation_result="USEFUL",
            risk_acknowledged=True, revision_direction="重新设计异常机制"), store_dir=self.store)
        payload = observation.run_observation(EP003, ledger=self.ledger_path,
                                              feedback_store=self.store)
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertEqual(payload["observation_status"], "COMPLETED")
        record = ledger.find_record(self.ledger_path, payload["observation_id"])
        self.assertEqual(record["creator_feedback_reference"], str(saved.stem))
        assert_no_scores(self, record, "EP003 completed observation record")

    def test_observation_never_touches_production_state(self):
        before = {name: _digest(EP003 / "meta" / name)
                  for name in PRODUCTION_FILES if (EP003 / "meta" / name).is_file()}
        self.assertTrue(before, "EP003 meta state files must exist for this check")

        observation.run_observation(EP003, ledger=self.ledger_path, feedback_store=self.store)

        after = {name: _digest(EP003 / "meta" / name) for name in before}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
