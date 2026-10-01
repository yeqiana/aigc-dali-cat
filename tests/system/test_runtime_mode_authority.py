"""Production mode must not be switched by the legacy runtime variable."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
import production_mode


class RuntimeModeAuthorityTests(unittest.TestCase):
    def test_runtime_mapping_is_pure_and_explicit(self):
        self.assertEqual(production_mode.runtime_for_mode("COLLABORATIVE"), "WORK")
        self.assertEqual(production_mode.runtime_for_mode("CODEX_MANAGED"), "CODEX")
        with self.assertRaises(ValueError):
            production_mode.runtime_for_mode("AUTO")

    def test_legacy_runtime_cannot_switch_configured_production_mode(self):
        for configured, runtime in (("COLLABORATIVE", "WORK"), ("CODEX_MANAGED", "CODEX")):
            for legacy in ("WORK", "WEB", "CODEX"):
                with self.subTest(configured=configured, legacy=legacy), mock.patch.dict(
                    os.environ, {"STORY_OS_RUNTIME": legacy}, clear=True
                ):
                    resolved = production_mode.resolve({"production": {"mode": configured}})
                self.assertEqual(resolved["effective_mode"], configured)
                self.assertEqual(resolved["effective_runtime"], runtime)
                self.assertEqual(resolved["source"], "config/storyos.yaml#production.mode")
                self.assertEqual(resolved["legacy_runtime_override"], legacy)

    def test_explicit_production_override_wins_over_both_config_and_legacy_runtime(self):
        for override, runtime in (("COLLABORATIVE", "WORK"), ("CODEX_MANAGED", "CODEX")):
            with self.subTest(override=override), mock.patch.dict(os.environ, {
                "STORY_OS_RUNTIME": "WORK" if runtime == "CODEX" else "CODEX",
                "STORY_OS_PRODUCTION_MODE": override,
            }, clear=True):
                resolved = production_mode.resolve({"production": {"mode": "COLLABORATIVE"}})
            self.assertEqual(resolved["effective_mode"], override)
            self.assertEqual(resolved["effective_runtime"], runtime)
            self.assertEqual(resolved["source"], "env:STORY_OS_PRODUCTION_MODE")
            self.assertIsNone(resolved["legacy_runtime_override"])


if __name__ == "__main__":
    unittest.main()
