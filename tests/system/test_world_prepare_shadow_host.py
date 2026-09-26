from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import host_request_persistence
import preimage_execution_persistence as execution
import preimage_task_contract as tasks
import product_runtime_adapter as adapter
import storyos_config


class WorldPrepareShadowHostTest(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / ".storyos-tmp"
        self.base.mkdir(exist_ok=True)
        self.raw = tempfile.mkdtemp(prefix="world-shadow-", dir=self.base)
        self.ep = Path(self.raw)
        (self.ep / "meta").mkdir()
        (self.ep / "meta/episode-state.json").write_text(
            '{"current_state":"STORYBOARD_LOCKED"}', encoding="utf-8"
        )
        (self.ep / "meta/story-gates.json").write_text(
            '{"story":{"locked":true},"visual":{}}', encoding="utf-8"
        )
        (self.ep / "meta/world-state.json").write_text(
            '{"status":"LOCKED","initial_state":{"characters":{"P01":{"clothing_anchor":"dark coat"}}},"frames":{}}',
            encoding="utf-8",
        )
        (self.ep / "meta/temporal-continuity.json").write_text(
            '{"status":"LOCKED","frames":{},"rules":{"time_continuity":"preserve"}}',
            encoding="utf-8",
        )
        self.old_meta = host_request_persistence.storage_config.episode_meta_store_config
        self.old_mode = execution.mode
        host_request_persistence.storage_config.episode_meta_store_config = lambda: {"mode": "json"}
        execution.mode = lambda: "json"
        self.flags = patch.object(adapter, "world_prepare_shadow_enabled", return_value=True), patch.object(
            adapter, "world_prepare_production_enabled", return_value=False
        ), patch.object(adapter, "character_finalize_shadow_enabled", return_value=False)
        for item in self.flags:
            item.start()

    def tearDown(self):
        for item in reversed(self.flags):
            item.stop()
        host_request_persistence.storage_config.episode_meta_store_config = self.old_meta
        execution.mode = self.old_mode
        shutil.rmtree(self.raw, ignore_errors=True)

    def _build(self):
        return adapter.build_request(
            self.ep, runtime="WORK", mode="full_auto", resume=True, source="world-shadow-test"
        )

    def _requests(self):
        response = self._build()
        shadow = next(row for row in response["shadow_requests"] if row["shadow_kind"] == "WORLD_PREPARE_AGENT")
        legacy = next(row for row in response["requests"] if row["task"]["task_type"] == "WORLD_PREPARE")
        return response, shadow, legacy

    def _candidate(self, request):
        task = request["task"]
        payload = tasks.valid_payload(task)
        capsule = (task.get("input_contract") or {}).get("world_prepare_capsule") or {}
        obligations = capsule.get("obligations") or {}
        for scope, frozen in (obligations.get("scopes") or {}).items():
            if isinstance(frozen, dict) and frozen:
                payload[scope] = frozen
            elif not isinstance(payload.get(scope), dict) or payload[scope].get("applicable") is False:
                payload[scope] = {"generated_from_empty_frozen_scope": True}
        candidate = tasks.candidate_template(task, payload)
        candidate["model_execution"] = {
            "real_model_execution": True, "wall_seconds": 1.0,
            "input_tokens": 100, "cached_input_tokens": 0,
            "output_tokens": 20, "reasoning_output_tokens": 5,
            "repeated_reads": 0, "failure": False, "timeout": False,
            "provider": "test", "model": "test-model",
        }
        return candidate

    def _complete_shadow(self, shadow):
        adapter.mark_preimage_world_shadow_running(self.ep, shadow["request_id"], worker_id="runner-world-1")
        return adapter.complete_preimage_world_shadow_task(
            self.ep, shadow["request_id"], self._candidate(shadow)
        )

    def test_shadow_disabled_preserves_legacy_request_shape(self):
        with patch.object(adapter, "world_prepare_shadow_enabled", return_value=False):
            response = adapter.build_request(
                self.ep, runtime="WORK", mode="full_auto", resume=True, source="world-shadow-off"
            )
        self.assertEqual(len(response["requests"]), 4)
        self.assertNotIn("shadow_requests", response)

    def test_shadow_enabled_adds_separate_request_without_changing_canonical_count(self):
        response, shadow, _legacy = self._requests()
        self.assertEqual(len(response["requests"]), 4)
        self.assertEqual(len(response["shadow_requests"]), 1)
        self.assertTrue(shadow["shadow"])
        self.assertEqual(shadow["next_step"], "PREIMAGE_WORLD_PREPARE_SHADOW")
        self.assertFalse(shadow["agent_execution"]["allowed_writes"])
        self.assertTrue(shadow["host_contract"]["must_not_write_shared_authority"])

    def test_shadow_isolation_preserves_current_pointer_and_canonical_metrics(self):
        response, shadow, _legacy = self._requests()
        pointer_before = adapter._read_current_request(self.ep)["request_id"]
        before = adapter.preimage_execution_metrics(self.ep)
        self._complete_shadow(shadow)
        self.assertEqual(adapter._read_current_request(self.ep)["request_id"], pointer_before)
        after = adapter.preimage_execution_metrics(self.ep)
        self.assertEqual(after["requested"], before["requested"])
        self.assertEqual(after["started"], 0)
        self.assertEqual(len(response["requests"]), 4)
        self.assertFalse((self.ep / shadow["task"]["candidate_output"]).exists())

    def test_duplicate_dispatch_and_resume_reuse_single_shadow_execution(self):
        _response, shadow, _legacy = self._requests()
        running = adapter.mark_preimage_world_shadow_running(
            self.ep, shadow["request_id"], worker_id="runner-world-1"
        )
        replay = adapter.mark_preimage_world_shadow_running(
            self.ep, shadow["request_id"], worker_id="runner-world-1"
        )
        second_response, second_shadow, _legacy2 = self._requests()
        self.assertEqual(second_shadow["request_id"], shadow["request_id"])
        self.assertEqual(running["agent_execution"]["execution_id"], replay["agent_execution"]["execution_id"])
        self.assertEqual(len([r for r in host_request_persistence.list_all(self.ep) if r.get("shadow_kind") == "WORLD_PREPARE_AGENT"]), 1)
        with self.assertRaisesRegex(RuntimeError, "ALREADY_RUNNING"):
            adapter.mark_preimage_world_shadow_running(self.ep, shadow["request_id"], worker_id="new-runner")
        self.assertEqual(len(second_response["requests"]), 4)

    def test_shadow_cannot_use_canonical_start_or_completion(self):
        _response, shadow, _legacy = self._requests()
        with self.assertRaisesRegex(ValueError, "start-preimage-shadow"):
            adapter.mark_preimage_task_running(self.ep, shadow["request_id"], worker_id="bad")
        with self.assertRaisesRegex(ValueError, "complete-preimage-shadow"):
            adapter.complete_preimage_task(self.ep, shadow["request_id"], self._candidate(shadow))

    def test_world_adapter_and_legacy_attempt_domains_do_not_collide(self):
        _response, shadow, _legacy = self._requests()
        meta = shadow["agent_execution"]
        world_record = execution.begin_execution(
            self.ep, snapshot_id=shadow["task"]["snapshot_id"], task_id=shadow["task"]["task_id"],
            execution_id=meta["execution_id"], attempt=1, idempotency_key=meta["idempotency_key"], shadow=True,
        )
        live_record = execution.begin_execution(
            self.ep, snapshot_id=shadow["task"]["snapshot_id"], task_id=shadow["task"]["task_id"],
            execution_id="exec_world_live_domain", attempt=1, idempotency_key="idem_world_live_domain", shadow=False,
        )
        self.assertEqual(world_record["status"], "ACTIVE")
        self.assertEqual(live_record["status"], "ACTIVE")
        self.assertTrue(world_record["shadow"])
        self.assertFalse(live_record["shadow"])

    def test_invalid_shadow_candidate_fails_closed_without_legacy_candidate_write(self):
        _response, shadow, _legacy = self._requests()
        candidate = self._candidate(shadow)
        candidate["payload"] = {"wrong.scope": {"value": "invalid"}}
        adapter.mark_preimage_world_shadow_running(self.ep, shadow["request_id"], worker_id="runner-world-1")
        failed = adapter.complete_preimage_world_shadow_task(self.ep, shadow["request_id"], candidate)
        self.assertEqual(failed["status"], "FAILED")
        self.assertTrue(failed["candidate_errors"])
        self.assertFalse((self.ep / shadow["task"]["candidate_output"]).exists())
        self.assertFalse((self.ep / "meta/episode-state.json").read_text(encoding="utf-8").find("IMAGE_PRODUCTION") >= 0)

    def test_legacy_first_then_shadow_comparison_and_authority_sha_unchanged(self):
        _response, shadow, legacy = self._requests()
        snapshot_path = self.ep / "meta/runtime/preimage-authority-snapshot.json"
        frozen_before = json.loads(snapshot_path.read_text(encoding="utf-8"))["authority_sha256"]
        legacy_candidate = self._candidate(shadow)
        adapter.mark_preimage_task_running(self.ep, legacy["request_id"], worker_id="legacy-world")
        legacy_candidate["task_id"] = legacy["task"]["task_id"]
        legacy_candidate["snapshot_id"] = legacy["task"]["snapshot_id"]
        adapter.complete_preimage_task(self.ep, legacy["request_id"], legacy_candidate)
        done = self._complete_shadow(shadow)
        self.assertEqual(done["comparison_status"], "COMPARED")
        self.assertTrue(done["shadow_comparison"]["structural_equal"])
        self.assertEqual(json.loads(snapshot_path.read_text(encoding="utf-8"))["authority_sha256"], frozen_before)
        record = execution.find_execution(
            self.ep, shadow["task"]["snapshot_id"], shadow["task"]["task_id"],
            shadow["agent_execution"]["execution_id"],
        )
        self.assertEqual(record["status"], "SHADOW_COMPLETED")
        self.assertTrue(record["shadow"])

    def test_shadow_first_then_legacy_comparison(self):
        _response, shadow, legacy = self._requests()
        done = self._complete_shadow(shadow)
        self.assertEqual(done["comparison_status"], "WAITING_FOR_LEGACY")
        adapter.mark_preimage_task_running(self.ep, legacy["request_id"], worker_id="legacy-world")
        legacy_candidate = self._candidate(shadow)
        legacy_candidate["task_id"] = legacy["task"]["task_id"]
        legacy_candidate["snapshot_id"] = legacy["task"]["snapshot_id"]
        adapter.complete_preimage_task(self.ep, legacy["request_id"], legacy_candidate)
        refreshed = host_request_persistence.load(self.ep, shadow["request_id"])
        self.assertEqual(refreshed["comparison_status"], "COMPARED")


if __name__ == "__main__":
    unittest.main()


def test_world_feature_defaults_shadow_on_and_production_off():
    cfg = storyos_config.load_config()
    adapters = storyos_config.get_path(cfg, "agent_runtime.adapters", {})
    assert adapters["world_prepare"]["shadow_enabled"] is True
    assert adapters["world_prepare"]["production_enabled"] is False
