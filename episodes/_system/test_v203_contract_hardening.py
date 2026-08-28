#!/usr/bin/env python3
"""Regression tests for Story OS V2.0.3 contract hardening."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

spec = importlib.util.spec_from_file_location("contract_sync", HERE / "contract_sync.py")
assert spec and spec.loader
contract_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract_sync)


class StoryOSV203ContractHardeningTests(unittest.TestCase):
    def test_manifest_declares_v203_and_single_canonical_engine(self) -> None:
        data = json.loads((ROOT / "story_os_manifest.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(data["story_os_version"], "2.0.3")
        self.assertEqual(data["canonical_engine"], "episodes/_system")
        self.assertEqual(data["canonical_state_source"], "<episode>/meta/episode-state.json")
        self.assertEqual(data["stages"], contract_sync.EXPECTED_STAGES)

    def test_skill_does_not_duplicate_core_engine(self) -> None:
        scripts = ROOT / "skills" / "dali-cat-story" / "scripts"
        duplicates = [name for name in contract_sync.CORE_ENGINE_FILES if (scripts / name).exists()]
        self.assertEqual(duplicates, [], f"Skill duplicated canonical engine files: {duplicates}")

    def test_adapter_wrappers_delegate_to_canonical_engine(self) -> None:
        scripts = ROOT / "skills" / "dali-cat-story" / "scripts"
        bootstrap = (scripts / "bootstrap_episode.py").read_text(encoding="utf-8-sig")
        validate_all = (scripts / "validate_all.py").read_text(encoding="utf-8-sig")
        self.assertIn("episode_state.py", bootstrap)
        self.assertIn('"init"', bootstrap)
        self.assertIn("validate_episode.py", validate_all)

    def test_adapter_contracts_are_synchronized(self) -> None:
        primary = (ROOT / "skills" / "dali-cat-story" / "SKILL.md").read_text(encoding="utf-8-sig")
        agents = (ROOT / ".agents" / "skills" / "dali-cat-story" / "SKILL.md").read_text(encoding="utf-8-sig")
        self.assertEqual(primary, agents)
        self.assertIn("V2.0.3", primary)
        self.assertIn("Skill is an adapter, not a Story OS copy", primary)

    def test_full_contract_sync(self) -> None:
        self.assertEqual(contract_sync.collect_errors(ROOT), [])


if __name__ == "__main__":
    unittest.main()
