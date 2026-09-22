from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import capture_event_contract
import preimage_directing_materializer as materializer
import temporal_continuity_gate
import wardrobe_contract
import world_state


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class PreimageDirectingMaterializerTest(unittest.TestCase):
    def make_episode(self, raw: str) -> Path:
        ep = Path(raw)
        (ep / "meta/runtime").mkdir(parents=True)
        write(ep / "meta/release-manifest.json", {"release": {"body_frame_count": 2}})
        write(
            ep / "meta/character-contract.json",
            {
                "cast": {
                    "members": [
                        {
                            "id": "P01",
                            "gender": "male",
                            "age": 25,
                            "build": "ordinary",
                            "hair": "black short hair",
                            "clothing_anchor": "grey jacket and dark trousers",
                            "device_anchor": "ordinary smartphone",
                        },
                        {
                            "id": "P02",
                            "gender": "female",
                            "age": 25,
                            "build": "ordinary",
                            "hair": "black shoulder-length hair",
                            "clothing_anchor": "beige jacket and jeans",
                        },
                    ]
                },
                "pov": {"character_id": "P01", "first_person": True},
            },
        )
        write(
            ep / "meta/shot-progression-review.json",
            {
                "status": "LOCKED",
                "frames": [
                    {
                        "frame": 1,
                        "location_zone": "village courtyard",
                        "camera_position": "handheld selfie",
                        "subject_distance": "near",
                        "pov_mode": "selfie",
                        "action": "arrive at the old house",
                        "capture_purpose": "record arrival with friend",
                        "visual_function": "ordinary relationship baseline",
                        "human_present": True,
                        "human_action_stage": "arrival",
                        "anomaly_logic_stage": "ordinary",
                        "emotion": {"state": "relaxed"},
                        "interaction": {"meaningful": True},
                        "lighting_design": {"practical_source": "daylight"},
                    },
                    {
                        "frame": 2,
                        "location_zone": "old house main room",
                        "camera_position": "handheld close view",
                        "subject_distance": "close",
                        "pov_mode": "first person",
                        "action": "read the marked almanac",
                        "capture_purpose": "keep evidence of the changed page",
                        "visual_function": "climax evidence",
                        "human_present": False,
                        "human_action_stage": "verify",
                        "anomaly_logic_stage": "confirmed",
                        "emotion": {"state": "tense"},
                        "interaction": {"meaningful": False},
                        "lighting_design": {"practical_source": "bare bulb"},
                    },
                ],
            },
        )
        write(
            ep / "meta/story-gates.json",
            {
                "story": {"climax_frame": 2},
                "visual": {
                    "environment_contract": {
                        "schema_version": 1,
                        "season": "mild",
                        "baseline": {
                            "condition": "clear morning",
                            "time_of_day": "morning",
                            "temperature_feel": "mild",
                            "ground_state": "dry",
                            "visibility": "clear",
                            "wind": "light",
                            "precipitation": "none",
                            "physical_cues": ["ordinary daylight"],
                        },
                        "segments": [
                            {
                                "id": "S1",
                                "start_frame": 1,
                                "end_frame": 1,
                                "condition": "clear morning",
                                "time_of_day": "morning",
                                "physical_cues": ["ordinary daylight"],
                                "conditional_effects": [],
                            },
                            {
                                "id": "S2",
                                "start_frame": 2,
                                "end_frame": 2,
                                "condition": "dry night",
                                "time_of_day": "night",
                                "physical_cues": ["bare bulb"],
                                "conditional_effects": [],
                            },
                        ],
                        "frame_overrides": {},
                    },
                    "frame_directives": {
                        "01": {
                            "narrative_role": "setup",
                            "frame_mode": "normal_record",
                            "impact_level": 0,
                            "required_visual_cues": [],
                            "scale_reference": "",
                            "escalation_from": None,
                        },
                        "02": {
                            "narrative_role": "climax",
                            "frame_mode": "climax_impact",
                            "impact_level": 3,
                            "required_visual_cues": ["marked almanac beside a human hand"],
                            "scale_reference": "human hand beside ordinary almanac",
                            "escalation_from": 1,
                        },
                    },
                    "world_state": {
                        "initial_location": "old house",
                        "weather": "clear mild",
                        "persistent_props": ["almanac"],
                    },
                    "temporal_continuity": {"timeline": ["morning", "night"]},
                    "wardrobe": {"look_policy": "stable ordinary clothing"},
                },
            },
        )
        write(
            ep / "meta/runtime/preimage-authority-barrier.json",
            {"status": "READY", "committed_snapshot_id": "snapshot-1"},
        )
        return ep

    def test_materializes_and_validates_missing_strict_contracts(self):
        with tempfile.TemporaryDirectory() as raw:
            ep = self.make_episode(raw)
            result = materializer.ensure(ep)
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(all(value == "CREATED" for value in result["contracts"].values()))
            self.assertEqual(capture_event_contract.validate(ep, True), [])
            self.assertEqual(world_state.validate(ep, True), [])
            self.assertEqual(temporal_continuity_gate.validate(ep, True), [])
            self.assertEqual(wardrobe_contract.validate(ep, True), [])
            temporal = json.loads((ep / "meta/temporal-continuity.json").read_text(encoding="utf-8"))
            self.assertTrue(temporal["frames"][1]["large_transition"])
            self.assertGreaterEqual(temporal["frames"][1]["elapsed_minutes_from_prev"], 20)
            reused = materializer.ensure(ep)
            self.assertTrue(all(value == "REUSED" for value in reused["contracts"].values()))

    def test_existing_invalid_contract_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as raw:
            ep = self.make_episode(raw)
            path = ep / "meta/capture-event-contract.json"
            original = {"schema_version": 1, "status": "DRAFT", "frames": {}}
            write(path, original)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "refusing overwrite"):
                materializer.ensure(ep)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
