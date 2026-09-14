"""Regression tests for the Runtime DAG --until stop target (STORY_OS_V262_DAG_STOP_TARGET).

--until exists so a bounded experiment can end on a chosen canonical stage instead of running
the whole DAG. The properties worth pinning:

1. it never reports "reached" for a stage the gates have not accepted (fail-closed);
2. it does not report "reached" for a stage whose step did not succeed;
3. when it does stop, no further step is dispatched.

The predicate tests use the real function and the real gate call. The wiring tests stub the
per-step execution and side-effect writers so they assert scheduling/stop behaviour only;
those writers have their own coverage elsewhere. The episode lives under episodes/_tests so the
real repo-relative paths in product_runtime_adapter still resolve, matching the sandbox pattern
already used by episodes/_system/test_v211_performance_regression.py.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import runtime_dag
import workflow_step_protocol as proto


def write_state(ep: Path, state: str) -> None:
    path = ep / "meta/episode-state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"current_state": state}), encoding="utf-8")


def spec(step_id, target_state, *, depends_on=()):
    return proto.StepSpec(step_id=step_id, executor="scoped_model", depends_on=tuple(depends_on),
                          covers=(), target_state=target_state, evidence_paths=(), expensive=True)


class StopTargetPredicateTest(unittest.TestCase):
    """stop_target_reached: the cheap state read first, then the real gate decision."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="storyos-until-")
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)

    def test_arrived_and_gates_pass_is_reached(self):
        write_state(self.ep, "PRODUCTION_PASSED")
        with patch.object(runtime_dag, "validate_target", return_value=(True, "PASS")) as gates:
            self.assertEqual(runtime_dag.stop_target_reached(self.ep, "PRODUCTION_PASSED"),
                             (True, "PASS"))
            gates.assert_called_once_with(self.ep, "PRODUCTION_PASSED")

    def test_below_target_does_not_spawn_the_gates(self):
        """The state read is cheap and runs first; the three gate subprocesses must not."""
        write_state(self.ep, "VISUAL_CALIBRATED")
        with patch.object(runtime_dag, "validate_target") as gates:
            reached, detail = runtime_dag.stop_target_reached(self.ep, "PRODUCTION_PASSED")
            gates.assert_not_called()
        self.assertFalse(reached)
        self.assertIn("VISUAL_CALIBRATED", detail)

    def test_gate_rejection_is_not_a_stop(self):
        """Reaching the state is not enough: an unvalidated stage must not stop the DAG."""
        write_state(self.ep, "PRODUCTION_PASSED")
        with patch.object(runtime_dag, "validate_target", return_value=(False, "frame 07 missing")):
            reached, detail = runtime_dag.stop_target_reached(self.ep, "PRODUCTION_PASSED")
        self.assertFalse(reached)
        self.assertIn("frame 07 missing", detail)

    def test_earlier_canonical_stage_counts_as_arrived(self):
        """The stop is "at or past", so a target passed on the way is still a valid stop."""
        write_state(self.ep, "PUBLISH_READY")
        with patch.object(runtime_dag, "validate_target", return_value=(True, "PASS")):
            reached, _ = runtime_dag.stop_target_reached(self.ep, "PRODUCTION_PASSED")
        self.assertTrue(reached)

    def test_missing_state_file_is_not_a_stop(self):
        with patch.object(runtime_dag, "validate_target") as gates:
            reached, _ = runtime_dag.stop_target_reached(self.ep, "PRODUCTION_PASSED")
            gates.assert_not_called()
        self.assertFalse(reached)

    def test_unknown_stop_target_is_rejected_before_any_side_effect(self):
        """A step id is not a stage: --until PRODUCTION must never silently become a no-op."""
        write_state(self.ep, "IDEA_LOCKED")
        with self.assertRaises(ValueError) as caught:
            runtime_dag.execute(self.ep, until="PRODUCTION")
        self.assertIn("unknown runtime DAG stop target", str(caught.exception))
        self.assertEqual(list(self.ep.rglob("*.jsonl")), [], "rejection must precede any write")


