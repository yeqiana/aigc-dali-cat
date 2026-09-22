from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import incremental_closure


class IncrementalClosureFailClosedTests(unittest.TestCase):
    def make_episode(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        td = tempfile.TemporaryDirectory(prefix="incremental-fail-closed-", dir=base)
        ep = Path(td.name)
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        (ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8")
        (ep / "meta/story-gates.json").write_text(
            json.dumps({"subtitles": {"required": False}}), encoding="utf-8")
        (ep / "meta/production-ledger.json").write_text("{}", encoding="utf-8")
        return td, ep

    def test_inner_frame_planner_error_is_outer_error_not_incremental_work(self):
        td, ep = self.make_episode()
        self.addCleanup(td.cleanup)
        inner = json.dumps({"action": "ERROR", "raw": "planner traceback"})
        with mock.patch.object(incremental_closure, "run", return_value=(0, inner)):
            result = incremental_closure.plan(ep)
        self.assertEqual(result["frames"], "ERROR")
        self.assertEqual(result["action"], "ERROR")
        self.assertEqual(result["frame_plan"]["raw"], "planner traceback")

    def test_nonzero_inner_planner_return_code_is_outer_error(self):
        td, ep = self.make_episode()
        self.addCleanup(td.cleanup)
        with mock.patch.object(incremental_closure, "run", return_value=(7, "traceback")):
            result = incremental_closure.plan(ep)
        self.assertEqual(result["frames"], "ERROR")
        self.assertEqual(result["action"], "ERROR")
        self.assertEqual(result["frame_plan"]["returncode"], 7)

    def test_cli_returns_nonzero_when_plan_reports_error(self):
        td, ep = self.make_episode()
        self.addCleanup(td.cleanup)
        with mock.patch.object(incremental_closure, "plan", return_value={"action": "ERROR"}), \
             mock.patch.object(sys, "argv", ["incremental_closure.py", "plan", str(ep), "--json"]):
            self.assertEqual(incremental_closure.main(), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
