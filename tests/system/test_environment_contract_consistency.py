#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import environment_contract


class EnvironmentContractConsistencyTests(unittest.TestCase):
    def _env(self, *, segment_time=None, cues=None):
        segment = {
            "id": "S_DUSK",
            "start_frame": 1,
            "end_frame": 1,
            "condition": "clear dusk on exposed bridge",
            "physical_cues": cues or ["ordinary bridge breeze"],
            "conditional_effects": [],
        }
        if segment_time is not None:
            segment["time_of_day"] = segment_time
        return {
            "schema_version": 1,
            "baseline": {
                "condition": "clear morning",
                "time_of_day": "morning",
                "ground_state": "dry",
                "visibility": "clear",
                "physical_cues": ["soft daylight"],
            },
            "segments": [segment],
            "frame_overrides": {},
        }

    def _directives(self, *, cues=None, impact=3):
        return {"01": {
            "narrative_role": "climax",
            "frame_mode": "climax_impact",
            "impact_level": impact,
            "required_visual_cues": cues or ["ordinary small figures against cloud sea"],
            "scale_reference": "small figures against wide geography",
            "escalation_from": 0,
            "generation_depends_on": [],
        }}

    def test_effective_daypart_conflict_is_detected_before_image_generation(self):
        env = self._env(segment_time=None)
        with patch.object(environment_contract, "_reality_first", return_value=False):
            errors = environment_contract.validate_effective_consistency(Path("ep"), env, self._directives(impact=1), 1)
        self.assertTrue(any(x.startswith("ENVIRONMENT_TIME_CONFLICT:01") for x in errors), errors)

    def test_explicit_segment_daypart_closes_inherited_baseline_conflict(self):
        env = self._env(segment_time="dusk")
        with patch.object(environment_contract, "_reality_first", return_value=False):
            errors = environment_contract.validate_effective_consistency(Path("ep"), env, self._directives(impact=1), 1)
        self.assertEqual(errors, [])

    def test_reality_first_high_impact_positive_promo_cue_is_rejected(self):
        env = self._env(segment_time="dusk", cues=["large golden cloud sea"])
        with patch.object(environment_contract, "_reality_first", return_value=True):
            errors = environment_contract.validate_effective_consistency(Path("ep"), env, self._directives(), 1)
        self.assertTrue(any(x.startswith("REALITY_FIRST_PROMO_CUE_CONFLICT:01") for x in errors), errors)

    def test_negative_anti_promo_wording_is_not_false_positive(self):
        env = self._env(segment_time="dusk", cues=["ordinary-device exposure rather than golden HDR rendering"])
        directives = self._directives(cues=["no tourism-poster blocking", "sun remains off-axis"])
        with patch.object(environment_contract, "_reality_first", return_value=True):
            errors = environment_contract.validate_effective_consistency(Path("ep"), env, directives, 1)
        self.assertEqual(errors, [])

    def test_afternoon_does_not_match_noon_substring(self):
        self.assertEqual(environment_contract._implied_daypart("warm afternoon market"), "afternoon")


if __name__ == "__main__":
    unittest.main()