class StopTargetWiringTest(unittest.TestCase):
    """execute(until=...): where the loop stops, and that it stays stopped.

    The stubbed worker advances meta/episode-state.json exactly as a real worker would, because
    stop_target_reached re-reads that file -- a step returning 0 while the state stays put is
    correctly NOT a stop, and one of the tests below pins that.
    """

    def setUp(self):
        # Under episodes/_tests: excluded from episode discovery, and inside ROOT so the real
        # repo-relative path handling in product_runtime_adapter still applies.
        (ROOT / "episodes/_tests").mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="storyos-until-", dir=ROOT / "episodes/_tests")
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)
        self.dispatched: list[str] = []
        self.rc_by_step: dict[str, int] = {}
        self.state_after_step: dict[str, str] = {}

        def fake_run_step(ep, step_id, **kwargs):
            self.dispatched.append(step_id)
            rc = self.rc_by_step.get(step_id, 0)
            if rc == 0 and step_id in self.state_after_step:
                write_state(ep, self.state_after_step[step_id])
            return rc, "stubbed"

        # Outside WORK/WEB the DAG takes the local executor branch, so a stubbed worker is
        # enough to drive the loop to a successful step without a real Codex run.
        for target, attr, value in (
            (runtime_dag, "reconcile_visual_profile_closure", lambda ep: None),
            (runtime_dag, "validate_target", lambda ep, name: (True, "mocked gates")),
            (runtime_dag.runtime_router, "detect", lambda: ("CODEX", {})),
            (runtime_dag.scoped_codex_worker, "run_step", fake_run_step),
            (runtime_dag.execution_capsule, "compile_capsule", lambda *a, **k: None),
            (runtime_dag.directing_quality, "after_step", lambda ep, step_id: []),
        ):
            patcher = patch.object(target, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _execute(self, steps, *, until):
        """Run execute() with a controlled step list; return (rc, stdout)."""
        buffer = io.StringIO()
        with patch.object(runtime_dag, "spec_rows", lambda: steps), \
             contextlib.redirect_stdout(buffer):
            rc = runtime_dag.execute(self.ep, until=until)
        return rc, buffer.getvalue()

    @staticmethod
    def _two_steps():
        return [spec("VISUAL_LOCK", "VISUAL_CALIBRATED"),
                spec("PRODUCTION", "PRODUCTION_PASSED", depends_on=("VISUAL_LOCK",))]

    def test_already_at_target_runs_no_step_at_all(self):
        """Arriving before the loop starts is a no-op, not a re-plan."""
        write_state(self.ep, "PRODUCTION_PASSED")
        rc, out = self._execute([spec("PRODUCTION", "PRODUCTION_PASSED")], until="PRODUCTION_PASSED")
        self.assertEqual(rc, 0)
        self.assertIn(runtime_dag.STOP_TARGET_REACHED, out)
        self.assertIn("already valid", out)
        self.assertEqual(self.dispatched, [], "no step may run once the target is already valid")

    def test_loop_stops_after_the_step_that_reaches_the_target(self):
        write_state(self.ep, "STORYBOARD_LOCKED")
        self.state_after_step = {"VISUAL_LOCK": "VISUAL_CALIBRATED",
                                 "PRODUCTION": "PRODUCTION_PASSED"}
        rc, out = self._execute(self._two_steps(), until="VISUAL_CALIBRATED")
        self.assertEqual(rc, 0)
        self.assertIn(runtime_dag.STOP_TARGET_REACHED, out)
        self.assertIn("after VISUAL_LOCK", out)
        self.assertEqual(self.dispatched, ["VISUAL_LOCK"], "PRODUCTION must not be dispatched")

    def test_loop_continues_while_the_target_is_not_yet_reached(self):
        """A target further along the canonical order must let the loop keep going, and the
        stop must land on the step that actually reaches it -- not on the first step."""
        write_state(self.ep, "STORYBOARD_LOCKED")
        self.state_after_step = {"VISUAL_LOCK": "VISUAL_CALIBRATED",
                                 "PRODUCTION": "PRODUCTION_PASSED"}
        rc, out = self._execute(self._two_steps(), until="PRODUCTION_PASSED")
        self.assertEqual(rc, 0)
        self.assertIn("after PRODUCTION", out)
        self.assertEqual(self.dispatched, ["VISUAL_LOCK", "PRODUCTION"])

    def test_successful_step_without_a_state_advance_is_not_a_stop(self):
        """rc=0 is not enough: the canonical state must actually have moved. This is the
        fail-closed property, observed from the loop rather than from the predicate."""
        write_state(self.ep, "STORYBOARD_LOCKED")
        rc, out = self._execute(self._two_steps(), until="VISUAL_CALIBRATED")
        self.assertEqual(rc, 0)
        self.assertNotIn(runtime_dag.STOP_TARGET_REACHED, out)
        self.assertEqual(self.dispatched, ["VISUAL_LOCK", "PRODUCTION"])

    def test_target_beyond_every_step_is_never_reported(self):
        """A target the DAG cannot reach must leave the exit path exactly as it was."""
        write_state(self.ep, "STORYBOARD_LOCKED")
        self.state_after_step = {"VISUAL_LOCK": "VISUAL_CALIBRATED",
                                 "PRODUCTION": "PRODUCTION_PASSED"}
        rc, out = self._execute(self._two_steps(), until="PUBLISH_READY")
        self.assertEqual(rc, 0)
        self.assertNotIn(runtime_dag.STOP_TARGET_REACHED, out)
        self.assertEqual(self.dispatched, ["VISUAL_LOCK", "PRODUCTION"])

    def test_a_failed_step_aborts_instead_of_reporting_a_stop(self):
        """A step that returned non-zero cannot have validated its stage, so --until must not
        fire: the DAG returns the failure rc, it does not claim the target was reached."""
        write_state(self.ep, "STORYBOARD_LOCKED")
        self.rc_by_step["VISUAL_LOCK"] = 4
        rc, out = self._execute(self._two_steps(), until="VISUAL_CALIBRATED")
        self.assertEqual(rc, 4)
        self.assertNotIn(runtime_dag.STOP_TARGET_REACHED, out)

    def test_no_until_behaves_exactly_as_before(self):
        """Default None: the loop is untouched, which is what keeps every caller safe."""
        write_state(self.ep, "STORYBOARD_LOCKED")
        self.state_after_step = {"VISUAL_LOCK": "VISUAL_CALIBRATED",
                                 "PRODUCTION": "PRODUCTION_PASSED"}
        rc, out = self._execute(self._two_steps(), until=None)
        self.assertEqual(rc, 0)
        self.assertNotIn(runtime_dag.STOP_TARGET_REACHED, out)
        self.assertEqual(self.dispatched, ["VISUAL_LOCK", "PRODUCTION"])


if __name__ == "__main__":
    unittest.main()
