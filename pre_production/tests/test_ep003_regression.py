#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EP003 regression: the archived risk case must be reported as WARNING.

EP003 (雾中的另一座生活区) is the frozen risk case from the design docs: a
mountain/fog anomaly whose space expression sits close to earlier episodes.
The advisor must surface it as WARNING with real similarity evidence, and must
never fabricate a score. The test skips (not fails) when the archive is absent
so it stays honest about what it actually verified.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.shadow_mode import analyze_episode, write_artifacts  # noqa: E402
from pre_production.story_dna.validator import (  # noqa: E402
    validate_advisor_report,
    validate_dna,
    validate_similarity_report,
)
from pre_production.tests.support import assert_no_scores, find_ep003_dir  # noqa: E402

EP003 = find_ep003_dir()


@unittest.skipUnless(EP003 is not None, "EP003 archive not present in this checkout")
class Ep003RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze_episode(EP003)
        cls.report = cls.result["advisor_report"]
        cls.evidence = cls.result["similarity_report"]["evidence"]

    def test_decision_is_warning(self):
        self.assertEqual(self.report["decision"], "WARNING")

    def test_similarity_evidence_exists(self):
        self.assertTrue(self.evidence, "EP003 must produce similarity evidence")
        for item in self.evidence:
            self.assertTrue(item["related_episode_id"])
            self.assertIn(item["risk_level"], ["LOW", "MEDIUM", "HIGH"])

    def test_evidence_points_at_real_historical_sources(self):
        for item in self.evidence:
            self.assertTrue(item["explanation"])
            if item.get("related_source_path"):
                self.assertTrue((REPO_ROOT / item["related_source_path"]).is_file(),
                                item["related_source_path"])

    def test_report_passes_every_contract(self):
        for group in self.result["issues"].values():
            self.assertEqual(group, [])
        self.assertEqual(validate_advisor_report(self.report), [])

    def test_report_never_contains_a_score(self):
        assert_no_scores(self, self.report, "EP003 advisor_report")
        assert_no_scores(self, self.result["similarity_report"], "EP003 similarity_report")
        assert_no_scores(self, self.result["dna"], "EP003 story_dna")

    def test_at_least_one_risk_carries_evidence(self):
        self.assertTrue(self.report["risks"])
        self.assertTrue(all(risk["evidence"] for risk in self.report["risks"]))

    def test_generated_artifacts_validate_after_round_trip(self):
        with tempfile.TemporaryDirectory(prefix="pp-ep003-") as tmp:
            written = write_artifacts(self.result, tmp)
            self.assertEqual(len(written), 3)
            dna = yaml.safe_load((Path(tmp) / "story_fingerprint.yaml").read_text(encoding="utf-8"))
            similarity = yaml.safe_load((Path(tmp) / "similarity_report.yaml").read_text(encoding="utf-8"))
            advisor = yaml.safe_load((Path(tmp) / "advisor_report.yaml").read_text(encoding="utf-8"))
            self.assertEqual(validate_dna(dna), [])
            self.assertEqual(validate_similarity_report(similarity), [])
            self.assertEqual(validate_advisor_report(advisor), [])
            self.assertEqual(advisor["decision"], "WARNING")


if __name__ == "__main__":
    unittest.main()

