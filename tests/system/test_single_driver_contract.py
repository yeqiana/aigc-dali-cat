#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2.6.1.1 single-driver contract: the portal must name one driver, and CI must care.

The 尸解仙 stall was not a crash. The agent drove runtime_dag.py by hand, nothing ever
started the resident loop, and no document said those were different things. Prose
alone had already failed once, so the block is asserted here and enforced again by
contract_sync on every doctor/CI run.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import contract_sync

START_HERE = ROOT / "START_HERE.md"
INDEX = ROOT / "episodes/_system/MODULE_INDEX.json"
CONTRACT_SYNC = ROOT / "episodes/_system/contract_sync.py"
ANALYSIS = ROOT / "docs/Story_OS_项目现状与执行流程分析_20260914.md"

BEGIN = "<!-- STORY_OS_SINGLE_DRIVER_BEGIN -->"
END = "<!-- STORY_OS_SINGLE_DRIVER_END -->"
REQUIRED_TOKENS = (
    "story_os.py runner",
    "story_os.py run",
    # The detached form of the same single driver (P0-C). It must be in the block
    # too, or the portal would name only the foreground entrypoint and an agent
    # would keep starting the Driver on a 300 s budget.
    "story_os.py driver",
    "runtime_dag",
    "host_loop",
    "orphaned_pending_work",
)


class SingleDriverContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.text = START_HERE.read_text(encoding="utf-8-sig")

    def block(self) -> str:
        return self.text.split(BEGIN, 1)[1].split(END, 1)[0]

    def test_portal_declares_exactly_one_single_driver_block(self) -> None:
        self.assertEqual(self.text.count(BEGIN), 1)
        self.assertEqual(self.text.count(END), 1)
        self.assertLess(self.text.index(BEGIN), self.text.index(END))

    def test_block_names_the_driver_the_drain_and_the_step_engine(self) -> None:
        body = self.block()
        for token in REQUIRED_TOKENS:
            self.assertIn(token, body)

    def test_block_separates_the_resident_driver_from_the_step_engine(self) -> None:
        body = self.block()
        self.assertIn("唯一常驻驱动", body)
        self.assertIn("步骤引擎", body)
        self.assertIn("有界排空", body)

    def test_block_promises_visibility_without_a_watchdog(self) -> None:
        body = self.block()
        self.assertIn("不提供看门狗", body)
        self.assertIn("orphaned_pending_work", body)

    def test_runtime_dag_is_a_step_engine_not_an_entrypoint(self) -> None:
        index = json.loads(INDEX.read_text(encoding="utf-8-sig"))
        self.assertNotIn("runtime_dag.py", index["canonical_entrypoints"])
        self.assertIn("runtime_dag.py", index["step_engines"])
        self.assertIn("story_os.py", index["canonical_entrypoints"])
        self.assertIn("workflow_runner.py", index["canonical_entrypoints"])
        self.assertIn("step_engines", index["agent_read_policy"])
        self.assertIn("story_os.py runner", index["agent_read_policy"])

    def test_contract_sync_enforces_the_same_block(self) -> None:
        self.assertEqual(contract_sync.SINGLE_DRIVER_MARKER, "STORY_OS_SINGLE_DRIVER")
        self.assertEqual(list(contract_sync.SINGLE_DRIVER_REQUIRED_TOKENS), list(REQUIRED_TOKENS))
        self.assertEqual(contract_sync.single_driver_errors(ROOT), [])

    def test_contract_sync_actually_calls_the_validator(self) -> None:
        # A defined-but-uncalled validator protects nothing while this suite stays green.
        source = CONTRACT_SYNC.read_text(encoding="utf-8-sig")
        self.assertIn("errors.extend(single_driver_errors(root))", source)

    def test_analysis_doc_classifies_the_step_engine(self) -> None:
        text = ANALYSIS.read_text(encoding="utf-8-sig")
        self.assertIn("step_engines", text)
        self.assertIn("步骤引擎", text)
        self.assertNotIn("`runtime_dag.py` / `next_action.py`", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
