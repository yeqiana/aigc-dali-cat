#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Experience Store read path tests, including the EP001/EP002/EP003 fixture.

The read path returns candidates only: no ranking, no similarity, no score.
The fixture seeds the store from the real episodes in this checkout, so it
verifies the write and the read path together and skips what is absent.
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

from pre_production.memory_adapter import (  # noqa: E402
    DECISION_FILE,
    EXPERIENCE_FILE,
    KIND_DECISION,
    KIND_EXPERIENCE,
    KIND_PATTERN,
    PATTERN_FILE,
    JsonlExperienceStore,
    build_experience_record,
    build_risk_pattern,
)
from pre_production.memory_adapter.tests import experience_fixture as fixture  # noqa: E402
from pre_production.tests.support import assert_no_scores  # noqa: E402

EPISODES = ("10-01", "10-02", "10-03")
RESULT_KEYS_THAT_WOULD_IMPLY_A_JUDGEMENT = ("rank", "ranking", "similarity",
                                            "weight", "priority", "order")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _ReadCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="pp-exp-read-")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.store = JsonlExperienceStore(self.dir)
        self.ids = {}
        for episode_id in EPISODES:
            record = build_experience_record(
                episode_id=episode_id,
                story_dna_reference="story_dna:" + episode_id + "@abcd1234",
                advisor_report_reference="advisor_report:PPA-" + episode_id + "-deadbeef",
                observation_reference="OBS-" + episode_id + "-abcdef12",
                feedback_reference="PFB-PPA-" + episode_id + "-deadbeef",
            )
            self.ids[episode_id] = self.store.save_experience(record)["id"]

    def assert_no_judgement_keys(self, records) -> None:
        for record in records:
            for key in record:
                self.assertNotIn(str(key).lower(), RESULT_KEYS_THAT_WOULD_IMPLY_A_JUDGEMENT,
                                 key)
            assert_no_scores(self, record, "read result")


class ExperienceReadPathTests(_ReadCase):
    def test_query_without_filters_returns_every_candidate_in_append_order(self):
        found = self.store.get_related_experience()
        self.assertEqual([row["episode_id"] for row in found], list(EPISODES))
        self.assertEqual(found, self.store.read(KIND_EXPERIENCE))

    def test_query_by_episode_id_returns_that_episode(self):
        found = self.store.get_related_experience(episode_id="10-02")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["episode_id"], "10-02")
        self.assertEqual(found[0]["experience_id"], self.ids["10-02"])

    def test_an_unknown_episode_id_returns_nothing(self):
        self.assertEqual(self.store.get_related_experience(episode_id="99-99"), [])

    def test_query_by_story_dna_reference_string(self):
        found = self.store.get_related_experience(story_dna="story_dna:10-03@abcd1234")
        self.assertEqual([row["episode_id"] for row in found], ["10-03"])

    def test_query_by_story_dna_mapping_builds_the_same_reference(self):
        dna = {"story_id": "10-02", "source": {"story_lock_sha256": "abcd1234" + "0" * 56}}
        found = self.store.get_related_experience(story_dna=dna)
        self.assertEqual([row["episode_id"] for row in found], ["10-02"])

    def test_episode_and_story_dna_filters_combine(self):
        found = self.store.get_related_experience(episode_id="10-01",
                                                  story_dna="story_dna:10-02@abcd1234")
        self.assertEqual(found, [])

    def test_limit_returns_the_first_candidates_without_reordering(self):
        everything = self.store.get_related_experience()
        limited = self.store.get_related_experience(limit=2)
        self.assertEqual(limited, everything[:2])
        self.assertEqual(self.store.get_related_experience(limit=0), [])
        self.assertEqual(self.store.get_related_experience(limit=99), everything)

    def test_read_results_carry_no_ranking_or_score_field(self):
        self.assert_no_judgement_keys(self.store.get_related_experience())

    def test_read_results_are_the_stored_records_untouched(self):
        stored = self.store.read(KIND_EXPERIENCE)
        found = self.store.get_related_experience()
        self.assertEqual(found, stored)
        self.assertEqual(self.store.read(KIND_EXPERIENCE), stored)


class PatternQueryTests(_ReadCase):
    def setUp(self):
        super().setUp()
        self.patterns = {
            "mountain_fog": build_risk_pattern(
                risk_type="similarity",
                pattern_description="mountain_environment + fog_environment + isolated_location",
                related_episode=["10-02"], evidence=["SE-10-03-10-02"], risk_level="HIGH"),
            "room_lamp": build_risk_pattern(
                risk_type="similarity",
                pattern_description="lodging_room + lamp_light_motif",
                related_episode=["01_不存在的夜行路"], evidence=["SE-10-01-01"], risk_level="MEDIUM"),
            "hook": build_risk_pattern(
                risk_type="hook",
                pattern_description="passive_observation",
                related_episode=["10-01"], evidence=["SE-10-01-hook"], risk_level="LOW"),
        }
        for record in self.patterns.values():
            self.store.save_risk_pattern(record)

    def test_query_without_filters_returns_every_pattern_in_append_order(self):
        found = self.store.query_pattern()
        self.assertEqual([row["pattern_id"] for row in found],
                         [record["pattern_id"] for record in self.patterns.values()])

    def test_query_filters_by_risk_type(self):
        found = self.store.query_pattern(risk_type="hook")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["pattern_id"], self.patterns["hook"]["pattern_id"])

    def test_a_token_matches_a_plain_substring(self):
        found = self.store.query_pattern(tokens=["fog_environment"])
        self.assertEqual([row["pattern_id"] for row in found],
                         [self.patterns["mountain_fog"]["pattern_id"]])

    def test_every_token_must_match(self):
        self.assertTrue(self.store.query_pattern(tokens=["mountain_environment", "fog_environment"]))
        self.assertEqual(self.store.query_pattern(
            tokens=["mountain_environment", "lamp_light_motif"]), [])

    def test_token_matching_is_case_insensitive(self):
        found = self.store.query_pattern(tokens=["FOG_ENVIRONMENT"])
        self.assertEqual([row["pattern_id"] for row in found],
                         [self.patterns["mountain_fog"]["pattern_id"]])

    def test_a_token_can_match_a_related_episode(self):
        found = self.store.query_pattern(tokens=["10-02"])
        self.assertEqual([row["pattern_id"] for row in found],
                         [self.patterns["mountain_fog"]["pattern_id"]])

    def test_an_unknown_token_returns_nothing(self):
        self.assertEqual(self.store.query_pattern(tokens=["not_a_real_token"]), [])

    def test_risk_type_and_token_filters_combine(self):
        self.assertEqual(self.store.query_pattern(risk_type="hook",
                                                  tokens=["fog_environment"]), [])

    def test_limit_keeps_the_first_candidates(self):
        everything = self.store.query_pattern()
        self.assertEqual(self.store.query_pattern(limit=1), everything[:1])

    def test_pattern_results_carry_no_ranking_or_score_field(self):
        self.assert_no_judgement_keys(self.store.query_pattern())


