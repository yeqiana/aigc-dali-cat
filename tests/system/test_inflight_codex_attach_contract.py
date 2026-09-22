#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate D (P0-D): a restarted Driver claims the Codex task its predecessor paid for.

2026-09-15 尸解仙: the host killed the Driver 300 s into CREATIVE_STORY. Codex did
not die with it -- it is hosted by the resident `codex_user_runner.py serve`
process -- so the step ran to completion and its output landed in
`runtime/codex-user-runner/task-results/<request_id>.json`. The next Driver called
`run_codex()` with a fresh `uuid4()`, paid for the same step a second time, and
left the first result unread.

`inflight_codex_task.py` writes a durable record *before* submission so a later
Driver can ask "does a task I already paid for answer exactly this question?"
instead of guessing. Three answers, none of which is "submit again by default":
ADOPT / WAIT / RESUBMIT, fail-closed towards RESUBMIT.

The seam test at the end is the one that matters most: it drives the real
`scoped_codex_worker.run_step` with the real Codex call wired to explode, so "the
restarted Driver adopts the old result" is proven by the absence of a second
submission rather than by inspecting a decision object.

Request ids here are 32-char hex because the runner itself only accepts that
charset (`codex_user_runner.task_result_path`); a non-hex id makes the result
unreadable, which is a different failure than the one under test.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import codex_user_runner
import inflight_codex_task
import scoped_codex_worker

STEP = "CREATIVE_STORY"
PROMPT = "bounded scoped worker prompt for CREATIVE_STORY"
STDIN_SHA = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()


def RID(n: int) -> str:
    """A valid runner request_id: uuid4().hex shape, so it is readable back."""
    return f"{n:032x}"


def result_payload(request_id: str, *, output: bytes = b'{"ok":true}', returncode: int = 0,
                   stdin_sha256: str = STDIN_SHA, task_type: str = "scoped_step",
                   timed_out: bool = False, output_bytes=None, output_sha256=None) -> dict:
    """The exact shape `codex_user_runner` persists to task-results/<id>.json."""
    return {
        "request_id": request_id,
        "recorded_at": "2026-09-15T00:00:00+0800",
        "returncode": returncode,
        "output_bytes": len(output) if output_bytes is None else output_bytes,
        "output_sha256": output_sha256 or hashlib.sha256(output).hexdigest(),
        "output_base64": base64.b64encode(output).decode("ascii"),
        "evidence": {
            "request_id": request_id,
            "task_type": task_type,
            "stdin_sha256": stdin_sha256,
            "timed_out": timed_out,
        },
    }


