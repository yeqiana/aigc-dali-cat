#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import storyos_config
import runtime_timeout_policy as ttp


class RuntimeTimeoutPolicyTests(unittest.TestCase):
    def test_config_matches_historical_defaults(self):
        cfg = storyos_config.load_config()
        policy = storyos_config.get_path(cfg, "timeout_policy")
        self.assertIsInstance(policy, dict)
        for role in ttp.REQUIRED_ROLES:
            self.assertEqual(policy.get(role), ttp.DEFAULT_SECONDS[role], role)
            self.assertEqual(ttp.seconds(role), policy[role], role)

    def test_clamp_bounds(self):
        self.assertEqual(ttp.clamp("fast_scout", 10_000), 240)
        self.assertEqual(ttp.clamp("fast_scout", 10), 60)
        self.assertEqual(ttp.clamp("image_lane_run", 10_000), 600)
        self.assertEqual(ttp.clamp("image_lane_run", 10), 60)
        self.assertEqual(ttp.clamp("review_critic", 456), 456)

    def test_unknown_role_rejected(self):
        with self.assertRaises(ValueError):
            ttp.seconds("no_such_role")

    def test_validate_rejects_non_mapping(self):
        cfg = copy.deepcopy(storyos_config.load_config())
        cfg["timeout_policy"] = None
        errors = storyos_config.validate(cfg)
        self.assertTrue(any("timeout_policy must be a mapping" in e for e in errors))

    def test_validate_rejects_non_positive_int(self):
        cfg = copy.deepcopy(storyos_config.load_config())
        cfg["timeout_policy"]["fast_scout"] = -1
        errors = storyos_config.validate(cfg)
        self.assertTrue(any("timeout_policy.fast_scout" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