class ExperienceStoreFixtureTests(unittest.TestCase):
    """EP001 / EP002 / EP003 initialisation through the real walk of the advisor."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="pp-exp-fixture-")
        cls.dir = Path(cls._tmp.name)
        cls.store = JsonlExperienceStore(cls.dir)
        cls.episodes = fixture.fixture_episodes()
        cls.seeded = fixture.seed_store(cls.store)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_fixture_found_at_least_one_real_episode(self):
        self.assertTrue(self.episodes, "no fixture episode is present in this checkout")
        self.assertEqual(set(self.seeded), set(self.episodes))

    def test_each_fixture_episode_wrote_one_experience_and_one_decision(self):
        self.assertEqual(len(self.store.read(KIND_EXPERIENCE)), len(self.seeded))
        self.assertEqual(len(self.store.read(KIND_DECISION)), len(self.seeded))
        for label, data in self.seeded.items():
            self.assertEqual(data["ingest"]["experience_status"], "APPENDED", label)
            self.assertEqual(data["ingest"]["decision_status"], "APPENDED", label)

    def test_each_fixture_experience_keeps_the_reference_chain(self):
        for label, data in self.seeded.items():
            found = self.store.get_related_experience(episode_id=data["episode_id"])
            self.assertEqual(len(found), 1, label)
            record = found[0]
            self.assertEqual(record["observation_reference"],
                             data["observation"]["observation_id"], label)
            self.assertEqual(record["feedback_reference"], data["feedback"]["feedback_id"], label)
            self.assertEqual(record["advisor_report_reference"],
                             data["ingest"]["advisor_report_reference"], label)
            self.assertTrue(record["story_dna_reference"].startswith("story_dna:"), label)
            self.assertFalse(record["blocks_production"], label)
            self.assertTrue(record["advisory_only"], label)

    def test_each_fixture_episode_reads_back_by_its_story_dna_reference(self):
        for label, data in self.seeded.items():
            reference = data["ingest"]["experience_id"] and data["observation"]["story_dna_reference"]
            found = self.store.get_related_experience(story_dna=reference)
            self.assertTrue(any(row["episode_id"] == data["episode_id"] for row in found), label)

    def test_the_fixture_only_created_the_three_store_files(self):
        names = sorted(path.name for path in self.dir.rglob("*") if path.is_file())
        self.assertEqual(names, sorted([EXPERIENCE_FILE, PATTERN_FILE, DECISION_FILE]))

    def test_fixture_records_never_carry_score_like_keys(self):
        for kind in (KIND_EXPERIENCE, KIND_PATTERN, KIND_DECISION):
            for record in self.store.read(kind):
                assert_no_scores(self, record, kind + " fixture record")

    def test_ep003_can_be_written_and_read(self):
        if "EP003" not in self.seeded:
            self.skipTest("EP003 archive not present in this checkout")
        data = self.seeded["EP003"]
        self.assertEqual(data["episode_id"], "10-03")
        self.assertEqual(data["decision"], "WARNING")
        self.assertTrue(data["evidence"], "EP003 must keep its similarity evidence")
        found = self.store.get_related_experience(episode_id="10-03")
        self.assertEqual(len(found), 1)
        decision = [row for row in self.store.read(KIND_DECISION)
                    if row["episode_id"] == "10-03"]
        self.assertEqual(len(decision), 1)
        self.assertEqual(decision[0]["advisor_decision"], "WARNING")
        self.assertEqual(decision[0]["creator_action"], "REVISE")
        patterns = self.store.query_pattern(risk_type="similarity", tokens=["fog"])
        self.assertTrue(patterns, "EP003 should leave a readable fog-related pattern")

    def test_seeding_the_store_never_touches_production_state(self):
        # The blast radius check: the episodes the store read must keep an
        # identical episode-state.json and story-gates.json byte for byte.
        tracked = [episode_dir / relative
                   for episode_dir in self.episodes.values()
                   for relative in ("meta/episode-state.json", "meta/story-gates.json")
                   if (episode_dir / relative).is_file()]
        if not tracked:
            self.skipTest("no episode level production state file to compare")
        before = {str(path): sha256_file(path) for path in tracked}
        with tempfile.TemporaryDirectory(prefix="pp-exp-state-") as tmp:
            fixture.seed_store(JsonlExperienceStore(Path(tmp)))
        after = {str(path): sha256_file(path) for path in tracked}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
