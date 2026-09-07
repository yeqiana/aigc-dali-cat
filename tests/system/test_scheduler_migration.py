#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import scheduler_core
import batch_scheduler
import image_scheduler


class SchedulerMigrationTests(unittest.TestCase):
    """B1 guard: both lanes consume scheduler_core primitives."""

    def source(self, module) -> str:
        return Path(module.__file__).read_text(encoding="utf-8-sig")

    def test_queue_transaction_is_shared_object(self):
        self.assertIs(image_scheduler.queue_transaction,
                      scheduler_core.queue_transaction)
        self.assertIs(image_scheduler.QueueMutationBusy,
                      scheduler_core.QueueMutationBusy)

    def test_image_lane_delegates_queue_io(self):
        src = self.source(image_scheduler)
        self.assertNotIn("def queue_transaction(", src)
        self.assertIn("scheduler_core.load_queue(ep", src)
        self.assertIn("scheduler_core.save_queue(ep,q)", src)

    def test_batch_lane_delegates_queue_and_ledger_io(self):
        src = self.source(batch_scheduler)
        self.assertIn("scheduler_core.load_queue(ep)", src)
        self.assertIn("scheduler_core.save_queue(ep,q)", src)
        self.assertIn("scheduler_core.ledger_begin(", src)
        self.assertIn("scheduler_core.ledger_success(", src)
        self.assertIn("scheduler_core.ledger_tech_fail(", src)
        self.assertIn("scheduler_core.current_contract_sha(", src)

    def test_no_private_portability_guard_duplicates(self):
        for module in (image_scheduler, batch_scheduler):
            self.assertNotIn("production queue portability guard failed",
                             self.source(module))


if __name__ == "__main__":
    unittest.main()
