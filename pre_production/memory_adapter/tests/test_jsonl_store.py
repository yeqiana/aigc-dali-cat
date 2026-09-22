#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONL Experience Store tests: append-only writes and tolerant reads.

These tests pin the storage behaviour only. They never assert a judgement about
a story, never expect a ranking and never expect a score.
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

from pre_production.memory_adapter import (  # noqa: E402
    JsonlExperienceStore,
    build_creator_decision_experience,
    build_experience_record,
    build_risk_pattern,
)
from pre_production.memory_adapter.experience_store_jsonl import (  # noqa: E402
    DECISION_FILE,
    EXPERIENCE_FILE,
    KIND_DECISION,
    KIND_EXPERIENCE,
    KIND_PATTERN,
    PATTERN_FILE,
    scan_jsonl,
)
from pre_production.tests.support import assert_no_scores  # noqa: E402


def experience_record(episode_id: str = "10-03", **overrides) -> dict:
    values = {
        "episode_id": episode_id,
        "story_dna_reference": "story_dna:10-03@2ed0c8c9",
        "advisor_report_reference": "advisor_report:PPA-10-03-4479f6cc",
        "observation_reference": "OBS-10-03-abcdef12",
        "feedback_reference": "PFB-PPA-10-03-4479f6cc",
    }
    values.update(overrides)
    return build_experience_record(**values)


def decision_record(episode_id: str = "10-03", **overrides) -> dict:
    values = {
        "episode_id": episode_id,
        "advisor_decision": "WARNING",
        "creator_action": "REVISE",
        "recommendation_result": "PARTIAL",
        "final_assessment": "改稿后重新评估",
        "feedback_reference": "PFB-PPA-10-03-4479f6cc",
    }
    values.update(overrides)
    return build_creator_decision_experience(**values)


def pattern_record(**overrides) -> dict:
    values = {
        "risk_type": "similarity",
        "pattern_description": "mountain_environment + fog_environment",
        "related_episode": ["10-02"],
        "evidence": ["SE-10-03-10-02"],
        "risk_level": "HIGH",
    }
    values.update(overrides)
    return build_risk_pattern(**values)


class _StoreCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="pp-exp-store-")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.store = JsonlExperienceStore(self.dir)

    def rows(self, path) -> list:
        return [line for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


class JsonlStoreLayoutTests(_StoreCase):
    def test_each_kind_maps_to_its_named_file(self):
        self.assertEqual(self.store.path_for(KIND_EXPERIENCE).name, EXPERIENCE_FILE)
        self.assertEqual(self.store.path_for(KIND_PATTERN).name, PATTERN_FILE)
        self.assertEqual(self.store.path_for(KIND_DECISION).name, DECISION_FILE)
        for name in (EXPERIENCE_FILE, PATTERN_FILE, DECISION_FILE):
            self.assertEqual(self.store.path_for(KIND_EXPERIENCE).parent, self.dir)

    def test_an_unknown_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.path_for("unknown-kind")

    def test_nothing_is_written_until_the_first_save(self):
        self.assertEqual(self.store.read(KIND_EXPERIENCE), [])
        self.assertEqual(list(self.dir.rglob("*")), [])


class JsonlAppendOnlyTests(_StoreCase):
    def test_save_reports_appended_with_id_and_path(self):
        record = experience_record()
        result = self.store.save_experience(record)
        self.assertEqual(result["status"], "APPENDED")
        self.assertEqual(result["id"], record["experience_id"])
        self.assertEqual(result["rows"], 1)
        self.assertEqual(Path(result["path"]), self.store.path_for(KIND_EXPERIENCE))

    def test_each_record_is_one_independent_json_object_per_line(self):
        first, second = experience_record(), experience_record("10-02")
        self.store.save_experience(first)
        self.store.save_experience(second)
        lines = self.rows(self.store.path_for(KIND_EXPERIENCE))
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["experience_id"], first["experience_id"])
        self.assertEqual(json.loads(lines[1])["experience_id"], second["experience_id"])

    def test_history_is_never_rewritten_or_reordered(self):
        self.store.save_experience(experience_record())
        path = self.store.path_for(KIND_EXPERIENCE)
        before = path.read_bytes()
        self.store.save_experience(experience_record("10-02"))
        after = path.read_bytes()
        self.assertTrue(after.startswith(before), "the earlier bytes must survive untouched")
        self.assertGreater(len(after), len(before))

    def test_a_duplicate_save_is_reused_and_not_appended(self):
        record = experience_record()
        self.store.save_experience(record)
        repeat = self.store.save_experience(dict(record))
        self.assertEqual(repeat["status"], "REUSED")
        self.assertEqual(repeat["id"], record["experience_id"])
        self.assertEqual(len(self.rows(self.store.path_for(KIND_EXPERIENCE))), 1)

    def test_a_changed_record_with_the_same_id_is_not_appended_again(self):
        record = experience_record(production_outcome="published")
        self.store.save_experience(record)
        repeat = self.store.save_experience(dict(record, production_outcome="archived"))
        self.assertEqual(repeat["status"], "REUSED")
        self.assertEqual(len(self.rows(self.store.path_for(KIND_EXPERIENCE))), 1)
        self.assertEqual(self.store.read(KIND_EXPERIENCE)[0]["production_outcome"], "published")

    def test_the_three_kinds_do_not_share_a_file(self):
        self.store.save_experience(experience_record())
        self.store.save_risk_pattern(pattern_record())
        self.store.save_creator_decision(decision_record())
        self.assertEqual(len(self.rows(self.store.path_for(KIND_EXPERIENCE))), 1)
        self.assertEqual(len(self.rows(self.store.path_for(KIND_PATTERN))), 1)
        self.assertEqual(len(self.rows(self.store.path_for(KIND_DECISION))), 1)

    def test_the_write_path_creates_the_store_directory(self):
        nested = self.dir / "a" / "b"
        store = JsonlExperienceStore(nested)
        store.save_experience(experience_record())
        self.assertTrue((nested / EXPERIENCE_FILE).is_file())


