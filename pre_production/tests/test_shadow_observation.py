#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Observation tests: observation ledger + human advisor feedback.

These tests prove the layer is additive and manual: it records experience,
never scores, never mutates production state and never blocks the flow.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production import cli  # noqa: E402
from pre_production.advisor import (  # noqa: E402
    assess_similarity_risks,
    build_recommendations,
    build_report,
)
from pre_production.shadow_mode import analyze_episode, write_artifacts  # noqa: E402
from pre_production.shadow_observation.feedback import (  # noqa: E402
    build_feedback,
    load_feedback,
    report_sha256,
    save_feedback,
    unknown_evidence_refs,
)
from pre_production.shadow_observation.ledger import (  # noqa: E402
    AUTHORITY,
    append_entry,
    build_entry,
    highest_risk_level,
    scan_ledger,
    summarize,
)
from pre_production.similarity_analysis.evidence import build_evidence  # noqa: E402
from pre_production.story_dna.validator import (  # noqa: E402
    validate_advisor_feedback,
    validate_observation_entry,
)
from pre_production.tests.support import (  # noqa: E402
    assert_no_scores,
    build_dna,
    find_ep003_dir,
)

CURRENT_LOCK = """# 《当前测试故事》Story Lock

> 系列：10
> 集数：03

## 一、一句话故事

主角在城市公寓里记录普通生活。

## 二、异常机制

局部重叠：两个有人正常生活的现实空间发生局部重叠。
"""

HISTORY_LOCK = """# 《历史测试故事》Story Lock

> 系列：10
> 集数：01

## 一、一句话故事

主角在城市公寓里记录普通生活。

## 二、异常机制

局部重叠：两个有人正常生活的现实空间发生局部重叠。
"""

STORY_LOCK_SHA = "a" * 64


def sample_report(*, level: str = "MEDIUM", episode_id: str = "CUR-01",
                  story_lock_sha: str = STORY_LOCK_SHA) -> dict:
    """An advisor report whose DNA carries a real Story Lock SHA."""
    dna = build_dna(episode_id, "当前故事")
    dna["source"] = {"story_lock_path": "docs/02_current_StoryLock.md",
                     "story_lock_sha256": story_lock_sha, "rule_version": "RULE_V1"}
    evidence = [build_evidence(
        current_story_id=episode_id, related_episode_id="HIS-01", related_title="历史测试故事",
        risk_level=level, matched_dimensions=["anomaly"],
        matched_features=["spatial_overlap_anomaly"],
        explanation="命中同一异常机制，属于结构性相似提示。")]
    risks = assess_similarity_risks(evidence)
    return build_report(episode_id=episode_id, dna=dna, evidence=evidence, risks=risks,
                        recommendations=build_recommendations(risks, dna), history_size=3,
                        created_at="2026-09-11T00:00:00+08:00")


class HighestRiskLevelTests(unittest.TestCase):
    def test_empty_is_none(self):
        self.assertEqual(highest_risk_level([]), "NONE")

    def test_picks_the_highest_present_level(self):
        risks = [{"level": "LOW"}, {"level": "HIGH"}, {"level": "MEDIUM"}]
        self.assertEqual(highest_risk_level(risks), "HIGH")

    def test_ignores_unknown_levels(self):
        self.assertEqual(highest_risk_level([{"level": "?"}, {"level": "LOW"}]), "LOW")


class ObservationLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-observe-")
        self.addCleanup(self.tmp.cleanup)
        self.ledger = Path(self.tmp.name) / "observation-ledger.jsonl"
        self.report = sample_report(level="MEDIUM")

    def test_build_entry_is_valid_and_non_authority(self):
        entry = build_entry(self.report)
        self.assertEqual(validate_observation_entry(entry), [])
        self.assertEqual(entry["authority"], AUTHORITY)
        self.assertEqual(entry["run_mode"], "shadow")
        self.assertEqual(entry["decision"], "WARNING")
        self.assertEqual(entry["highest_risk_level"], "MEDIUM")
        self.assertTrue(entry["advisory_only"])
        self.assertFalse(entry["blocks_production"])
        self.assertFalse(entry["mutates_episode_state"])
        self.assertFalse(entry["mutates_story_gates"])
        self.assertIsNone(entry["feedback_id"])
        self.assertTrue(entry["observation_id"].startswith("OB-CUR-01-"))

    def test_entry_has_no_score_like_keys(self):
        assert_no_scores(self, build_entry(self.report), "observation entry")

    def test_append_then_reuse_for_the_same_story_lock(self):
        entry = build_entry(self.report)
        first = append_entry(self.ledger, entry)
        self.assertEqual(first["status"], "APPENDED")
        second = append_entry(self.ledger, entry)
        self.assertEqual(second["status"], "REUSED")
        self.assertEqual(second["total_entries"], 1)
        self.assertEqual(len(self.ledger.read_text(encoding="utf-8").splitlines()), 1)

    def test_new_story_lock_revision_appends_a_new_row(self):
        append_entry(self.ledger, build_entry(sample_report(story_lock_sha="a" * 64)))
        outcome = append_entry(self.ledger, build_entry(sample_report(story_lock_sha="b" * 64)))
        self.assertEqual(outcome["status"], "APPENDED")
        self.assertEqual(outcome["total_entries"], 2)

    def test_entry_that_claims_to_block_production_is_rejected(self):
        entry = build_entry(self.report)
        entry["blocks_production"] = True
        with self.assertRaises(ValueError):
            append_entry(self.ledger, entry)
        self.assertFalse(self.ledger.exists(), "invalid entry must not be written")

    def test_scan_reports_malformed_lines_without_raising(self):
        self.ledger.write_text(
            json.dumps(build_entry(self.report), ensure_ascii=False) + "\n" + "{not json}\n",
            encoding="utf-8")
        entries, malformed = scan_ledger(self.ledger)
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(malformed), 1)
        self.assertEqual(malformed[0]["line"], 2)

    def test_scan_missing_ledger_is_empty(self):
        self.assertEqual(scan_ledger(self.ledger), ([], []))

    def test_summarize_counts_real_values(self):
        append_entry(self.ledger, build_entry(sample_report(story_lock_sha="a" * 64)))
        append_entry(self.ledger, build_entry(sample_report(story_lock_sha="b" * 64,
                                                      level="HIGH")))
        summary = summarize(scan_ledger(self.ledger)[0])
        self.assertEqual(summary["observations"], 2)
        self.assertEqual(summary["episodes"], 1)
        self.assertEqual(summary["by_decision"], {"WARNING": 1, "NEEDS_REVISION": 1})
        self.assertEqual(summary["by_highest_risk_level"]["HIGH"], 1)
        self.assertEqual(summary["authority"], AUTHORITY)


class AdvisorFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-feedback-")
        self.addCleanup(self.tmp.cleanup)
        self.report = sample_report()

    def test_build_feedback_is_human_and_valid(self):
        feedback = build_feedback(self.report, creator_decision="accepted",
                                  advisor_accuracy="partially_correct",
                                  confirmed_evidence=["SE-CUR-01-HIS-01"], notes="先改机制")
        self.assertEqual(validate_advisor_feedback(feedback), [])
        self.assertEqual(feedback["judgement_source"], "human")
        self.assertEqual(feedback["creator_decision"], "accepted")
        self.assertEqual(feedback["advisor_accuracy"], "partially_correct")
        self.assertEqual(feedback["feedback_id"], "PFB-" + self.report["report_id"])

    def test_feedback_binds_the_exact_report_revision(self):
        feedback = build_feedback(self.report)
        self.assertEqual(feedback["advisor_report_sha256"], report_sha256(self.report))
        changed = dict(self.report)
        changed["decision"] = "PASS"
        self.assertNotEqual(report_sha256(changed), feedback["advisor_report_sha256"])

    def test_feedback_has_no_score_like_keys(self):
        assert_no_scores(self, build_feedback(self.report), "advisor feedback")

    def test_invalid_accuracy_label_is_rejected(self):
        feedback = build_feedback(self.report, advisor_accuracy="87")
        self.assertTrue(validate_advisor_feedback(feedback))

    def test_save_and_load_round_trip(self):
        store = Path(self.tmp.name) / "feedback"
        feedback = build_feedback(self.report, creator_decision="revised")
        path = save_feedback(feedback, store_dir=store)
        self.assertTrue(path.is_file())
        self.assertEqual(path.parent, store)
        self.assertEqual(load_feedback(path), feedback)

    def test_unknown_evidence_refs_flags_undeclared_ids(self):
        feedback = build_feedback(self.report, confirmed_evidence=["SE-CUR-01-HIS-01"],
                                  refuted_evidence=["SE-NOPE-9"])
        self.assertEqual(unknown_evidence_refs(feedback, self.report), ["SE-NOPE-9"])

    def test_known_evidence_refs_produce_no_warning(self):
        feedback = build_feedback(self.report, confirmed_evidence=["SE-CUR-01-HIS-01"])
        self.assertEqual(unknown_evidence_refs(feedback, self.report), [])


class ObserveCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-observe-cli-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ep = self.root / "ep"
        (self.ep / "docs").mkdir(parents=True)
        (self.ep / "docs" / "02_current_StoryLock.md").write_text(CURRENT_LOCK, encoding="utf-8")
        self.hist = self.root / "hist"
        (self.hist / "docs").mkdir(parents=True)
        (self.hist / "docs" / "02_history_StoryLock.md").write_text(HISTORY_LOCK, encoding="utf-8")
        self.ledger = self.root / "observation-ledger.jsonl"
        self.out = self.root / "artifacts"

    def _record_args(self, *extra):
        return ["observe", "record", str(self.ep), "--ledger", str(self.ledger),
                "--repo-root", str(self.root), "--history", str(self.hist), "--limit", "1", *extra]

    def test_observe_record_dry_run_writes_nothing(self):
        self.assertEqual(cli.main(self._record_args("--dry-run")), 0)
        self.assertFalse(self.ledger.exists())

    def test_observe_record_appends_then_reuses(self):
        self.assertEqual(cli.main(self._record_args()), 0)
        self.assertEqual(len(self.ledger.read_text(encoding="utf-8").splitlines()), 1)
        self.assertEqual(cli.main(self._record_args()), 0)
        self.assertEqual(len(self.ledger.read_text(encoding="utf-8").splitlines()), 1)

    def test_observe_list_json_reports_summary(self):
        cli.main(self._record_args())
        self.assertEqual(cli.main(["observe", "list", "--ledger", str(self.ledger), "--json"]), 0)

    def test_observe_feedback_writes_a_human_record(self):
        analyzed = analyze_episode(self.ep, repo_root=self.root, history_paths=(self.hist,),
                                   history_limit=1)
        write_artifacts(analyzed, self.out)
        store = self.root / "feedback"
        rc = cli.main(["observe", "feedback", "--report", str(self.out / "advisor_report.yaml"),
                       "--store", str(store), "--decision", "accepted", "--accuracy", "correct",
                       "--confirmed", "SE-unknown-but-allowed"])
        self.assertEqual(rc, 0)
        written = list(store.glob("*.json"))
        self.assertEqual(len(written), 1)
        record = json.loads(written[0].read_text(encoding="utf-8"))
        self.assertEqual(record["judgement_source"], "human")
        self.assertEqual(record["creator_decision"], "accepted")

    def test_observe_feedback_dry_run_writes_nothing(self):
        analyzed = analyze_episode(self.ep, repo_root=self.root, history_paths=(self.hist,),
                                   history_limit=1)
        write_artifacts(analyzed, self.out)
        store = self.root / "feedback"
        rc = cli.main(["observe", "feedback", "--report", str(self.out / "advisor_report.yaml"),
                       "--store", str(store), "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertFalse(store.exists())


class ShadowObservationEp003Tests(unittest.TestCase):
    def test_ep003_observation_is_warning_with_evidence(self):
        ep003 = find_ep003_dir()
        if ep003 is None:
            self.skipTest("archived EP003 episode is unavailable")
        analyzed = analyze_episode(ep003, repo_root=REPO_ROOT)
        entry = build_entry(analyzed["advisor_report"],
                            similarity_report=analyzed["similarity_report"])
        self.assertEqual(validate_observation_entry(entry), [])
        self.assertEqual(entry["decision"], "WARNING")
        self.assertTrue(analyzed["similarity_report"]["evidence"],
                        "WARNING must be backed by similarity evidence")
        self.assertGreater(entry["evidence_count"], 0)
        assert_no_scores(self, entry, "ep003 observation entry")


if __name__ == "__main__":
    unittest.main()
