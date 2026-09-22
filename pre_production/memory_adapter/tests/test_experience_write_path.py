#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feedback -> Experience Store write path tests.

Covers the phase link "Advisor Feedback -> Creator Decision Experience +
Episode Experience": references are preserved, the advisor report is never
copied, and a rejected ingest leaves the store untouched.
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
    KIND_DECISION,
    KIND_EXPERIENCE,
    KIND_PATTERN,
    JsonlExperienceStore,
    build_experience_record,
    decision_experience_from_feedback,
    experience_from_feedback,
    ingest_feedback,
    pattern_from_evidence,
)
from pre_production.memory_adapter.experience_schema import (  # noqa: E402
    DECISION_EXPERIENCE_CONTRACT,
    EXPERIENCE_CONTRACT,
)
from pre_production.observation import build_feedback  # noqa: E402
from pre_production.story_dna.schema import load_contract  # noqa: E402
from pre_production.tests.support import assert_no_scores  # noqa: E402

REPORT_MARKER = "EXPLANATION_MARKER_THAT_MUST_NOT_BE_COPIED"
OBSERVATION_ID = "OBS-10-03-abcdef12"
DNA_REFERENCE = "story_dna:10-03@2ed0c8c9"


def advisor_report(report_id: str = "PPA-10-03-deadbeef", episode_id: str = "10-03",
                   decision: str = "WARNING") -> dict:
    """A synthetic advisor report; the write path must keep only its references."""
    return {
        "schema": "advisor_report",
        "schema_version": 1,
        "report_id": report_id,
        "episode_id": episode_id,
        "story_id": episode_id,
        "title": "雾中的另一座生活区",
        "decision": decision,
        "confidence": {"level": "MEDIUM", "basis": "evidence count"},
        "risks": [{"level": "HIGH", "summary": "mountain + fog", "evidence": ["SE-1"]}],
        "recommendations": ["重新设计异常机制"],
        "evidence": [{"evidence_id": "SE-1", "explanation": REPORT_MARKER}],
        "boundaries": {"advisory_only": True, "blocks_production": False},
        "source": {"story_lock_path": "episodes/x/story.md",
                   "story_lock_sha256": "2ed0c8c9" + "0" * 56},
    }


def feedback_record(report: dict = None, **overrides) -> dict:
    values = {
        "creator_decision": "REVISE",
        "recommendation_result": "PARTIAL",
        "risk_acknowledged": True,
        "revision_direction": "重新设计异常机制",
        "final_effect": "改稿后重新评估",
        "notes": "雾中生活区与既有篇目过近",
    }
    values.update(overrides)
    return build_feedback(report if report is not None else advisor_report(), **values)


def observation_record() -> dict:
    return {"observation_id": OBSERVATION_ID, "story_dna_reference": DNA_REFERENCE,
            "episode_id": "10-03", "advisor_report_reference": "advisor_report:PPA-10-03-deadbeef"}


class _WriteCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="pp-exp-write-")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.store = JsonlExperienceStore(self.dir)

    def files(self) -> list:
        return sorted(path.name for path in self.dir.rglob("*") if path.is_file())


class FeedbackConversionTests(unittest.TestCase):
    def test_creator_decision_experience_mirrors_the_feedback(self):
        feedback = feedback_record()
        record = decision_experience_from_feedback(feedback)
        self.assertEqual(record["episode_id"], feedback["episode_id"])
        self.assertEqual(record["advisor_decision"], feedback["advisor_decision"])
        self.assertEqual(record["creator_action"], feedback["creator_decision"])
        self.assertEqual(record["recommendation_result"], feedback["recommendation_result"])
        self.assertEqual(record["final_assessment"], feedback["final_effect"])
        self.assertEqual(record["feedback_reference"], feedback["feedback_id"])
        self.assertTrue(record["advisory_only"])
        self.assertFalse(record["blocks_production"])

    def test_final_assessment_falls_back_to_notes_when_effect_is_empty(self):
        feedback = feedback_record(final_effect="", notes="只写了备注")
        self.assertEqual(decision_experience_from_feedback(feedback)["final_assessment"],
                         "只写了备注")

    def test_episode_experience_keeps_references_and_facts(self):
        feedback = feedback_record()
        record = experience_from_feedback(feedback, observation=observation_record(),
                                          production_outcome="published",
                                          audience_feedback="comments: 3")
        self.assertEqual(record["observation_reference"], OBSERVATION_ID)
        self.assertEqual(record["feedback_reference"], feedback["feedback_id"])
        self.assertEqual(record["advisor_report_reference"],
                         "advisor_report:" + feedback["advisor_report_id"])
        self.assertEqual(record["story_dna_reference"], DNA_REFERENCE)
        self.assertEqual(record["production_outcome"], "published")
        self.assertEqual(record["audience_feedback"], "comments: 3")

    def test_episode_experience_works_without_an_observation(self):
        record = experience_from_feedback(feedback_record())
        self.assertIsNone(record["observation_reference"])
        self.assertEqual(record["advisor_report_reference"],
                         "advisor_report:PPA-10-03-deadbeef")

    def test_a_risk_pattern_keeps_the_evidence_reference_only(self):
        evidence = {"evidence_id": "SE-10-03-10-02", "risk_type": "similarity",
                    "risk_level": "HIGH", "related_episode_id": "10-02",
                    "matched_features": ["mountain_environment", "fog_environment"],
                    "explanation": REPORT_MARKER}
        record = pattern_from_evidence(evidence)
        self.assertEqual(record["evidence"], ["SE-10-03-10-02"])
        self.assertEqual(record["related_episode"], ["10-02"])
        self.assertEqual(record["pattern_description"],
                         "mountain_environment + fog_environment")
        self.assertNotIn(REPORT_MARKER, json.dumps(record, ensure_ascii=False))