class InflightCodexAttachContractTests(unittest.TestCase):

    def setUp(self) -> None:
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="inflight-", dir=base)
        self.ep = Path(self._td.name)
        (self.ep / "meta/runtime").mkdir(parents=True, exist_ok=True)
        self.runtime = Path(self._td.name) / "runner-runtime"
        (self.runtime / codex_user_runner.RESULT_DIR_NAME).mkdir(parents=True, exist_ok=True)
        patcher = mock.patch.object(codex_user_runner, "runtime_dir", return_value=self.runtime)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        self._td.cleanup()

    # --- fixtures -----------------------------------------------------------

    def fingerprint(self, prompt: str = PROMPT, step: str = STEP) -> str:
        return inflight_codex_task.fingerprint(step=step, prompt=prompt)

    def record_task(self, request_id: str, *, timeout_seconds: int = 0,
                    prompt: str = PROMPT, step: str = STEP, stdin_sha256: str = STDIN_SHA) -> dict:
        """Default timeout 0 puts the task past its deadline, so a validation
        verdict surfaces instead of WITHIN_TASK_DEADLINE masking it."""
        return inflight_codex_task.begin(
            self.ep, step=step, request_id=request_id,
            fingerprint_value=self.fingerprint(prompt, step),
            stdin_sha256=stdin_sha256, timeout_seconds=timeout_seconds)

    def store_result(self, request_id: str, payload: dict) -> Path:
        path = self.runtime / codex_user_runner.RESULT_DIR_NAME / f"{request_id}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def classify(self, *, prompt: str = PROMPT, step: str = STEP, running=()) -> dict:
        with mock.patch.object(
                inflight_codex_task, "_runner_inflight_state",
                side_effect=lambda rid: (
                    inflight_codex_task.RUNNER_TASK_RUNNING
                    if str(rid) in {str(x) for x in running}
                    else inflight_codex_task.RUNNER_TASK_NOT_RUNNING)):
            return inflight_codex_task.classify(
                self.ep, step=step, fingerprint_value=self.fingerprint(prompt, step))

    # --- in-flight request_id 有持久证据 ------------------------------------

    def test_the_record_is_durable_before_the_task_is_submitted(self):
        self.record_task(RID(1), timeout_seconds=3600)
        path = self.ep / inflight_codex_task.REL
        self.assertTrue(path.is_file(), "in-flight 记录没有落盘，Driver 死后无从领取")

        # Read through a cold path: a restarted Driver has only the file.
        fresh = json.loads(path.read_text(encoding="utf-8"))
        row = fresh["steps"][STEP]
        self.assertEqual(row["request_id"], RID(1))
        self.assertEqual(row["fingerprint"], self.fingerprint())
        self.assertEqual(row["stdin_sha256"], STDIN_SHA)
        self.assertEqual(inflight_codex_task.lookup(self.ep, STEP)["request_id"], RID(1))

    def test_clearing_a_collected_task_leaves_nothing_to_attach(self):
        self.record_task(RID(2))
        inflight_codex_task.clear(self.ep, STEP)
        self.assertIsNone(inflight_codex_task.lookup(self.ep, STEP))
        verdict = self.classify()
        self.assertEqual(verdict["decision"], inflight_codex_task.RESUBMIT)
        self.assertEqual(verdict["reason"], "NO_IN_FLIGHT_RECORD")

    # --- Driver 重启可领取旧成功结果 ----------------------------------------

    def test_a_restarted_driver_adopts_a_complete_result(self):
        self.record_task(RID(3))
        self.store_result(RID(3), result_payload(RID(3), output=b"the story"))

        verdict = self.classify()
        self.assertEqual(verdict["decision"], inflight_codex_task.ADOPT)
        self.assertEqual(verdict["reason"], "OK")
        self.assertEqual(verdict["output"], b"the story")
        self.assertEqual(verdict["returncode"], 0)

    # --- source SHA 漂移不会误复用 ------------------------------------------

    def test_drifted_inputs_are_never_reused(self):
        """The fingerprint pins step + prompt bytes + capsule source SHA."""
        self.record_task(RID(4))
        self.store_result(RID(4), result_payload(RID(4)))

        self.assertEqual(self.classify(prompt=PROMPT + " (story changed)")["reason"],
                         "FINGERPRINT_DRIFT")
        # A different step has no record of its own; either way nothing is reused.
        other = self.classify(step="VISUAL_LOCK")
        self.assertEqual(other["decision"], inflight_codex_task.RESUBMIT)
        self.assertNotIn("output", other)

    def test_v2_identity_ignores_volatile_prompt_bytes_but_not_authority_drift(self):
        """Restarted prompts may change derived capsule bytes without changing the task."""
        stable = "a" * 64
        first = inflight_codex_task.fingerprint(
            step=STEP, prompt="prompt with compiled_at=A", source_sha256=stable)
        second = inflight_codex_task.fingerprint(
            step=STEP, prompt="prompt with compiled_at=B", source_sha256=stable)
        changed = inflight_codex_task.fingerprint(
            step=STEP, prompt="prompt with compiled_at=B", source_sha256="b" * 64)
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_creative_story_attach_identity_excludes_its_own_prepared_outputs(self):
        """The real P0-D bug: prepare-time files must not make CREATIVE_STORY self-drift."""
        (self.ep / "meta").mkdir(exist_ok=True)
        (self.ep / "meta/runtime-request.json").write_text(json.dumps({
            "topic": {"title": "same story"},
            "story_input": {"mode": "auto_create"},
            "creative_hints": [],
            "visual_profile": None,
            "provenance": {"source": "natural_language", "original_request": "make same story"},
        }), encoding="utf-8")
        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8")
        first = scoped_codex_worker.attach_source_sha256(self.ep, STEP)
        # These are all created/updated by prompt()/CREATIVE_STORY itself and were
        # exactly what changed during the first real fault injection.
        for name in ("character-contract.json", "resource-selection.json",
                     "directing-quality.json", "story-gates.json"):
            (self.ep / "meta" / name).write_text(json.dumps({"changed": name}), encoding="utf-8")
        second = scoped_codex_worker.attach_source_sha256(self.ep, STEP)
        self.assertEqual(first, second)

        request = json.loads((self.ep / "meta/runtime-request.json").read_text(encoding="utf-8"))
        request["story_input"] = {"mode": "user_seed", "raw": "materially changed story"}
        (self.ep / "meta/runtime-request.json").write_text(json.dumps(request), encoding="utf-8")
        self.assertNotEqual(first, scoped_codex_worker.attach_source_sha256(self.ep, STEP))

    def test_a_result_produced_from_different_bytes_is_not_adopted(self):
        """The runner's recorded stdin SHA pins the output to the exact prompt."""
        self.record_task(RID(5))
        self.store_result(RID(5), result_payload(RID(5), stdin_sha256="f" * 64))
        verdict = self.classify()
        self.assertEqual(verdict["decision"], inflight_codex_task.RESUBMIT)
        self.assertEqual(verdict["validation"], "STDIN_DRIFT")
        self.assertNotIn("output", verdict)

    def test_another_step_or_another_task_type_is_not_adopted(self):
        self.record_task(RID(6))
        self.store_result(RID(6), result_payload(RID(7)))
        self.assertEqual(self.classify()["validation"], "REQUEST_ID_MISMATCH")

        self.store_result(RID(6), result_payload(RID(6), task_type="image"))
        self.assertEqual(self.classify()["validation"], "TASK_TYPE_NOT_SCOPED_STEP")

    def test_a_truncated_result_is_not_adopted(self):
        """Existence is not completeness: a half-written file must not close a step."""
        self.record_task(RID(8))
        self.store_result(RID(8), result_payload(RID(8), output_bytes=4096))
        self.assertEqual(self.classify()["validation"], "OUTPUT_TRUNCATED")

        self.store_result(RID(8), result_payload(RID(8), output_sha256="0" * 64))
        self.assertEqual(self.classify()["validation"], "OUTPUT_SHA_MISMATCH")

    # --- rc 非 0 不会被当成功 -------------------------------------------------

    def test_a_nonzero_returncode_is_never_adopted(self):
        for rc in (1, 20, 21, 22, 23, 24, 124):
            with self.subTest(rc=rc):
                self.record_task(RID(9))
                self.store_result(RID(9), result_payload(RID(9), returncode=rc))
                verdict = self.classify()
                self.assertEqual(verdict["decision"], inflight_codex_task.RESUBMIT)
                self.assertEqual(verdict["validation"], f"RETURNCODE_{rc}")
                self.assertNotIn("output", verdict, "非 0 退出码的结果被当成了答案")

    def test_a_timed_out_result_is_never_adopted_even_at_rc_zero(self):
        self.record_task(RID(10))
        self.store_result(RID(10), result_payload(RID(10), returncode=0, timed_out=True))
        self.assertEqual(self.classify()["validation"], "TASK_TIMED_OUT")

    # --- in-flight 未结束时不会重复提交 --------------------------------------

    def test_a_still_running_task_waits_instead_of_resubmitting(self):
        self.record_task(RID(11), timeout_seconds=3600)
        verdict = self.classify(running=(RID(11),))
        self.assertEqual(verdict["decision"], inflight_codex_task.WAIT)
        self.assertEqual(verdict["reason"], "TASK_STILL_RUNNING")
        self.assertNotIn("output", verdict)

    def test_an_absent_result_inside_the_task_deadline_waits(self):
        """A runner that restarted and lost its in-flight map is not proof of death."""
        self.record_task(RID(12), timeout_seconds=3600)
        verdict = self.classify()
        self.assertEqual(verdict["decision"], inflight_codex_task.WAIT)
        self.assertEqual(verdict["reason"], "WITHIN_TASK_DEADLINE")

    def test_an_absent_result_past_the_deadline_resubmits(self):
        self.record_task(RID(13), timeout_seconds=0)
        verdict = self.classify()
        self.assertEqual(verdict["decision"], inflight_codex_task.RESUBMIT)
        self.assertEqual(verdict["reason"], "NO_DURABLE_RESULT")

    def test_reachable_old_runner_without_inflight_visibility_never_resubmits(self):
        """A protocol-old live runner must not turn uncertainty into duplicate work."""
        self.record_task(RID(17), timeout_seconds=0)
        with mock.patch.object(
                inflight_codex_task.codex_user_runner, "runner_health",
                return_value={"status": "ok", "user": "RENRP\\yeqian"}):
            verdict = inflight_codex_task.classify(
                self.ep, step=STEP, fingerprint_value=self.fingerprint())
        self.assertEqual(verdict["decision"], inflight_codex_task.WAIT)
        self.assertEqual(verdict["reason"], "RUNNER_INFLIGHT_VISIBILITY_UNAVAILABLE")

    def test_current_runner_protocol_exposes_inflight_feature(self):
        service = codex_user_runner.RunnerState("127.0.0.1", 0, "test-token")
        health = service.health()
        self.assertGreaterEqual(health["protocol_revision"], 2)
        self.assertIn("inflight_request_ids", health)
        self.assertIn("inflight_request_ids", health["features"])

    # --- the real seam -------------------------------------------------------

    def test_run_step_adopts_without_calling_codex_again(self):
        """重启后的 Driver 不得把同一个 Codex 任务再发一次。

        Drives `scoped_codex_worker.run_step` end to end with the Codex call wired
        to raise: passing means the step closed on the adopted bytes and no second
        submission happened.
        """
        self.record_task(RID(14), timeout_seconds=3600)
        self.store_result(RID(14), result_payload(RID(14), output=b"adopted output"))

        def boom(*args, **kwargs):
            raise AssertionError("Driver 重启后又提交了一次 Codex 任务")

        with mock.patch.object(scoped_codex_worker, "prompt", return_value=PROMPT), \
                mock.patch.object(scoped_codex_worker.runtime_router, "local_codex_allowed",
                                  return_value=True), \
                mock.patch.object(codex_user_runner, "bridge_required", return_value=True), \
                mock.patch.object(scoped_codex_worker, "resolve_codex", return_value=Path("codex")), \
                mock.patch.object(scoped_codex_worker, "prefix", return_value=["codex"]), \
                mock.patch.object(codex_user_runner, "run_codex", side_effect=boom), \
                mock.patch.object(scoped_codex_worker.episode_performance, "safe_begin_stage",
                                  return_value=None), \
                mock.patch.object(scoped_codex_worker.episode_performance, "safe_end_stage",
                                  return_value=None):
            rc, log = scoped_codex_worker.run_step(self.ep, STEP, codex_raw="codex", timeout=60)

        self.assertEqual(rc, 0)
        self.assertIn("adopted output", Path(log).read_text(encoding="utf-8"))
        self.assertIsNone(
            inflight_codex_task.lookup(self.ep, STEP),
            "ADOPT 后已完成任务仍残留在 in-flight，会导致后续 Driver 循环重复领取同一结果",
        )

    def test_run_step_submits_fresh_when_the_task_is_provably_gone(self):
        """过期且无产出：不是「再等等」，而是真的可以重跑。"""
        self.record_task(RID(15), timeout_seconds=0)
        self.assertEqual(self.classify()["decision"], inflight_codex_task.RESUBMIT)

        worker = scoped_codex_worker
        with mock.patch.object(worker, "prompt", return_value=PROMPT), \
                mock.patch.object(worker.runtime_router, "local_codex_allowed", return_value=True), \
                mock.patch.object(codex_user_runner, "bridge_required", return_value=True), \
                mock.patch.object(worker, "resolve_codex", return_value=Path("codex")), \
                mock.patch.object(worker, "prefix", return_value=["codex"]), \
                mock.patch.object(codex_user_runner, "run_codex",
                                  side_effect=AssertionError("reached the Codex call")) as run_codex, \
                mock.patch.object(worker.episode_performance, "safe_begin_stage", return_value=None), \
                mock.patch.object(worker.episode_performance, "safe_end_stage", return_value=None):
            with self.assertRaises(AssertionError):
                worker.run_step(self.ep, STEP, codex_raw="codex", timeout=60)
        self.assertTrue(run_codex.called, "任务已确认消失时却没有重新提交")
        # The fresh submission records a new request_id before it runs.
        self.assertNotEqual(inflight_codex_task.lookup(self.ep, STEP)["request_id"], RID(15))

    def test_status_is_a_read_only_projection(self):
        self.record_task(RID(16), timeout_seconds=3600)
        data = inflight_codex_task.status(self.ep)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["step"], STEP)
        self.assertEqual(data["tasks"][0]["request_id"], RID(16))
        self.assertIn(data["tasks"][0]["decision"],
                      {inflight_codex_task.ADOPT, inflight_codex_task.WAIT,
                       inflight_codex_task.RESUBMIT})
        self.assertEqual(inflight_codex_task.lookup(self.ep, STEP)["request_id"], RID(16))


if __name__ == "__main__":
    unittest.main()
