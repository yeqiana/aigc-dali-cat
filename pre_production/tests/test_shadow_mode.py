#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Mode integration tests: report-only, never blocks production."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.shadow_mode import analyze_episode, run_shadow, write_artifacts  # noqa: E402
from pre_production.story_dna.validator import (  # noqa: E402
    validate_advisor_report,
    validate_dna,
    validate_similarity_report,
)
from pre_production.tests.support import assert_no_scores  # noqa: E402

CURRENT_LOCK = """# 《当前测试故事》Story Lock

> 系列：10
> 集数：03

## 一、一句话故事

主角在城市公寓里记录普通生活。

## 二、异常机制

局部重叠：两个有人正常生活的现实空间发生局部重叠。

## 三、反同质化

本集避免重复，声明机制不同。
"""

HISTORY_LOCK = """# 《历史测试故事》Story Lock

> 系列：10
> 集数：01

## 一、一句话故事

主角在城市公寓里记录普通生活。

## 二、异常机制

局部重叠：两个有人正常生活的现实空间发生局部重叠。
"""

INJECTED_HISTORY = [{
    "story_id": "10-01", "title": "历史测试故事",
    "setting": {"location": ["urban_area"], "environment": [], "time_period": [],
                "social_context": []},
    "anomaly": {"anomaly_type": ["spatial_overlap_anomaly"], "anomaly_mechanism": [],
                "anomaly_visibility": [], "escalation_pattern": []},
}]


class ShadowModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-shadow-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.ep = root / "ep"
        (self.ep / "docs").mkdir(parents=True)
        (self.ep / "docs" / "02_current_StoryLock.md").write_text(CURRENT_LOCK, encoding="utf-8")
        self.hist = root / "hist"
        (self.hist / "docs").mkdir(parents=True)
        (self.hist / "docs" / "02_history_StoryLock.md").write_text(HISTORY_LOCK, encoding="utf-8")
        self.out = root / "out"

    def test_analyze_episode_end_to_end_with_injected_history(self):
        result = analyze_episode(self.ep, repo_root=REPO_ROOT, history=list(INJECTED_HISTORY))
        self.assertEqual(result["dna"]["story_id"], "10-03")
        self.assertEqual(result["advisor_report"]["decision"], "WARNING")
        self.assertTrue(result["similarity_report"]["evidence"])
        for group in result["issues"].values():
            self.assertEqual(group, [])

    def test_write_artifacts_produces_three_valid_yaml_files(self):
        result = analyze_episode(self.ep, repo_root=REPO_ROOT, history=[])
        written = write_artifacts(result, self.out)
        self.assertEqual(sorted(written), ["advisor_report.yaml", "similarity_report.yaml",
                                           "story_fingerprint.yaml"])
        dna = yaml.safe_load((self.out / "story_fingerprint.yaml").read_text(encoding="utf-8"))
        similarity = yaml.safe_load((self.out / "similarity_report.yaml").read_text(encoding="utf-8"))
        advisor = yaml.safe_load((self.out / "advisor_report.yaml").read_text(encoding="utf-8"))
        self.assertEqual(validate_dna(dna), [])
        self.assertEqual(validate_similarity_report(similarity), [])
        self.assertEqual(validate_advisor_report(advisor), [])
        for payload in (dna, similarity, advisor):
            assert_no_scores(self, payload, "artifact")

    def test_shadow_run_writes_artifacts_and_review_reference(self):
        payload = run_shadow(self.ep, out_dir=self.out, repo_root=REPO_ROOT,
                             history_paths=(self.hist,), history_limit=1,
                             memory_store=Path(self.tmp.name) / "memory")
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertFalse(payload["blocks_production"])
        self.assertTrue(payload["advisory_only"])
        self.assertEqual(payload["decision"], "WARNING")
        self.assertEqual(sorted(payload["artifacts"]), ["advisor_report.yaml",
                                                        "similarity_report.yaml",
                                                        "story_fingerprint.yaml"])
        self.assertTrue(payload["review_reference"])
        self.assertTrue(Path(payload["review_reference"]).is_file())

    def test_shadow_run_dry_run_writes_nothing(self):
        payload = run_shadow(self.ep, out_dir=self.out, repo_root=REPO_ROOT,
                             history_paths=(self.hist,), history_limit=1, dry_run=True)
        self.assertTrue(payload["ok"], payload.get("errors"))
        self.assertEqual(payload["artifacts"], {})
        self.assertFalse(self.out.exists())

    def test_shadow_run_never_raises_on_bad_input(self):
        payload = run_shadow(Path(self.tmp.name) / "missing-episode")
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["blocks_production"])
        self.assertTrue(payload["errors"])

    def test_shadow_run_returns_unknown_decision_when_it_cannot_analyze(self):
        empty = Path(self.tmp.name) / "ep-without-lock"
        empty.mkdir()
        payload = run_shadow(empty)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["decision"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
