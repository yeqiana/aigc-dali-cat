#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Experience Accumulation: read-only statistics tests.

The accumulation phase only counts what is already stored, so these tests pin
the two guarantees the read-only surface must never break: it changes no JSONL
byte, and it leaves every Runtime file untouched. They also pin the documented
Good Experience standard and prove the output carries no score-like key.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.cli import main as cli_main  # noqa: E402
from pre_production.memory_adapter import (  # noqa: E402
    QUALITY_STANDARD,
    REQUIRED_EXPERIENCE_FIELDS,
    JsonlExperienceStore,
    build_experience_record,
    collect_stats,
)
from pre_production.memory_adapter.tests.experience_fixture import (  # noqa: E402
    CREATOR_JUDGEMENTS,
    fixture_episodes,
    seed_store,
)
from pre_production.tests.support import assert_no_scores  # noqa: E402

RUNTIME_FILES = ("episode-state.json", "story-gates.json")
STORE_FILES = ("experience-records.jsonl", "risk-patterns.jsonl", "creator-decisions.jsonl")
DEFAULT_STORE_DIR = Path("reports") / "pre-production" / "experience-store"


def _digest(path) -> str:
    file_path = Path(path)
    if not file_path.is_file():
        return "missing"
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _snapshot(paths) -> dict:
    return {str(path): _digest(path) for path in paths}


def _runtime_snapshot() -> dict:
    snapshot: dict = {}
    for episode_dir in fixture_episodes().values():
        meta = Path(episode_dir) / "meta"
        snapshot[str(meta)] = ",".join(sorted(item.name for item in meta.iterdir())) if meta.is_dir() else "missing"
        for name in RUNTIME_FILES:
            snapshot[str(meta / name)] = _digest(meta / name)
    return snapshot


