#!/usr/bin/env python3
"""Regression tests for Story OS V2.0.3.x contract hardening."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = load_module("story_os_contract_test", HERE / "story_os_contract.py")
contract_sync = load_module("contract_sync_test", HERE / "contract_sync.py")
# Imports below resolve sibling modules through the test script directory in normal CI.
import sys
sys.path.insert(0, str(HERE))
import episode_state  # noqa: E402
import runtime_router  # noqa: E402
import release_package  # noqa: E402
import codex_auto_orchestrator  # noqa: E402


class StoryOSContractHardeningTests(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "story_os_manifest.json").read_text(encoding="utf-8-sig"))

    def test_manifest_declares_single_canonical_engine(self) -> None:
        data = self.manifest()
        self.assertEqual(data["canonical_engine"], "episodes/_system")
        self.assertEqual(data["canonical_state_source"], "<episode>/meta/episode-state.json")
        self.assertEqual(data["stages"], list(contract.CANONICAL_STAGES))

    def test_product_version_drives_engine_and_runtime(self) -> None:
        version = self.manifest()["story_os_version"]
        self.assertEqual(contract.story_os_version(ROOT), version)
        self.assertEqual(episode_state.SYSTEM_VERSION, version)
        self.assertEqual(episode_state.STATES, list(contract.CANONICAL_STAGES))
        self.assertEqual(runtime_router.capabilities()["story_os_version"], version)
        self.assertEqual(release_package.STORY_OS_VERSION, version)
        self.assertEqual(codex_auto_orchestrator.STORY_OS_VERSION, version)
        self.assertEqual(codex_auto_orchestrator.STATES, list(contract.CANONICAL_STAGES))
        orchestrator_text = (HERE / "codex_auto_orchestrator.py").read_text(encoding="utf-8-sig")
        self.assertNotIn("2.0.2", orchestrator_text)
        gates = episode_state.new_gates("TEST")
        self.assertEqual(gates["tool_version"], version)

    def test_runtime_and_authority_versions_match_manifest(self) -> None:
        version = self.manifest()["story_os_version"]
        runtime = json.loads((ROOT / "runtimes/runtime-contract.json").read_text(encoding="utf-8-sig"))
        authority = json.loads((ROOT / "standards/AUTHORITY_INDEX.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(runtime["story_os_version"], version)
        self.assertEqual(authority["story_os_version"], version)

    def test_skill_does_not_duplicate_core_engine(self) -> None:
        scripts = ROOT / "skills/dali-cat-story/scripts"
        duplicates = [name for name in contract_sync.CORE_ENGINE_FILES if (scripts / name).exists()]
        self.assertEqual(duplicates, [], f"Skill duplicated canonical engine files: {duplicates}")
        self.assertFalse((ROOT / "skills/dali-cat-story/requirements.txt").exists(),
                         "thin adapter must not own a second runtime requirements file")

    def test_adapter_contracts_are_synchronized(self) -> None:
        primary = (ROOT / "skills/dali-cat-story/SKILL.md").read_text(encoding="utf-8-sig")
        agents = (ROOT / ".agents/skills/dali-cat-story/SKILL.md").read_text(encoding="utf-8-sig")
        self.assertEqual(primary, agents)
        self.assertIn(self.manifest()["story_os_version"], primary)
        self.assertIn("Skill is an adapter, not a Story OS copy", primary)

    def test_story_gates_template_tracks_current_contract(self) -> None:
        template = json.loads((ROOT / "standards/templates/story-gates.template.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(template["tool_version"], self.manifest()["story_os_version"])
        self.assertTrue(template["machine_contract"]["strict"])
        self.assertIn("authenticity_card", template["visual"])
        self.assertIn("production_evidence", template)

    def test_repository_eol_policy(self) -> None:
        attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8-sig")
        self.assertIn("* text=auto eol=lf", attrs)
        self.assertIn("*.cmd text eol=crlf", attrs)
        self.assertIn("*.bat text eol=crlf", attrs)

    def test_full_contract_sync(self) -> None:
        self.assertEqual(contract_sync.collect_errors(ROOT), [])


if __name__ == "__main__":
    unittest.main()
