"""Regression tests for the scheduling-only Runtime DAG Phase A skeleton."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import runtime_scheduler


def node(node_id, *, depends_on=None, priority="MEDIUM", node_type="story"):
    return {
        "node_id": node_id,
        "node_type": node_type,
        "depends_on": depends_on or [],
        "input_contract": {},
        "output_contract": {},
        "retry_policy": {},
        "priority": priority,
        "evidence_required": [],
    }


class RuntimeDagSchedulerTest(unittest.TestCase):
    def test_dependency_must_complete_before_release(self):
        result = runtime_scheduler.schedule([node("A", depends_on=["B"]), node("B")])
        self.assertEqual([item["node_id"] for item in result["dispatch"]], ["B"])
        self.assertEqual([item["node_id"] for item in result["waiting"]], ["A"])

    def test_independent_nodes_share_executable_queue(self):
        result = runtime_scheduler.schedule([node("A"), node("B")], max_workers=2)
        self.assertEqual([item["node_id"] for item in result["dispatch"]], ["A", "B"])

    def test_priority_is_high_first_and_stable_for_ties(self):
        result = runtime_scheduler.schedule([
            node("medium-first", priority="MEDIUM"),
            node("low", priority="LOW"),
            node("high-one", priority="HIGH"),
            node("high-two", priority="HIGH"),
        ], max_workers=4)
        self.assertEqual([item["node_id"] for item in result["dispatch"]],
                         ["high-one", "high-two", "medium-first", "low"])

    def test_failure_blocks_only_downstream_branch(self):
        result = runtime_scheduler.schedule([
            node("failed-root"),
            node("downstream", depends_on=["failed-root"]),
            node("independent"),
        ], failed=["failed-root"], max_workers=2)
        self.assertEqual([item["node_id"] for item in result["dispatch"]], ["independent"])
        self.assertEqual([item["node_id"] for item in result["blocked"]], ["downstream"])

    def test_scheduler_never_writes_episode_state_or_gate_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            ep = Path(temp) / "episode"
            state = ep / "meta/episode-state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8")
            before = state.read_bytes()
            result = runtime_scheduler.schedule([node("concept", node_type="concept")])
            self.assertEqual(state.read_bytes(), before)
            self.assertFalse(result["authority"]["episode_state_mutated"])
            self.assertFalse(result["authority"]["gate_decision"])
            self.assertFalse(result["authority"]["evidence_generated"])
            self.assertNotIn("gate_pass", result)


if __name__ == "__main__":
    unittest.main()