class _StatsCase(unittest.TestCase):
    """Shared temp store / feedback / ledger so nothing lands in the checkout."""

    def setUp(self):
        if not fixture_episodes():
            self.skipTest("no fixture episode in this checkout")
        self._tmp = tempfile.TemporaryDirectory(prefix="pp-stats-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.store_dir = self.tmp / "store"
        self.feedback_dir = self.tmp / "feedback"
        self.ledger = self.tmp / "ledger.jsonl"
        self.store = JsonlExperienceStore(self.store_dir)

    def run_cli(self, *argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli_main(list(argv))
        return code, buffer.getvalue()

    def stats_argv(self, *extra):
        return ("experience", "stats", "--store", str(self.store_dir),
                "--feedback-store", str(self.feedback_dir),
                "--ledger", str(self.ledger)) + tuple(extra)

    def stats(self, **kwargs):
        return collect_stats(self.store, feedback_dir=self.feedback_dir,
                             ledger_path=self.ledger, **kwargs)

    def store_files(self) -> list:
        return sorted(self.store_dir.glob("*.jsonl")) if self.store_dir.is_dir() else []


class EmptyStoreTests(_StatsCase):
    def test_empty_store_reports_zeros_and_writes_nothing(self):
        payload = self.stats()
        self.assertEqual(payload["counts"], {"experience": 0, "pattern": 0, "decision": 0})
        self.assertEqual(payload["quality"]["complete"], 0)
        self.assertEqual(payload["quality"]["incomplete"], 0)
        self.assertEqual(payload["episodes"]["with_experience"], [])
        self.assertEqual(payload["malformed"],
                         {"experience": 0, "pattern": 0, "decision": 0})
        for labels in payload["distribution"].values():
            self.assertEqual(labels, {})
        self.assertFalse(self.store_dir.exists(), "stats must not create the store dir")

    def test_missing_store_directory_is_not_an_error(self):
        code, out = self.run_cli(*self.stats_argv())
        self.assertEqual(code, 0)
        self.assertIn("experience=0", out)
        self.assertIn("read-only", out)

    def test_documented_precondition_is_reported_as_note_not_verdict(self):
        payload = self.stats()
        precondition = payload["pattern_learning_precondition"]
        self.assertIn("30-50", precondition["documented"])
        self.assertEqual(precondition["complete_experiences"], 0)
        self.assertIs(payload["blocks_production"], False)
        self.assertIs(payload["advisory_only"], True)
        self.assertEqual(payload["authority"], "derived_non_authority")


class ReadOnlyTests(_StatsCase):
    def test_stats_keeps_every_jsonl_byte_identical(self):
        seed_store(self.store)
        files = self.store_files() + sorted(self.feedback_dir.glob("*.json")) \
            + [self.ledger]
        before = _snapshot(files)
        self.assertTrue(before, "fixture must have produced stored records")

        code, out = self.run_cli(*self.stats_argv())
        self.assertEqual(code, 0)
        self.assertIn("read-only", out)

        self.assertEqual(before, _snapshot(files))
        self.assertEqual(files, self.store_files() + sorted(self.feedback_dir.glob("*.json"))
                         + [self.ledger])

    def test_stats_never_touches_runtime_files(self):
        before = _runtime_snapshot()
        seed_store(self.store)
        self.run_cli(*self.stats_argv())
        self.assertEqual(before, _runtime_snapshot())

    def test_stats_does_not_touch_the_real_default_store(self):
        default_dir = REPO_ROOT / DEFAULT_STORE_DIR
        before = sorted(item.name for item in default_dir.iterdir()) if default_dir.is_dir() else None
        code, _ = self.run_cli(*self.stats_argv())
        self.assertEqual(code, 0)
        after = sorted(item.name for item in default_dir.iterdir()) if default_dir.is_dir() else None
        self.assertEqual(before, after)

    def test_plain_output_contains_no_rate_or_score_language(self):
        seed_store(self.store)
        _, out = self.run_cli(*self.stats_argv())
        lowered = out.lower()
        for token in ("score", "percent", "%", "hit rate", "adoption rate", "grade"):
            self.assertNotIn(token, lowered)


class AccumulationStatsTests(_StatsCase):
    def test_quality_standard_matches_the_documented_four_facts(self):
        self.assertEqual(REQUIRED_EXPERIENCE_FIELDS,
                         ("story_dna_reference", "advisor_report_reference",
                          "feedback_reference", "production_outcome"))
        self.assertEqual(QUALITY_STANDARD,
                         "story_dna + advisor_report + human_feedback + production_outcome")

    def test_incomplete_experience_is_reported_by_missing_field(self):
        seeded = seed_store(self.store)
        payload = self.stats()
        self.assertEqual(payload["counts"]["experience"], len(seeded))
        self.assertEqual(payload["quality"]["complete"], 0)
        self.assertEqual(payload["quality"]["missing_by_field"],
                         {"production_outcome": len(seeded)})
        self.assertEqual(payload["quality"]["complete_episodes"], [])

    def test_complete_experience_needs_all_four_references(self):
        seed_store(self.store)
        record = build_experience_record(
            episode_id="10-03",
            story_dna_reference="story_dna:10-03@abcd1234",
            advisor_report_reference="advisor_report:PPA-10-03-deadbeef",
            observation_reference="OBS-10-03-deadbeef",
            feedback_reference="PFB-PPA-10-03-manual",
            production_outcome="revised then archived",
        )
        self.store.save_experience(record)
        payload = self.stats()
        self.assertEqual(payload["quality"]["complete"], 1)
        self.assertEqual(payload["quality"]["complete_episodes"], ["10-03"])
        self.assertIn("10-03", payload["episodes"]["with_experience"])

    def test_distribution_reports_label_counts_only(self):
        seeded = seed_store(self.store)
        payload = self.stats()
        distribution = payload["distribution"]
        expected = {
            "advisor_decision": dict(Counter(item["decision"] for item in seeded.values())),
            "creator_action": dict(Counter(CREATOR_JUDGEMENTS[label]["creator_decision"]
                                           for label in seeded)),
            "recommendation_result": dict(Counter(CREATOR_JUDGEMENTS[label]["recommendation_result"]
                                                  for label in seeded)),
        }
        for key, value in expected.items():
            self.assertEqual(distribution[key], value, key)
        self.assertEqual(set(distribution["risk_type"]), {"similarity"})
        self.assertEqual(sum(distribution["risk_level"].values()),
                         payload["counts"]["pattern"])
        self.assertEqual(sorted(payload["episodes"]["with_decision"]),
                         sorted(payload["episodes"]["with_experience"]))

    def test_episode_coverage_lists_real_episode_ids(self):
        seeded = seed_store(self.store)
        payload = self.stats()
        self.assertEqual(payload["episodes"]["with_experience"],
                         sorted(item["episode_id"] for item in seeded.values()))

    def test_json_output_is_parseable_and_carries_no_score_key(self):
        seed_store(self.store)
        code, out = self.run_cli(*self.stats_argv("--json"))
        self.assertEqual(code, 0)
        payload = json.loads(out)
        assert_no_scores(self, payload, "experience stats payload")
        self.assertEqual(payload["authority"], "derived_non_authority")
        self.assertIs(payload["blocks_production"], False)

    def test_stats_reads_feedback_and_ledger_without_writing_them(self):
        seed_store(self.store)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text("", encoding="utf-8")
        before = _snapshot([self.ledger])
        code, out = self.run_cli(*self.stats_argv())
        self.assertEqual(code, 0)
        self.assertIn("feedback    : files=0", out)
        self.assertEqual(before, _snapshot([self.ledger]))


if __name__ == "__main__":
    unittest.main()
