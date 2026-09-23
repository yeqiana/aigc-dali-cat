#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
import asyncio
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import scheduler_core


class SchedulerCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="scheduler-core-test-")
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)

    def test_missing_queue_returns_empty(self):
        q = scheduler_core.load_queue(self.ep)
        self.assertEqual(q, scheduler_core.EMPTY_QUEUE)

    def test_execution_loop_honors_five_worker_cap(self):
        active = 0
        peak = 0

        async def handler(_task):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.03)
            active -= 1
            return {"ok": True}

        async def consume(_event):
            return "success"

        tasks = [{"id": str(index)} for index in range(6)]
        asyncio.run(scheduler_core.run_execution_loop(
            tasks, handler, consume, workers=6))
        self.assertEqual(peak, 5)

    def test_execution_loop_restores_one_slot_after_two_successes(self):
        statuses = ["tech_failed", "generated", "generated", "tech_failed",
                    "blocked", "generated", "generated"]
        reported_caps = []
        dispatched_caps = []

        async def handler(_task):
            return {"ok": True}

        async def consume(_event):
            return statuses.pop(0)

        async def completed(_event, _status, _active, cap):
            reported_caps.append(cap)

        async def dispatched(_row, _active, cap):
            dispatched_caps.append(cap)

        tasks = [{"id": str(index)} for index in range(7)]
        asyncio.run(scheduler_core.run_execution_loop(
            tasks, handler, consume, workers=3,
            completed=completed, dispatched=dispatched))
        self.assertEqual(reported_caps, [2, 2, 3, 2, 2, 2, 3])
        self.assertIn(3, dispatched_caps[3:])

    def test_execution_loop_failure_floor_and_new_run_reset(self):
        async def handler(_task):
            return {"ok": True}

        async def run_with(statuses):
            caps = []

            async def consume(_event):
                return statuses.pop(0)

            async def completed(_event, _status, _active, cap):
                caps.append(cap)

            tasks = [{"id": str(index)} for index in range(len(statuses))]
            await scheduler_core.run_execution_loop(
                tasks, handler, consume, workers=3, completed=completed)
            return caps

        self.assertEqual(asyncio.run(run_with(["tech_failed"] * 4)), [2, 1, 1, 1])
        self.assertEqual(asyncio.run(run_with(["generated"])), [3])

    def test_empty_queue_roundtrip(self):
        q = scheduler_core.empty_queue(max_parallel=5)
        scheduler_core.save_queue(self.ep, q)
        loaded = scheduler_core.load_queue(self.ep)
        self.assertEqual(loaded["max_parallel"], 5)
        self.assertEqual(loaded["schema_version"], 1)
        self.assertEqual(loaded["items"], [])

    def test_portability_guard_rejects_escaped_path(self):
        q = scheduler_core.empty_queue()
        q["items"] = [{"frame": 1, "prompt_file": "D:/repo/episodes/x/a.png"}]
        scheduler_core.save_queue(self.ep, q)
        with self.assertRaises(ValueError):
            scheduler_core.load_queue(self.ep)

    def test_queue_transaction_is_same_thread_reentrant(self):
        with scheduler_core.queue_transaction(self.ep):
            q = scheduler_core.load_queue(self.ep)
            q["items"].append({"frame": 1})
            with scheduler_core.queue_transaction(self.ep):
                scheduler_core.save_queue(self.ep, q)
        self.assertEqual(scheduler_core.load_queue(self.ep)["items"][0]["frame"], 1)

    def test_save_queue_fails_when_foreign_lock_is_held(self):
        import runner_state_store
        self.assertTrue(runner_state_store.acquire_lock(
            self.ep, lock_rel=scheduler_core.SCHEDULER_LOCK_REL))
        try:
            with self.assertRaises(scheduler_core.QueueMutationBusy):
                scheduler_core.save_queue(self.ep, scheduler_core.empty_queue())
        finally:
            runner_state_store.release_lock(
                self.ep, lock_rel=scheduler_core.SCHEDULER_LOCK_REL)

    def test_ledger_state_defaults_pending(self):
        self.assertEqual(scheduler_core.ledger_state(self.ep, 1), "PENDING")

    def test_ready_items_scope_and_order(self):
        import production_ledger

        ready_state = next(iter(production_ledger.READY_LEDGER_STATES))
        q = scheduler_core.empty_queue()
        q["items"] = [
            {"frame": 2, "scope": "batch", "status": "queued",
             "priority": 1, "depends_on": [1]},
            {"frame": 1, "scope": "batch", "status": "queued",
             "priority": 5, "depends_on": []},
            {"frame": 3, "scope": "visual_lock", "status": "queued",
             "priority": 9, "depends_on": []},
        ]
        scheduler_core.write_json(
            self.ep / "meta/production-ledger.json",
            {"frames": {"01": {"status": ready_state}}},
        )
        batch = scheduler_core.ready_items(self.ep, q, scope="batch")
        self.assertEqual([int(x["frame"]) for x in batch], [1, 2])
        all_items = scheduler_core.ready_items(self.ep, q)
        self.assertEqual([int(x["frame"]) for x in all_items], [3, 1, 2])

    def test_current_contract_sha_delegates_provenance(self):
        import sys

        fake = mock.MagicMock()
        fake.provenance.return_value = {"contract_sha256": "abc123"}
        with mock.patch.dict(sys.modules, {"frame_contract": fake}):
            self.assertEqual(scheduler_core.current_contract_sha(self.ep, 1),
                             "abc123")
        fake.provenance.return_value = None
        with mock.patch.dict(sys.modules, {"frame_contract": fake}):
            with self.assertRaises(ValueError):
                scheduler_core.current_contract_sha(self.ep, 1)

    def test_ledger_success_rejects_backend_contract_drift(self):
        # S4: a worker result bound to a stale Frame Contract must never be
        # committed as if it matched the currently resolved contract.
        import sys

        item = {
            "id": "drift-item", "frame": 1, "kind": "original",
            "model": "gpt-image-2", "quality": "high",
            "frame_contract": {"contract_sha256": "stale-sha"},
        }
        result = {
            "output": str(self.ep / "candidate.png"),
            "payload": {
                "image_model": {"model": "gpt-image-2", "quality": "high"},
                "frame_contract": {"contract_sha256": "stale-sha"},
            },
        }
        fake_ledger = mock.Mock()
        with mock.patch.object(scheduler_core, "current_contract_sha",
                               return_value="current-sha"), \
             mock.patch.dict(sys.modules, {"ledger_call": fake_ledger}):
            ok, message = scheduler_core.ledger_success(self.ep, item, result)
        self.assertFalse(ok)
        self.assertIn("backend frame contract drift", message)
        self.assertIn("stale-sha", message)
        self.assertIn("current-sha", message)
        fake_ledger.success.assert_not_called()

    def test_ledger_success_accepts_matching_current_contract(self):
        import sys

        item = {
            "id": "fresh-item", "frame": 1, "kind": "original",
            "model": "gpt-image-2", "quality": "high",
            "frame_contract": {"contract_sha256": "current-sha"},
        }
        result = {
            "output": str(self.ep / "candidate.png"),
            "payload": {
                "image_model": {"model": "gpt-image-2", "quality": "high"},
                "frame_contract": {"contract_sha256": "current-sha"},
            },
        }
        fake_ledger = mock.Mock()
        fake_ledger.success.return_value = (True, "")
        with mock.patch.object(scheduler_core, "current_contract_sha",
                               return_value="current-sha"), \
             mock.patch.dict(sys.modules, {"ledger_call": fake_ledger}):
            ok, message = scheduler_core.ledger_success(self.ep, item, result)
        self.assertTrue(ok, message)
        fake_ledger.success.assert_called_once()


if __name__ == "__main__":
    unittest.main()