class JsonlValidationTests(_StoreCase):
    def test_a_record_missing_required_keys_is_rejected_before_any_write(self):
        with self.assertRaises(ValueError):
            self.store.save_experience({"schema": "experience_record"})
        self.assertFalse(self.store.path_for(KIND_EXPERIENCE).exists())

    def test_a_record_that_would_block_production_is_rejected(self):
        broken = dict(experience_record(), blocks_production=True)
        with self.assertRaises(ValueError):
            self.store.save_experience(broken)
        self.assertFalse(self.store.path_for(KIND_EXPERIENCE).exists())

    def test_a_record_with_a_score_like_key_is_rejected(self):
        broken = dict(experience_record(), similarity_score=87)
        with self.assertRaises(ValueError) as ctx:
            self.store.save_experience(broken)
        self.assertIn("score", str(ctx.exception))
        self.assertFalse(self.store.path_for(KIND_EXPERIENCE).exists())

    def test_an_unknown_risk_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.save_risk_pattern(pattern_record(risk_type="made_up"))
        self.assertFalse(self.store.path_for(KIND_PATTERN).exists())

    def test_an_unknown_creator_action_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.save_creator_decision(decision_record(creator_action="APPROVED"))
        self.assertFalse(self.store.path_for(KIND_DECISION).exists())

    def test_a_rejected_write_leaves_existing_history_byte_identical(self):
        self.store.save_experience(experience_record())
        path = self.store.path_for(KIND_EXPERIENCE)
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            self.store.save_experience({"schema": "experience_record"})
        self.assertEqual(path.read_bytes(), before)

    def test_stored_records_never_carry_score_like_keys(self):
        self.store.save_experience(experience_record())
        self.store.save_risk_pattern(pattern_record())
        self.store.save_creator_decision(decision_record())
        for kind in (KIND_EXPERIENCE, KIND_PATTERN, KIND_DECISION):
            for record in self.store.read(kind):
                assert_no_scores(self, record, kind + " record")


class JsonlReadToleranceTests(_StoreCase):
    def test_reading_a_missing_file_is_empty_and_never_raises(self):
        self.assertEqual(self.store.read(KIND_PATTERN), [])
        self.assertEqual(scan_jsonl(self.dir / "not-there.jsonl"), ([], []))

    def test_a_malformed_line_is_reported_not_raised(self):
        path = self.store.path_for(KIND_EXPERIENCE)
        good = experience_record()
        path.write_text("{not json\n" + json.dumps(good, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
        rows, malformed = scan_jsonl(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["experience_id"], good["experience_id"])
        self.assertEqual(len(malformed), 1)
        self.assertEqual(malformed[0]["line"], 1)
        self.assertEqual(self.store.read(KIND_EXPERIENCE), rows)

    def test_a_non_object_line_is_reported_not_raised(self):
        path = self.store.path_for(KIND_EXPERIENCE)
        path.write_text("[1, 2, 3]\n", encoding="utf-8", newline="\n")
        rows, malformed = scan_jsonl(path)
        self.assertEqual(rows, [])
        self.assertEqual(malformed[0]["error"], "not_an_object")

    def test_reads_keep_append_order(self):
        ids = []
        for index in range(4):
            record = experience_record("10-0" + str(index + 1))
            ids.append(self.store.save_experience(record)["id"])
        self.assertEqual([row["experience_id"] for row in self.store.read(KIND_EXPERIENCE)], ids)

    def test_summary_counts_real_rows_and_reports_malformed_lines(self):
        self.store.save_experience(experience_record())
        path = self.store.path_for(KIND_EXPERIENCE)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("{broken\n")
        summary = self.store.summarize()
        self.assertEqual(summary["counts"][KIND_EXPERIENCE], 1)
        self.assertEqual(summary["malformed"][KIND_EXPERIENCE], 1)
        self.assertEqual(summary["episodes"], 1)
        self.assertEqual(summary["authority"], "derived_non_authority")


if __name__ == "__main__":
    unittest.main()
