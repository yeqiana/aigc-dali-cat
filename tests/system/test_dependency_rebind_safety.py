#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import temporal_continuity_gate
import wardrobe_contract


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DependencyRebindSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        _write(self.ep / "meta/release-manifest.json", {"release": {"body_frame_count": 1}})
        _write(self.ep / "meta/world-state.json", {"schema_version": 1, "recorder": "P02"})
        _write(self.ep / "meta/character-contract.json", {"cast": {"members": [{"id": "P01"}]}})
        _write(self.ep / "meta/temporal-continuity.json", {
            "schema_version": 1,
            "status": "LOCKED",
            "frame_count": 1,
            "source_world_state_sha256": "stale",
            "world_state_synced": True,
            "frames": [{
                "frame": "01", "elapsed_minutes_from_prev": 0,
                "daypart": "dusk", "weather": "clear mild", "precipitation": "none",
                "ambient_light": "dusk_low", "large_transition": False, "transition_reason": "",
            }],
        })
        _write(self.ep / "meta/wardrobe-contract.json", {
            "schema_version": 1,
            "status": "LOCKED",
            "frame_count": 1,
            "source_temporal_sha256": "stale",
            "rules": {},
            "frames": {"01": {
                "scene_context": "west cloud bridge overlook",
                "location_type": "outdoor",
                "temperature_band": "mild",
                "weather": "clear mild",
                "activity": "standing and watching sunset",
                "outfits": {"P01": {
                    "present": True, "look_id": "P01_DAY_LOOK", "garments": ["日常衣裙"],
                    "outer_layer": "", "leg_layer": "", "headwear": "", "footwear": "",
                    "temperature_fit": "PASS", "weather_fit": "PASS", "activity_fit": "PASS",
                    "identity_consistent": True, "change_reason": "",
                }},
            }},
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_temporal_rebind_preserves_locked_rows_and_updates_only_source_binding(self):
        before = json.loads((self.ep / "meta/temporal-continuity.json").read_text(encoding="utf-8"))
        result = temporal_continuity_gate.rebind_source(self.ep, "world-state recorder-only correction")
        self.assertEqual(result["frames"], before["frames"])
        self.assertEqual(result["status"], "LOCKED")
        self.assertEqual(result["source_world_state_sha256"], _sha(self.ep / "meta/world-state.json"))
        self.assertEqual(temporal_continuity_gate.validate(self.ep), [])
        self.assertEqual(result["source_rebind_history"][-1]["reason"], "world-state recorder-only correction")

    def test_temporal_force_refuses_to_destroy_locked_authority_without_explicit_reset(self):
        with self.assertRaisesRegex(ValueError, "refusing destructive temporal prepare"):
            temporal_continuity_gate.prepare(self.ep, force=True)
        locked = json.loads((self.ep / "meta/temporal-continuity.json").read_text(encoding="utf-8"))
        self.assertEqual(locked["status"], "LOCKED")
        self.assertEqual(locked["frames"][0]["daypart"], "dusk")

    def test_wardrobe_rebind_preserves_locked_schedule(self):
        temporal_continuity_gate.rebind_source(self.ep, "dependency refresh")
        before = json.loads((self.ep / "meta/wardrobe-contract.json").read_text(encoding="utf-8"))
        result = wardrobe_contract.rebind_source(self.ep, "temporal source rebinding only")
        self.assertEqual(result["frames"], before["frames"])
        self.assertEqual(result["status"], "LOCKED")
        self.assertEqual(result["source_temporal_sha256"], _sha(self.ep / "meta/temporal-continuity.json"))
        self.assertEqual(wardrobe_contract.validate(self.ep), [])
        self.assertEqual(result["source_rebind_history"][-1]["reason"], "temporal source rebinding only")

    def test_wardrobe_force_refuses_to_destroy_locked_authority_without_explicit_reset(self):
        with self.assertRaisesRegex(ValueError, "refusing destructive wardrobe prepare"):
            wardrobe_contract.prepare(self.ep, force=True)
        locked = json.loads((self.ep / "meta/wardrobe-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(locked["status"], "LOCKED")
        self.assertIn("01", locked["frames"])


if __name__ == "__main__":
    unittest.main()
