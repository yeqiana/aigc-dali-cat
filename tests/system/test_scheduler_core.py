#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
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

    def test_empty_queue_roundtrip(self):
        q = scheduler_core.empty_queue(max_parallel=3)
        scheduler_core.save_queue(self.ep, q)
        loaded = scheduler_core.load_queue(self.ep)
        self.assertEqual(loaded["max_parallel"], 3)
        self.assertEqual(loaded["schema_version"], 1)
        self.assertEqual(loaded["items"], [])

    def test_portability_guard_rejects_escaped_path(self):
        q = scheduler_core.empty_queue()
        q["items"] = [{"frame": 1, "prompt_file": "D:/repo/episodes/x/a.png"}]
        scheduler_core.save_queue(self.ep, q)
        with self.assertRaises(ValueError):
            scheduler_core.load_queue(self.ep)

    def test_queue_transaction_serializes(self):
        with scheduler_core.queue_transaction(self.ep):
            q = scheduler_core.load_queue(self.ep)
            q["items"].append({"frame": 1})
            scheduler_core.save_queue(self.ep, q)
        with self.assertRaises(scheduler_core.QueueMutationBusy):
            with scheduler_core.queue_transaction(self.ep):
                with scheduler_core.queue_transaction(self.ep):
                    pass

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


if __name__ == "__main__":
    unittest.main()