class IngestWritePathTests(_WriteCase):
    def test_ingest_writes_one_experience_and_one_decision(self):
        payload = ingest_feedback(feedback_record(), store=self.store,
                                  observation=observation_record())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["experience_status"], "APPENDED")
        self.assertEqual(payload["decision_status"], "APPENDED")
        self.assertEqual(len(self.store.read(KIND_EXPERIENCE)), 1)
        self.assertEqual(len(self.store.read(KIND_DECISION)), 1)
        self.assertEqual(len(self.store.read(KIND_PATTERN)), 0)
        self.assertEqual(self.files(), ["creator-decisions.jsonl", "experience-records.jsonl"])

    def test_ingest_reports_the_ids_it_wrote(self):
        payload = ingest_feedback(feedback_record(), store=self.store)
        stored = self.store.read(KIND_EXPERIENCE)[0]
        decisions = self.store.read(KIND_DECISION)[0]
        self.assertEqual(payload["experience_id"], stored["experience_id"])
        self.assertEqual(payload["decision_experience_id"], decisions["decision_experience_id"])
        self.assertEqual(payload["advisor_report_reference"], stored["advisor_report_reference"])
        self.assertEqual(payload["blocks_production"], False)
        self.assertEqual(payload["advisory_only"], True)

    def test_ingest_never_copies_the_full_advisor_report(self):
        ingest_feedback(feedback_record(), store=self.store, observation=observation_record())
        stored = self.store.read(KIND_EXPERIENCE)[0]
        self.assertEqual(set(stored), set(load_contract(EXPERIENCE_CONTRACT)["required"]))
        decision = self.store.read(KIND_DECISION)[0]
        self.assertEqual(set(decision),
                         set(load_contract(DECISION_EXPERIENCE_CONTRACT)["required"]))
        dumped = json.dumps([stored, decision], ensure_ascii=False)
        self.assertNotIn(REPORT_MARKER, dumped)
        for leaked in ("recommendations", "boundaries", "confidence", "source", "evidence"):
            self.assertNotIn(leaked, stored)

    def test_ingest_keeps_the_reference_chain_intact(self):
        feedback = feedback_record()
        payload = ingest_feedback(feedback, store=self.store, observation=observation_record())
        self.assertEqual(payload["feedback_reference"], feedback["feedback_id"])
        self.assertEqual(payload["observation_reference"], OBSERVATION_ID)
        self.assertEqual(payload["advisor_report_reference"],
                         "advisor_report:" + feedback["advisor_report_id"])

    def test_ingest_writes_no_score_like_key(self):
        ingest_feedback(feedback_record(), store=self.store)
        assert_no_scores(self, self.store.read(KIND_EXPERIENCE)[0], "episode experience")
        assert_no_scores(self, self.store.read(KIND_DECISION)[0], "creator decision experience")

    def test_reingesting_the_same_feedback_is_idempotent(self):
        feedback = feedback_record()
        first = ingest_feedback(feedback, store=self.store, observation=observation_record())
        second = ingest_feedback(feedback, store=self.store, observation=observation_record())
        self.assertEqual(first["experience_id"], second["experience_id"])
        self.assertEqual(second["experience_status"], "REUSED")
        self.assertEqual(second["decision_status"], "REUSED")
        self.assertEqual(len(self.store.read(KIND_EXPERIENCE)), 1)
        self.assertEqual(len(self.store.read(KIND_DECISION)), 1)

    def test_dry_run_writes_nothing(self):
        payload = ingest_feedback(feedback_record(), store=self.store, dry_run=True)
        self.assertEqual(payload["dry_run"], True)
        self.assertEqual(payload["experience_status"], "DRY_RUN")
        self.assertEqual(payload["decision_status"], "DRY_RUN")
        self.assertEqual(self.files(), [])
        self.assertEqual(self.store.read(KIND_EXPERIENCE), [])


class IngestFailureIsolationTests(_WriteCase):
    def test_feedback_without_a_creator_decision_raises_and_writes_nothing(self):
        broken = feedback_record()
        broken["creator_decision"] = None
        with self.assertRaises(ValueError):
            ingest_feedback(broken, store=self.store, observation=observation_record())
        self.assertEqual(self.files(), [])

    def test_feedback_with_a_foreign_creator_decision_raises(self):
        broken = feedback_record()
        broken["creator_decision"] = "APPROVED"
        with self.assertRaises(ValueError):
            ingest_feedback(broken, store=self.store)
        self.assertEqual(self.files(), [])

    def test_a_non_mapping_feedback_record_raises(self):
        with self.assertRaises(ValueError):
            ingest_feedback(["not", "a", "record"], store=self.store)
        self.assertEqual(self.files(), [])

    def test_a_rejected_ingest_keeps_earlier_records_byte_identical(self):
        ingest_feedback(feedback_record(), store=self.store, observation=observation_record())
        paths = [self.store.path_for(kind) for kind in (KIND_EXPERIENCE, KIND_DECISION)]
        before = [path.read_bytes() for path in paths]
        broken = feedback_record()
        broken["recommendation_result"] = None
        with self.assertRaises(ValueError):
            ingest_feedback(broken, store=self.store)
        self.assertEqual([path.read_bytes() for path in paths], before)

    def test_a_storage_failure_is_not_swallowed(self):
        blocked = self.dir / "blocked"
        blocked.write_text("a file where a directory is needed", encoding="utf-8")
        store = JsonlExperienceStore(blocked / "experience-store")
        with self.assertRaises(OSError):
            store.save_experience(build_experience_record(
                episode_id="10-03", observation_reference="OBS-1"))


if __name__ == "__main__":
    unittest.main()
