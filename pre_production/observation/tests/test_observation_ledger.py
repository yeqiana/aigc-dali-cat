#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode Observation Ledger schema and lifecycle tests.

The ledger is derived experience, never authority: it must satisfy its contract,
stay forward-only, never carry a score and never touch episode state.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.observation import ledger  # noqa: E402
from pre_production.observation.schema import (  # noqa: E402
    AUTHORITY,
    OBSERVATION_STATUSES,
    validate_observation_record,
)
from pre_production.tests.support import assert_no_scores  # noqa: E402

REQUIRED_FIELDS = (
    "episode_id",
    "story_dna_reference",
    "advisor_report_reference",
    "observation_status",
    "creator_feedback_reference",
    "production_outcome",
    "learning_summary",
)


def sample_observation(episode_id: str = "10-03", status: str = "OBSERVED") -> dict:
    return ledger.build_observation(
        episode_id,
        story_dna_reference="story_dna:10-03@deadbeef",
        advisor_report_reference="advisor_report:PPA-10-03-deadbeef",
        observation_status=status,
    )


class ObservationLedgerSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-obs-ledger-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger_path = self.root / "observation-ledger.jsonl"

    def test_fresh_record_matches_contract(self):
        record = sample_observation()
        self.assertEqual(validate_observation_record(record), [])

    def test_all_required_fields_present(self):
        record = sample_observation()
        for field in REQUIRED_FIELDS:
            self.assertIn(field, record)

    def test_default_status_is_observed(self):
        self.assertEqual(sample_observation()["observation_status"], "OBSERVED")
        self.assertEqual(OBSERVATION_STATUSES, ("OBSERVED", "FEEDBACK_PENDING", "COMPLETED"))

    def test_record_is_advisory_only_and_never_blocks(self):
        record = sample_observation()
        self.assertTrue(record["advisory_only"])
        self.assertFalse(record["blocks_production"])
        self.assertEqual(record["authority"], AUTHORITY)
        self.assertEqual(AUTHORITY, "derived_non_authority")

    def test_record_never_carries_a_score(self):
        assert_no_scores(self, sample_observation(), "observation record")

    def test_missing_required_field_is_reported(self):
        record = sample_observation()
        del record["learning_summary"]
        self.assertIn("episode_observation: missing required key 'learning_summary'",
                      validate_observation_record(record))

    def test_unknown_status_is_reported(self):
        record = sample_observation()
        record["observation_status"] = "ARCHIVED"
        self.assertTrue(validate_observation_record(record))

    def test_observation_id_is_stable_per_report_revision(self):
        first = ledger.observation_id("10-03", "advisor_report:PPA-10-03-deadbeef")
        second = ledger.observation_id("10-03", "advisor_report:PPA-10-03-deadbeef")
        other = ledger.observation_id("10-03", "advisor_report:PPA-10-03-cafebabe")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertTrue(first.startswith("OBS-10-03-"))


class ObservationLedgerLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pp-obs-ledger-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger_path = self.root / "observation-ledger.jsonl"

    def _append(self, **kwargs):
        record = sample_observation(**kwargs)
        return record, ledger.append_record(self.ledger_path, record)

    def test_first_append_writes_one_row(self):
        record, outcome = self._append()
        self.assertEqual(outcome["status"], "APPENDED")
        self.assertEqual(outcome["rows"], 1)
        self.assertEqual(ledger.find_record(self.ledger_path, record["observation_id"]), record)

    def test_repeating_an_identical_snapshot_is_reused(self):
        record = sample_observation()
        ledger.append_record(self.ledger_path, record)
        outcome = ledger.append_record(self.ledger_path, ledger.build_observation(
            "10-03", story_dna_reference="story_dna:10-03@deadbeef",
            advisor_report_reference="advisor_report:PPA-10-03-deadbeef"))
        self.assertEqual(outcome["status"], "REUSED")
        self.assertEqual(len(ledger.scan_ledger(self.ledger_path)[0]), 1)

    def test_lifecycle_moves_forward_only(self):
        record = sample_observation()
        ledger.append_record(self.ledger_path, record)
        oid = record["observation_id"]

        ledger.mark_feedback_pending(self.ledger_path, oid)
        self.assertEqual(ledger.find_record(self.ledger_path, oid)["observation_status"],
                         "FEEDBACK_PENDING")

        ledger.complete_observation(self.ledger_path, oid,
                                    creator_feedback_reference="PFB-PPA-10-03-deadbeef",
                                    production_outcome="shipped",
                                    learning_summary="advisory matched reality")
        closed = ledger.find_record(self.ledger_path, oid)
        self.assertEqual(closed["observation_status"], "COMPLETED")
        self.assertEqual(closed["creator_feedback_reference"], "PFB-PPA-10-03-deadbeef")
        self.assertEqual(closed["production_outcome"], "shipped")
        # A lifecycle move is a new snapshot: history stays readable.
        self.assertEqual(len(ledger.scan_ledger(self.ledger_path)[0]), 3)

    def test_transition_backwards_is_rejected(self):
        record = sample_observation()
        ledger.append_record(self.ledger_path, record)
        oid = record["observation_id"]
        ledger.complete_observation(self.ledger_path, oid)
        with self.assertRaises(ValueError):
            ledger.transition(self.ledger_path, oid, "OBSERVED")

    def test_transition_on_unknown_observation_is_rejected(self):
        with self.assertRaises(ValueError):
            ledger.transition(self.ledger_path, "OBS-missing", "FEEDBACK_PENDING")

    def test_unknown_target_status_is_rejected(self):
        record = sample_observation()
        ledger.append_record(self.ledger_path, record)
        with self.assertRaises(ValueError):
            ledger.transition(self.ledger_path, record["observation_id"], "ARCHIVED")

    def test_latest_snapshot_wins_per_observation(self):
        record = sample_observation()
        ledger.append_record(self.ledger_path, record)
        ledger.mark_feedback_pending(self.ledger_path, record["observation_id"])
        records = ledger.read_records(self.ledger_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["observation_status"], "FEEDBACK_PENDING")

    def test_malformed_line_is_reported_but_never_raises(self):
        good = sample_observation()
        self.ledger_path.write_text(
            json.dumps(good, ensure_ascii=False) + "\n" + "{ not json \n" + "[1,2,3]\n",
            encoding="utf-8")
        rows, malformed = ledger.scan_ledger(self.ledger_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual([item["line"] for item in malformed], [2, 3])

    def test_summarize_uses_real_counts(self):
        first = sample_observation("10-03")
        ledger.append_record(self.ledger_path, first)
        ledger.complete_observation(self.ledger_path, first["observation_id"],
                                    creator_feedback_reference="PFB-1")
        second = ledger.build_observation("10-04",
                                          advisor_report_reference="advisor_report:PPA-10-04-x")
        ledger.append_record(self.ledger_path, second)
        summary = ledger.summarize(ledger.read_records(self.ledger_path))
        self.assertEqual(summary["observations"], 2)
        self.assertEqual(summary["episodes"], 2)
        self.assertEqual(summary["with_feedback"], 1)
        self.assertEqual(summary["by_status"], {"COMPLETED": 1, "OBSERVED": 1})
        self.assertEqual(summary["authority"], AUTHORITY)
        assert_no_scores(self, summary, "ledger summary")

    def test_ledger_never_touches_episode_state_or_gates(self):
        record = sample_observation()
        ledger.append_record(self.ledger_path, record)
        ledger.complete_observation(self.ledger_path, record["observation_id"])
        names = {path.name for path in self.root.rglob("*")}
        self.assertNotIn("episode-state.json", names)
        self.assertNotIn("story-gates.json", names)
        self.assertEqual(names, {"observation-ledger.jsonl"})


if __name__ == "__main__":
    unittest.main()
