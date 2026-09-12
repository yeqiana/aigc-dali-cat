"""V2.1 Registry and execution-fact regression coverage."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import runtime_node_evidence
import runtime_node_registry
import runtime_scheduler


class RuntimeNodeRegistryTest(unittest.TestCase):
    def test_first_batch_nodes_are_registered_with_declared_dependencies(self):
        nodes = {item["node_id"]: item for item in runtime_node_registry.first_batch_nodes()}
        self.assertEqual(nodes["character_prepare"]["depends_on"], ["story_lock"])
        self.assertEqual(nodes["environment_prepare"]["depends_on"], ["story_lock"])
        self.assertEqual(nodes["frame_contract_compile"]["depends_on"],
                         ["character_prepare", "environment_prepare"])
        self.assertEqual(nodes["image_generation"]["depends_on"], ["frame_contract_compile"])

    def test_scheduler_releases_parallel_preparation_after_story_lock(self):
        result = runtime_scheduler.schedule(
            runtime_node_registry.first_batch_nodes(), completed=["story_lock"], max_workers=2)
        self.assertEqual([item["node_id"] for item in result["dispatch"]],
                         ["character_prepare", "environment_prepare"])

    def test_failed_node_does_not_block_independent_node(self):
        contract = runtime_node_registry.first_batch_nodes() + [{
            "node_id": "independent_review", "node_type": "review", "depends_on": [],
            "priority": "LOW", "executor": "review", "evidence_required": [],
            "input_contract": {}, "output_contract": {}, "retry_policy": {},
        }]
        result = runtime_scheduler.schedule(contract, failed=["story_lock"], max_workers=2)
        self.assertEqual([item["node_id"] for item in result["dispatch"]], ["independent_review"])
        self.assertIn("character_prepare", [item["node_id"] for item in result["blocked"]])

    def test_execution_evidence_is_fact_only_and_preserves_episode_state(self):
        with tempfile.TemporaryDirectory() as temp:
            ep = Path(temp)
            state = ep / "meta/episode-state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8")
            before = state.read_bytes()
            row = runtime_node_evidence.record(
                ep, node_id="story_lock", start_time="2026-09-12T00:00:00+00:00",
                end_time="2026-09-12T00:00:01+00:00", status="PASS",
                output="executor returned", evidence=["meta/story-gates.json"])
            self.assertEqual(state.read_bytes(), before)
            self.assertIsNone(row["gate_pass"])
            self.assertFalse(row["episode_state_mutated"])


if __name__ == "__main__":
    unittest.main()
