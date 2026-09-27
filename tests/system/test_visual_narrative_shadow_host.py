from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import host_request_persistence
import preimage_execution_persistence as execution
import preimage_task_contract as tasks
import product_runtime_adapter as adapter


class VisualNarrativeShadowHostTest(unittest.TestCase):
    def setUp(self):
        base = ROOT / ".storyos-tmp"
        base.mkdir(exist_ok=True)
        self.raw = tempfile.mkdtemp(prefix="visual-shadow-", dir=base)
        self.ep = Path(self.raw)
        (self.ep / "meta").mkdir()
        (self.ep / "meta/episode-state.json").write_text(
            '{"current_state":"STORYBOARD_LOCKED"}', encoding="utf-8")
        (self.ep / "meta/story-gates.json").write_text(
            '{"story":{"locked":true,"climax_frame":10},"visual":{}}', encoding="utf-8")
        (self.ep / "meta/shot-progression-review.json").write_text(json.dumps({
            "schema_version": 3, "status": "LOCKED", "genre_family": "suspense_strange",
            "anomaly_applicable": True, "interaction_applicable": True,
            "rules": {"max_identical_setup_consecutive": 2},
            "frames": [{"frame": "01", "shot_scale": "wide", "scene_position_id": "doorway"}],
        }), encoding="utf-8")
        self.old_meta = host_request_persistence.storage_config.episode_meta_store_config
        self.old_mode = execution.mode
        host_request_persistence.storage_config.episode_meta_store_config = lambda: {"mode": "json"}
        execution.mode = lambda: "json"
        self.flags = [
            patch.object(adapter, "character_finalize_shadow_enabled", return_value=False),
            patch.object(adapter, "world_prepare_shadow_enabled", return_value=False),
            patch.object(adapter, "visual_narrative_prepare_shadow_enabled", return_value=True),
            patch.object(adapter, "visual_narrative_prepare_production_enabled", return_value=False),
        ]
        for flag in self.flags:
            flag.start()

    def tearDown(self):
        for flag in reversed(self.flags):
            flag.stop()
        host_request_persistence.storage_config.episode_meta_store_config = self.old_meta
        execution.mode = self.old_mode
        shutil.rmtree(self.raw, ignore_errors=True)

    def _requests(self):
        response = adapter.build_request(self.ep, runtime="WORK", mode="full_auto", resume=True, source="visual-test")
        shadow = next(row for row in response["shadow_requests"] if row["shadow_kind"] == "VISUAL_NARRATIVE_PREPARE_AGENT")
        legacy = next(row for row in response["requests"] if row["task"]["task_type"] == "VISUAL_NARRATIVE_PREPARE")
        return response, shadow, legacy

    def _candidate(self, request, shadow_request=None):
        source_task = (shadow_request or request)["task"]
        capsule = source_task["input_contract"]["visual_narrative_capsule"]
        payload = {key: value for key, value in capsule["obligations"]["scopes"].items()}
        candidate = tasks.candidate_template(request["task"], payload)
        candidate["model_execution"] = {
            "real_model_execution": True, "wall_seconds": 1.0, "input_tokens": 100,
            "cached_input_tokens": 0, "output_tokens": 20, "reasoning_output_tokens": 5,
            "repeated_reads": 0, "failure": False, "timeout": False,
            "provider": "fixture", "model": "fixture",
        }
        return candidate

    def _complete_shadow(self, shadow, candidate=None):
        adapter.mark_preimage_visual_shadow_running(self.ep, shadow["request_id"], worker_id="visual-runner")
        return adapter.complete_preimage_visual_shadow_task(
            self.ep, shadow["request_id"], candidate or self._candidate(shadow))

    def test_shadow_off_leaves_canonical_request_set_unchanged(self):
        with patch.object(adapter, "visual_narrative_prepare_shadow_enabled", return_value=False):
            response = adapter.build_request(self.ep, runtime="WORK", mode="full_auto", resume=True, source="off")
        self.assertEqual(len(response["requests"]), 4)
        self.assertNotIn("shadow_requests", response)

    def test_shadow_request_is_separate_and_does_not_change_canonical_count_or_pointer(self):
        response, shadow, _legacy = self._requests()
        pointer = adapter._read_current_request(self.ep)["request_id"]
        self.assertEqual(len(response["requests"]), 4)
        self.assertEqual(len(response["shadow_requests"]), 1)
        self.assertEqual(adapter._read_current_request(self.ep)["request_id"], pointer)
        self.assertTrue(shadow["shadow"])
        self.assertFalse(shadow["agent_execution"]["allowed_writes"])
        self.assertTrue(shadow["host_contract"]["not_canonical_preimage_concurrency"])

    def test_shadow_cannot_use_canonical_start_or_completion(self):
        _response, shadow, _legacy = self._requests()
        with self.assertRaisesRegex(ValueError, "start-preimage-shadow"):
            adapter.mark_preimage_task_running(self.ep, shadow["request_id"], worker_id="wrong")
        with self.assertRaisesRegex(ValueError, "complete-preimage-shadow"):
            adapter.complete_preimage_task(self.ep, shadow["request_id"], self._candidate(shadow))

    def test_duplicate_dispatch_crash_resume_and_shadow_live_domain_isolation(self):
        _response, shadow, _legacy = self._requests()
        started = adapter.mark_preimage_visual_shadow_running(self.ep, shadow["request_id"], worker_id="visual-runner")
        resumed = adapter.mark_preimage_visual_shadow_running(self.ep, shadow["request_id"], worker_id="visual-runner")
        record = execution.begin_execution(self.ep, snapshot_id=shadow["task"]["snapshot_id"],
            task_id=shadow["task"]["task_id"], execution_id="visual-live-test", attempt=1,
            idempotency_key="visual-live-test", shadow=False)
        self.assertEqual(started["agent_execution"]["execution_id"], resumed["agent_execution"]["execution_id"])
        self.assertEqual(record["status"], "ACTIVE")
        self.assertFalse(record["shadow"])
        with self.assertRaisesRegex(RuntimeError, "ALREADY_RUNNING"):
            adapter.mark_preimage_visual_shadow_running(self.ep, shadow["request_id"], worker_id="other")
        again, same, _ = self._requests()
        self.assertEqual(same["request_id"], shadow["request_id"])
        self.assertEqual(len([r for r in host_request_persistence.list_all(self.ep)
                              if r.get("shadow_kind") == "VISUAL_NARRATIVE_PREPARE_AGENT"]), 1)
        self.assertEqual(len(again["requests"]), 4)

    def test_shadow_completion_is_idempotent_and_metrics_pointer_are_isolated(self):
        _response, shadow, _legacy = self._requests()
        pointer = adapter._read_current_request(self.ep)["request_id"]
        metrics_before = adapter.preimage_execution_metrics(self.ep)
        candidate = self._candidate(shadow)
        first = self._complete_shadow(shadow, candidate)
        replay = adapter.complete_preimage_visual_shadow_task(self.ep, shadow["request_id"], candidate)
        self.assertEqual(first["status"], "FINALIZED")
        self.assertEqual(replay["status"], "FINALIZED")
        self.assertEqual(adapter._read_current_request(self.ep)["request_id"], pointer)
        metrics_after = adapter.preimage_execution_metrics(self.ep)
        self.assertEqual(metrics_after["requested"], metrics_before["requested"])
        self.assertEqual(metrics_after["started"], metrics_before["started"])
        self.assertFalse(adapter.visual_narrative_shadow_metrics(self.ep)["canonical_preimage_concurrency_included"])
        changed = self._candidate(shadow)
        changed["payload"]["visual.narrative_core"]["climax_frame"] = 999
        with self.assertRaisesRegex(ValueError, "ALREADY_FINALIZED_DIFFERENT_CANDIDATE"):
            adapter.complete_preimage_visual_shadow_task(self.ep, shadow["request_id"], changed)

    def test_invalid_candidate_fails_closed_and_never_writes_legacy_path_or_authority(self):
        _response, shadow, _legacy = self._requests()
        before = json.loads((self.ep / "meta/story-gates.json").read_text(encoding="utf-8"))
        candidate = self._candidate(shadow)
        candidate["payload"] = {"wrong.scope": {"bad": True}}
        failed = self._complete_shadow(shadow, candidate)
        self.assertEqual(failed["status"], "FAILED")
        self.assertTrue(failed["candidate_errors"])
        self.assertFalse((self.ep / shadow["task"]["candidate_output"]).exists())
        self.assertEqual(json.loads((self.ep / "meta/story-gates.json").read_text(encoding="utf-8")), before)
        self.assertEqual(json.loads((self.ep / "meta/episode-state.json").read_text(encoding="utf-8"))["current_state"],
                         "STORYBOARD_LOCKED")

    def _compare_in_order(self, legacy_first):
        _response, shadow, legacy = self._requests()
        gates_before = (self.ep / "meta/story-gates.json").read_bytes()
        if legacy_first:
            adapter.mark_preimage_task_running(self.ep, legacy["request_id"], worker_id="legacy")
            adapter.complete_preimage_task(self.ep, legacy["request_id"], self._candidate(legacy, shadow))
        done = self._complete_shadow(shadow)
        if not legacy_first:
            self.assertEqual(done["comparison_status"], "WAITING_FOR_LEGACY")
            adapter.mark_preimage_task_running(self.ep, legacy["request_id"], worker_id="legacy")
            adapter.complete_preimage_task(self.ep, legacy["request_id"], self._candidate(legacy, shadow))
        final = host_request_persistence.load(self.ep, shadow["request_id"])
        self.assertEqual(final["comparison_status"], "COMPARED")
        self.assertTrue(final["shadow_comparison"]["domain_semantic"]["semantic_equivalent"])
        self.assertEqual((self.ep / "meta/story-gates.json").read_bytes(), gates_before)
        self.assertIsInstance(final.get("shadow_candidate"), dict)
        self.assertEqual(final["shadow_candidate"]["task_id"], shadow["task"]["task_id"])

    def test_legacy_first_then_shadow_comparison(self):
        self._compare_in_order(True)

    def test_shadow_first_then_legacy_comparison(self):
        self._compare_in_order(False)


if __name__ == "__main__":
    unittest.main()
