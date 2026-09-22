#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W-93/D5: invalid Environment PREIMAGE must fail before authority commit."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import preimage_task_contract as tasks


class PreimageEnvironmentCandidateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="preimage-env-contract-", dir=base)
        self.ep = Path(self._td.name)
        (self.ep / "meta").mkdir(parents=True, exist_ok=True)
        (self.ep / "meta/release-manifest.json").write_text(
            json.dumps({"release": {"body_frame_count": 2}}), encoding="utf-8")
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps({"schema_version": 1, "story": {}, "visual": {}}), encoding="utf-8")
        self.snapshot = {
            "snapshot_id": "a" * 64,
            "authority_sha256": {"story_gates": "b" * 64},
        }
        self.task = tasks.task_contract(self.ep, "ENVIRONMENT_PREPARE", self.snapshot)

    def tearDown(self) -> None:
        self._td.cleanup()

    def payload(self, *, include_segment_daypart: bool) -> dict:
        segment = {
            "id": "S02",
            "start_frame": 2,
            "end_frame": 2,
            "condition": "warm afternoon market",
            "physical_cues": ["angled daylight"],
            "conditional_effects": [],
        }
        if include_segment_daypart:
            segment["time_of_day"] = "afternoon"
        return {
            "visual.environment_contract": {
                "schema_version": 1,
                "season": "mild",
                "baseline": {
                    "condition": "clear morning",
                    "time_of_day": "morning",
                    "ground_state": "dry",
                    "visibility": "clear",
                    "physical_cues": ["soft morning light"],
                },
                "segments": [segment],
                "frame_overrides": {},
            },
            "visual.frame_directives": {
                "01": {
                    "narrative_role": "setup",
                    "frame_mode": "normal_record",
                    "impact_level": 0,
                    "required_visual_cues": [],
                    "scale_reference": "",
                    "escalation_from": None,
                },
                "02": {
                    "narrative_role": "transition",
                    "frame_mode": "normal_record",
                    "impact_level": 0,
                    "required_visual_cues": [],
                    "scale_reference": "",
                    "escalation_from": None,
                },
            },
        }

    def test_candidate_with_inherited_wrong_daypart_is_rejected_before_write(self) -> None:
        candidate = tasks.candidate_template(
            self.task, self.payload(include_segment_daypart=False))
        errors = tasks.verify_candidate(candidate, self.task)
        self.assertTrue(any("ENVIRONMENT_TIME_CONFLICT:02" in e for e in errors), errors)
        self.assertTrue(tasks.write_candidate(self.ep, self.task, candidate))
        self.assertFalse((self.ep / self.task["candidate_output"]).exists())

    def test_candidate_with_explicit_matching_daypart_passes(self) -> None:
        candidate = tasks.candidate_template(
            self.task, self.payload(include_segment_daypart=True))
        errors = tasks.verify_candidate(candidate, self.task)
        self.assertEqual(errors, [])

    def test_scoped_environment_directive_mentions_daypart_consistency(self) -> None:
        import scoped_codex_worker
        directive = scoped_codex_worker.STEP_DIRECTIVES["PREIMAGE_ENVIRONMENT"]
        self.assertIn("time_of_day", directive)
        self.assertIn("physically consistent", directive)


if __name__ == "__main__":
    unittest.main(verbosity=2)
