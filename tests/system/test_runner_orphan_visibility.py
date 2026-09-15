#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2.6.1.1: an idle host loop must be visible, and nothing here may restart one.

2026-09-14 尸解仙: the engine wrote HOST_WAIT at 17:49:37 and was never resumed.
Nothing noticed, because no production module ever read the runner lifecycle
evidence that episode_runner.py had already written. These tests pin both halves
of the fix -- the projection reports IDLE honestly, and neither module gains the
ability to act on it.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import next_action
import runner_health_monitor
import runner_state_store

# Code-level capabilities only. The docstrings deliberately say "no watchdog", so a
# naive word scan would fire on the promise instead of on a violation of it.
FORBIDDEN_TOKENS = (
    "acquire_lock",
    "release_lock",
    "runner_state_store.save",
    "runner_state_store.acquire_lock",
    "runner_state_store.release_lock",
    "runner_state_store.mark_",
    "threading.",
    "subprocess.",
    "os.system",
    "signal.",
    "time.sleep",
)

# runner_health_monitor is allowed exactly one contact with the store: a read.
READ_ONLY_TOKENS = ("runner_state_store.load",)


class RunnerOrphanVisibilityTests(unittest.TestCase):

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="runner-orphan-")
        self.ep = Path(self._td.name)
        (self.ep / "meta").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_no_runner_state_reads_unknown_and_idle(self) -> None:
        state = runner_health_monitor.check(self.ep)
        self.assertEqual(state["status"], "UNKNOWN")
        self.assertEqual(state["host_loop"], "IDLE")
        self.assertEqual(state["host_loop_source"], "meta/runtime-runner-state.json")
        self.assertIsNone(state["runner_status"])

    def test_fresh_heartbeat_is_the_only_thing_that_reads_running(self) -> None:
        runner_state_store.save(self.ep, status="RUNNING", pid=1)
        state = runner_health_monitor.check(self.ep)
        self.assertEqual(state["status"], "HEALTHY")
        self.assertEqual(state["host_loop"], "RUNNING")

    def test_new_running_epoch_clears_previous_terminal_diagnostics(self) -> None:
        runner_state_store.save(
            self.ep, status="TECH_FAILED", pid=123, return_code=21,
            last_error="old failure", last_action="RETRY", error="old exception", attempt=3,
        )
        row = runner_state_store.save(self.ep, status="RUNNING", pid=456, resume_enabled=True)
        self.assertEqual(row["status"], "RUNNING")
        self.assertEqual(row["pid"], 456)
        for stale in ("return_code", "last_error", "last_action", "error", "attempt"):
            self.assertNotIn(stale, row)

    def test_terminal_status_is_idle_even_with_a_fresh_heartbeat(self) -> None:
        # save() stamps a heartbeat on every call, so each of these rows carries a
        # heartbeat seconds old -- and still nobody is running the loop. This is the
        # whole point: HEALTHY is the only status that proves a live loop.
        for status in ("HOST_WAIT", "COMPLETED", "CAPABILITY_WAIT", "HUMAN_REQUIRED",
                       "HARD_STOP", "YIELDED"):
            with self.subTest(status=status):
                runner_state_store.save(self.ep, status=status, pid=1)
                state = runner_health_monitor.check(self.ep)
                self.assertEqual(state["runner_status"], status)
                self.assertEqual(state["host_loop"], "IDLE")

    def test_stale_heartbeat_reads_recovery_required_and_idle(self) -> None:
        with mock.patch.object(runner_state_store, "_now",
                               return_value="2020-01-01T00:00:00+00:00"):
            runner_state_store.save(self.ep, status="RUNNING", pid=1)
        state = runner_health_monitor.check(self.ep)
        self.assertEqual(state["status"], "RECOVERY_REQUIRED")
        self.assertEqual(state["host_loop"], "IDLE")

    def test_naive_heartbeat_stamp_does_not_crash_the_projection(self) -> None:
        # Hand-written evidence predating the current stamp format.
        (self.ep / runner_state_store.REL).write_text(json.dumps({
            "status": "RUNNING", "pid": 1, "heartbeat": "2020-01-01T00:00:00",
        }), encoding="utf-8")
        state = runner_health_monitor.check(self.ep)
        self.assertEqual(state["status"], "RECOVERY_REQUIRED")
        self.assertEqual(state["host_loop"], "IDLE")

    def test_orphaned_pending_work_is_true_when_work_is_owed_and_nothing_runs(self) -> None:
        data = next_action.apply_runtime_block_semantics(
            {"action": "PREIMAGE_COMPILE", "host_loop": "IDLE"}
        )
        self.assertTrue(data["work_pending"])
        self.assertTrue(data["orphaned_pending_work"])
        # Visible, never blocking: the episode still needs a human to start the driver.
        self.assertFalse(data["hard_stop"])
        self.assertFalse(data["blocking"])
        self.assertEqual(data["host_loop"], "IDLE")

    def test_orphaned_pending_work_is_false_while_a_loop_runs(self) -> None:
        data = next_action.apply_runtime_block_semantics(
            {"action": "PREIMAGE_COMPILE", "host_loop": "RUNNING"}
        )
        self.assertFalse(data["orphaned_pending_work"])

    def test_orphaned_pending_work_is_false_when_nothing_is_owed(self) -> None:
        data = next_action.apply_runtime_block_semantics(
            {"action": "COMPLETE", "host_loop": "IDLE"}
        )
        self.assertFalse(data["work_pending"])
        self.assertFalse(data["orphaned_pending_work"])

    def test_host_loop_defaults_to_idle_when_projection_is_silent(self) -> None:
        data = next_action.apply_runtime_block_semantics({"action": "PREIMAGE_COMPILE"})
        self.assertEqual(data["host_loop"], "IDLE")
        self.assertTrue(data["orphaned_pending_work"])

    def test_host_loop_helper_falls_back_to_idle_instead_of_raising(self) -> None:
        with mock.patch.object(next_action.runner_health_monitor, "check",
                               side_effect=RuntimeError("unreadable evidence")):
            projected = next_action.host_loop(self.ep)
        self.assertEqual(projected["host_loop"], "IDLE")
        self.assertIsNone(projected["runner_status"])

    def test_no_production_module_can_act_on_a_runner(self) -> None:
        """No watchdog: the projection reports, it never starts/stops/waits."""
        sources = {
            name: (ROOT / "episodes/_system" / name).read_text(encoding="utf-8")
            for name in ("next_action.py", "runner_health_monitor.py")
        }
        for name, text in sources.items():
            with self.subTest(module=name):
                for token in FORBIDDEN_TOKENS:
                    self.assertNotIn(
                        token, text,
                        f"{name} must not be able to start, stop, signal or wait on a runner",
                    )
        self.assertNotIn(
            "runner_state_store", sources["next_action.py"],
            "next_action must project runner health, never read the store itself",
        )
        self.assertIn(READ_ONLY_TOKENS[0], sources["runner_health_monitor.py"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
