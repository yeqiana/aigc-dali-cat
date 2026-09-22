#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Human Feedback Entry tests (CLI).

The human entrance is a command line action: record one advisor run, then write
what the creator decided. It is always manual and never blocks production.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.cli import main  # noqa: E402
from pre_production.observation import ledger  # noqa: E402

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


def _run(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(argv)
    return code, buffer.getvalue()


class HumanFeedbackEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-human-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ep = self.root / "ep"
        (self.ep / "docs").mkdir(parents=True)
        (self.ep / "docs" / "02_current_StoryLock.md").write_text(CURRENT_LOCK, encoding="utf-8")
        self.hist = self.root / "hist"
        (self.hist / "docs").mkdir(parents=True)
        (self.hist / "docs" / "02_history_StoryLock.md").write_text(HISTORY_LOCK, encoding="utf-8")
        self.out = self.root / "out"
        self.ledger_path = self.root / "observation-ledger.jsonl"
        self.store = self.root / "advisor-feedback"
        self.report = self._prepare_report()

    def _prepare_report(self) -> Path:
        code, output = _run(["analyze", str(self.ep), "--out-dir", str(self.out),
                             "--repo-root", str(self.root), "--history", str(self.hist),
                             "--limit", "1"])
        self.assertEqual(code, 0, output)
        report_path = self.out / "advisor_report.yaml"
        self.assertTrue(report_path.is_file())
        return report_path

    def test_record_creates_one_observation_waiting_for_feedback(self):
        code, output = _run(["observe", "record", "--report", str(self.report),
                             "--ledger", str(self.ledger_path), "--feedback-store", str(self.store)])
        self.assertEqual(code, 0, output)
        self.assertIn("advisory only; blocks_production = False", output)
        records = ledger.read_records(self.ledger_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["observation_status"], "FEEDBACK_PENDING")
        self.assertEqual(records[0]["episode_id"], "10-03")
        self.assertTrue(records[0]["advisor_report_reference"].startswith("advisor_report:"))
        self.assertTrue(records[0]["story_dna_reference"].startswith("story_dna:"))

    def test_record_dry_run_writes_nothing(self):
        code, output = _run(["observe", "record", "--report", str(self.report),
                             "--ledger", str(self.ledger_path), "--dry-run"])
        self.assertEqual(code, 0, output)
        self.assertFalse(self.ledger_path.exists())

    def test_record_never_crashes_on_bad_input(self):
        missing = self.root / "missing-episode"
        code, output = _run(["observe", "record", str(missing),
                             "--ledger", str(self.ledger_path)])
        self.assertEqual(code, 1)
        self.assertIn("advisory only; blocks_production = False", output)
        self.assertIn("error", output.lower())
        self.assertFalse(self.ledger_path.exists())

    def test_feedback_entry_records_the_human_judgement(self):
        _run(["observe", "record", "--report", str(self.report),
              "--ledger", str(self.ledger_path), "--feedback-store", str(self.store)])
        code, output = _run([
            "observe", "feedback", "--report", str(self.report),
            "--creator-decision", "REVISE", "--recommendation-result", "USEFUL",
            "--risk-acknowledged", "yes",
            "--revision-direction", "重新设计异常机制",
            "--final-effect", "改后与历史篇目差异明显",
            "--notes", "风险成立但建议需要更具体",
            "--store", str(self.store), "--ledger", str(self.ledger_path)])
        self.assertEqual(code, 0, output)
        written = sorted(self.store.glob("*.json"))
        self.assertEqual(len(written), 1)
        payload = json.loads(written[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["creator_decision"], "REVISE")
        self.assertEqual(payload["recommendation_result"], "USEFUL")
        self.assertTrue(payload["risk_acknowledged"])
        self.assertEqual(payload["judgement_source"], "human")
        self.assertFalse(payload["blocks_production"])

        observation = ledger.find_record(self.ledger_path, ledger.observation_id(
            payload["episode_id"], "advisor_report:" + payload["advisor_report_id"]))
        self.assertEqual(observation["observation_status"], "COMPLETED")
        self.assertEqual(observation["creator_feedback_reference"], payload["feedback_id"])

    def test_feedback_dry_run_writes_nothing(self):
        code, output = _run([
            "observe", "feedback", "--report", str(self.report),
            "--creator-decision", "ACCEPT", "--recommendation-result", "PARTIAL",
            "--risk-acknowledged", "no", "--store", str(self.store),
            "--ledger", str(self.ledger_path), "--dry-run"])
        self.assertEqual(code, 0, output)
        self.assertIn("dry-run", output)
        self.assertFalse(self.store.exists())
        self.assertFalse(self.ledger_path.exists())

    def test_feedback_requires_a_loadable_report(self):
        code, output = _run([
            "observe", "feedback", "--report", str(self.root / "nope.yaml"),
            "--creator-decision", "ACCEPT", "--recommendation-result", "USEFUL",
            "--risk-acknowledged", "yes"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR", output)

    def test_list_reports_the_ledger_state(self):
        _run(["observe", "record", "--report", str(self.report),
              "--ledger", str(self.ledger_path), "--feedback-store", str(self.store)])
        code, output = _run(["observe", "list", "--ledger", str(self.ledger_path), "--json"])
        self.assertEqual(code, 0, output)
        payload = json.loads(output)
        self.assertEqual(payload["summary"]["observations"], 1)
        self.assertEqual(payload["records"][0]["observation_status"], "FEEDBACK_PENDING")


if __name__ == "__main__":
    unittest.main()
