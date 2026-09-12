"""Smart Scheduler contracts stay planner-only and preserve Runtime authority."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))
import production_plan
import runtime_failure_strategy
import runtime_node_execution
import runtime_node_registry
import runtime_scheduler


class SmartSchedulerTest(unittest.TestCase):
    def test_registry_contains_complete_logical_production_chain(self):
        nodes = {row["node_id"]: row for row in runtime_node_registry.first_batch_nodes()}
        self.assertEqual(set(nodes), {"story_lock", "character_prepare", "environment_prepare",
                         "frame_contract_compile", "image_generation", "review", "repair", "release"})
        self.assertEqual(nodes["release"]["depends_on"], ["review", "repair"])

    def test_parallel_release_and_priority_score_are_deterministic(self):
        rows = runtime_node_registry.first_batch_nodes()
        result = runtime_scheduler.schedule(rows, completed=["story_lock"], max_workers=2)
        self.assertEqual([x["node_id"] for x in result["dispatch"]], ["character_prepare", "environment_prepare"])
        tasks = [dict(rows[1], depends_on=[], priority="MEDIUM", priority_score=60),
                 dict(rows[2], depends_on=[], priority="MEDIUM", priority_score=70)]
        self.assertEqual([x["node_id"] for x in runtime_scheduler.schedule(tasks, max_workers=2)["dispatch"]],
                         ["environment_prepare", "character_prepare"])

    def test_failure_isolated_and_resource_slots_limit_dispatch(self):
        independent = {"node_id": "independent", "node_type": "review", "depends_on": [],
                       "priority": "LOW", "executor": "review", "evidence_required": [],
                       "input_contract": {}, "output_contract": {}, "retry_policy": {}}
        result = runtime_scheduler.schedule(runtime_node_registry.first_batch_nodes() + [independent],
                                            failed=["story_lock"], max_workers=2)
        self.assertEqual([x["node_id"] for x in result["dispatch"]], ["independent"])
        rows = [dict(independent, node_id="a"), dict(independent, node_id="b"), dict(independent, node_id="c")]
        limited = runtime_scheduler.schedule(rows, max_workers=3,
            resource_snapshot={"max_workers": 3, "runtime_capacity": {"text": 2, "image": 1}})
        self.assertEqual([x["node_id"] for x in limited["dispatch"]], ["a", "b"])
        self.assertEqual([x["node_id"] for x in limited["queued"]], ["c"])

    def test_execution_evidence_and_dry_run_do_not_change_state(self):
        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw); state = ep / "meta/episode-state.json"; state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8"); before = state.read_bytes()
            row = runtime_node_execution.record(ep, node_id="review", start_time="a", end_time="b",
                status="FAILED", attempt=2, output="fact", evidence=["meta/frame-reviews"])
            plan = production_plan.build(ep)
            self.assertEqual(state.read_bytes(), before); self.assertEqual(row["attempt"], 2)
            self.assertIsNone(row["gate_pass"]); self.assertTrue(plan["dry_run"])
            self.assertFalse((ep / production_plan.REL).exists())

    def test_failure_strategy_is_advice_not_gate(self):
        resolved = runtime_failure_strategy.resolve("identity_failure")
        self.assertEqual(resolved["action"], "reference_repair")
        self.assertIn("no_episode_state", resolved["authority"])


if __name__ == "__main__": unittest.main()
