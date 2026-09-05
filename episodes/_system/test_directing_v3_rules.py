#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import shot_progression_gate as gate  # noqa: E402


class DirectingV3RulesTests(unittest.TestCase):
    def _episode(self, root: Path) -> Path:
        ep = root / "ep"
        (ep / "meta").mkdir(parents=True)
        (ep / "meta/release-manifest.json").write_text(
            json.dumps({"release": {"body_frame_count": 10}}, ensure_ascii=False),
            encoding="utf-8",
        )
        data = gate.prepare(ep, force=True)
        data["status"] = "LOCKED"
        data["genre_family"] = "general_reality_crack"
        scales = ["wide", "medium", "close", "detail", "medium", "wide", "close", "medium", "detail", "wide"]
        stages = ["ordinary", "discovery", "confirmation", "spatial_contradiction", "human_consequence", "reversal", "human_consequence", "reversal", "human_consequence", "payoff"]
        for idx, row in enumerate(data["frames"], start=1):
            row.update({
                "camera_position": f"position-{idx}",
                "subject_distance": scales[idx - 1],
                "primary_subject": f"subject-{idx}",
                "action": f"action-{idx}",
                "visual_function": f"new-evidence-{idx}",
                "capture_purpose": f"record-{idx}",
                "pov_mode": "first_person",
                "location_zone": f"zone-{(idx - 1) // 2}",
                "shot_scale": scales[idx - 1],
                "scene_position_id": f"SP{idx:02d}",
                "anomaly_logic_stage": stages[idx - 1],
                "human_action_stage": "act" if idx >= 4 else "observe",
                "new_information": True,
            })
            row["lighting_design"] = {
                "practical_source": "sunlight" if idx <= 5 else "street_light",
                "contrast_mode": "soft_directional" if idx <= 5 else "partial_illumination",
                "suspense_function": "none" if idx == 1 else "guide_attention_without_staging",
                "physically_motivated": True,
                "invented_cinematic_light": False,
            }
            row["anomaly_concealment"] = {
                "carrier": "glass_reflection" if idx == 2 else "none",
                "purpose": "reflection reveals an extra figure" if idx == 2 else "",
                "physical_anchor": "bus window" if idx == 2 else "",
                "adds_information": idx == 2,
            }
        data["frames"][1]["cinematic_reference"] = {
            "reference_id": "NEGATIVE_SPACE_SUSPENSE",
            "technique_translation": "casual bus-window frame leaves doorway negative space",
            "exact_shot_recreation": False,
        }
        data["frames"][5]["cinematic_reference"] = {
            "reference_id": "FRAME_WITHIN_FRAME",
            "technique_translation": "real doorway frames the distant anomaly",
            "exact_shot_recreation": False,
        }
        gate.write_json(ep / gate.REL, data)
        return ep

    def test_valid_schema3_directing_contract(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._episode(Path(td))
            self.assertEqual(gate.validate(ep, require_locked=True), [])

    def test_duplicate_scene_position_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._episode(Path(td))
            data = gate.read_json(ep / gate.REL)
            data["frames"][4]["scene_position_id"] = data["frames"][0]["scene_position_id"]
            gate.write_json(ep / gate.REL, data)
            self.assertTrue(any("SCENE_POSITION_REUSE" in x for x in gate.validate(ep, True)))

    def test_missing_concealment_and_cinema_refs_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._episode(Path(td))
            data = gate.read_json(ep / gate.REL)
            for row in data["frames"]:
                row["cinematic_reference"] = {"reference_id": "", "technique_translation": "", "exact_shot_recreation": False}
                row["anomaly_concealment"] = {"carrier": "none", "purpose": "", "physical_anchor": "", "adds_information": False}
            gate.write_json(ep / gate.REL, data)
            errors = gate.validate(ep, True)
            self.assertTrue(any("CINEMATIC_REFERENCE_COVERAGE_FAIL" in x for x in errors))
            self.assertTrue(any("ANOMALY_CONCEALMENT_MISSING" in x for x in errors))

    def test_invented_cinematic_light_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._episode(Path(td))
            data = gate.read_json(ep / gate.REL)
            data["frames"][3]["lighting_design"]["invented_cinematic_light"] = True
            gate.write_json(ep / gate.REL, data)
            self.assertTrue(any("invented cinematic light forbidden" in x for x in gate.validate(ep, True)))


if __name__ == "__main__":
    unittest.main()
