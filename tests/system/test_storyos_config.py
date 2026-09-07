#!/usr/bin/env python3
from __future__ import annotations

import sys
import copy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import storyos_config


class StoryOSConfigTests(unittest.TestCase):
    def test_config_and_index_validate(self):
        self.assertEqual(storyos_config.validate(), [])
        self.assertEqual(storyos_config.validate_index(), [])
        index = storyos_config.load_index()
        self.assertEqual(index["config"], "config/storyos.yaml")
        self.assertIn("PRODUCTION", index["stage_read_sets"])

    def test_current_image_configuration(self):
        config = storyos_config.load_config()
        self.assertEqual(storyos_config.get_path(config, "image.model"), "gpt-image-2")
        self.assertEqual(storyos_config.get_path(config, "image.quality"), "high")
        self.assertEqual(storyos_config.get_path(config, "visual.default_profile_id"), "M00")
        self.assertEqual(storyos_config.get_path(config, "normalize.automatic_ratio_delta_max"), 0.01)
        self.assertEqual(storyos_config.get_path(config, "normalize.review_ratio_delta_max"), 0.03)
        self.assertEqual(storyos_config.get_path(config, "production.max_inflight_images"), 3)

    def test_stage_read_sets_start_with_config(self):
        index = storyos_config.load_index()
        for step, paths in index["stage_read_sets"].items():
            self.assertEqual(paths[0], "config/storyos.yaml", step)

    def test_invalid_quality_fails_fast(self):
        config = copy.deepcopy(storyos_config.load_config())
        config["image"]["quality"] = "medium"
        self.assertIn("image.quality must be high", storyos_config.validate(config))

    def test_compat_switches_must_be_typed_bools(self):
        base = storyos_config.load_config()
        for key in ("read_legacy_json", "rewrite_bound_runtime_request", "migrate_historical_episode_meta"):
            bad = copy.deepcopy(base)
            bad["compatibility"][key] = "true"
            self.assertIn(f"compatibility.{key} must be a bool", storyos_config.validate(bad))

    def test_compat_switch_off_still_valid(self):
        config = copy.deepcopy(storyos_config.load_config())
        config["compatibility"]["read_legacy_json"] = False
        self.assertEqual(storyos_config.validate(config), [])

    def test_legacy_json_read_guard(self):
        live = storyos_config.load_config()
        self.assertTrue(storyos_config.legacy_json_read_allowed(live))
        storyos_config.guard_legacy_json_read("runtime-index.json")
        blocked = copy.deepcopy(live)
        blocked["compatibility"]["read_legacy_json"] = False
        self.assertFalse(storyos_config.legacy_json_read_allowed(blocked))
        with self.assertRaisesRegex(ValueError, "LEGACY_JSON_READ_BLOCKED"):
            storyos_config.guard_legacy_json_read("runtime-index.json", cfg=blocked)

    def test_index_contracts_internal_and_episode_layout(self):
        index = storyos_config.load_index()
        self.assertIsInstance(index["internal"]["legacy_runtime_index"], str)
        for group in ("authority", "evidence", "derived", "local_derived", "media"):
            self.assertIn(group, index["episode_layout"])


if __name__ == "__main__":
    unittest.main()
