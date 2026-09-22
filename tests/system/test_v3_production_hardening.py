"""Regression coverage for E003-E006; all records remain evidence, not state."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))
import failure_memory
import story_dna_trace
import style_registry
import visual_reality_score


class ProductionHardeningTest(unittest.TestCase):
    def test_story_dna_trace_requires_mapping_and_contract_binding(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td) / "episodes/demo"; (ep / "meta/runtime/contracts/frames").mkdir(parents=True)
            (ep / "meta").mkdir(exist_ok=True)
            (ep / "meta/release-manifest.json").write_text(json.dumps({"body_frame_count": 2}), encoding="utf-8")
            (ep / "meta/story-gates.json").write_text(json.dumps({"story": {"story_core": "A", "emotional_goal": "B", "character_relationship": "C", "reversal_point": "D"}}), encoding="utf-8")
            doc = story_dna_trace.build(ep, required_frames=[1])
            for key, item in doc["frame_mapping"].items():
                (ep / f"meta/runtime/contracts/frames/{key}.json").write_text(json.dumps({"story_dna_mapping": item}), encoding="utf-8")
            self.assertEqual(story_dna_trace.verify(ep), [])
            (ep / "meta/runtime/contracts/frames/01.json").write_text("{}", encoding="utf-8")
            self.assertTrue(any("contract_mapping_missing:01" in e for e in story_dna_trace.verify(ep)))

    def test_failure_memory_is_append_only_and_reusable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            failure_memory.record({"failure_type": "realism_failure", "frame_id": "15", "prompt_issue": "too polished", "visual_issue": "ad-like", "identity_issue": "", "repair_action": "regenerate_frame", "final_result": "passed"}, root=root)
            self.assertEqual(failure_memory.guidance(failure_type="realism_failure", root=root)[0]["repair_action"], "regenerate_frame")
            with self.assertRaises(ValueError):
                failure_memory.record({"failure_type": "unknown", "frame_id": "15", "prompt_issue": "", "visual_issue": "", "identity_issue": "", "repair_action": "x", "final_result": "passed"}, root=root)

    def test_visual_reality_low_score_requires_repair(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            dimensions = {"phone_capture": 50, "lighting_realism": 50, "depth_realism": 50, "human_naturalness": 50, "scene_lived_in": 50, "ai_artifact_risk": 90}
            result = visual_reality_score.score(ep, "1", dimensions)
            self.assertEqual(result["decision"], "repair_required")
            self.assertIn("visual_reality_score_missing_or_low:01", visual_reality_score.verify(ep))

    def test_style_registry_aliases_existing_visual_profile_authority(self):
        m00 = style_registry.resolve("M00_REAL_LIFE")
        self.assertEqual(m00["visual_profile_id"], "M00_REAL_WORLD_DOCUMENTARY_V1")
        with self.assertRaises(ValueError): style_registry.resolve("UNREGISTERED")

    def test_ep003_reports_historical_evidence_missing(self):
        candidates = list((ROOT / "episodes/_archive").glob("*EP003*"))
        if not candidates:
            self.skipTest("EP003 archive is absent in this checkout")
        ep = candidates[0]
        self.assertIn("Historical Evidence Missing: meta/story-dna-trace.json", story_dna_trace.verify(ep))


if __name__ == "__main__":
    unittest.main()
