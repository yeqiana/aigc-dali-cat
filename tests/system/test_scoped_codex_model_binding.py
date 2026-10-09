"""Scoped workers consume explicit Model Policy bindings without starting Codex."""
from __future__ import annotations

import sys
import subprocess
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
import scoped_codex_worker as worker
import codex_critic_runner


class ScopedCodexModelBindingTests(unittest.TestCase):
    def test_prompt_authoring_resolves_the_structured_text_role(self):
        binding = {
            "role": "prompt.production", "profile": "structured_text",
            "model": "policy-text-model", "reasoning_effort": "low",
            "model_policy_sha256": "a" * 64,
        }
        with patch.object(worker.model_policy, "resolve", return_value=binding) as resolve:
            actual = worker.resolved_model("PROMPT_AUTHORING", Path("episode"))
        resolve.assert_called_once_with("prompt.production", episode=Path("episode"))
        self.assertEqual(actual, binding)

    def test_codex_exec_argv_binds_model_and_reasoning_effort(self):
        with patch.object(worker, "prefix", return_value=["codex"]):
            command = worker.codex_exec_command(Path("codex.exe"), {
                "model": "policy-model", "reasoning_effort": "high",
            })
        self.assertEqual(command[:8], [
            "codex", "exec", "--skip-git-repo-check", "--ephemeral",
            "-m", "policy-model", "-c", 'model_reasoning_effort="high"',
        ])

    def test_prompt_authoring_is_a_bounded_scoped_step(self):
        self.assertIn("PROMPT_AUTHORING", worker.STEP_DIRECTIVES)
        self.assertIn("Do NOT call image_generation", worker.STEP_DIRECTIVES["PROMPT_AUTHORING"])

    def test_incomplete_model_policy_binding_fails_closed(self):
        with patch.object(worker.model_policy, "resolve", return_value={"model": "no-policy"}):
            with self.assertRaisesRegex(ValueError, "complete binding"):
                worker.resolved_model("PROMPT_AUTHORING", Path("episode"))

    def test_scoped_fingerprint_binds_model_policy_identity(self):
        observed = []

        def record(**kwargs):
            observed.append(kwargs)
            return kwargs

        binding = {
            "role": "prompt.production", "model": "policy-model",
            "reasoning_effort": "low", "model_policy_sha256": "policy-sha",
        }
        with patch.object(worker.runtime_request, "authority_for_episode", return_value=None), \
             patch.object(worker.inflight_codex_task, "fingerprint", side_effect=record):
            identity = worker.scoped_fingerprint(Path("episode"), "PROMPT_AUTHORING", "prompt", binding, "source-sha")

        self.assertIs(identity, observed[0])
        self.assertEqual(observed[0]["model_role"], "prompt.production")
        self.assertEqual(observed[0]["effective_model"], "policy-model")
        self.assertEqual(observed[0]["reasoning_effort"], "low")
        self.assertEqual(observed[0]["model_policy_sha256"], "policy-sha")
        self.assertEqual(observed[0]["evidence_sha256"], "source-sha")

    def test_safe_runner_diagnostics_reads_only_named_durable_result_and_projects_allowlist(self):
        remote = {
            "request_id": "req-123", "returncode": 1, "elapsed_seconds": 3.5,
            "timed_out": False, "task_type": "scoped_step", "transport": "user_runner",
            "api_key": "must-not-persist",
        }
        durable = {"output_base64": "secret-like-output", "raw_stdout": "private"}
        with patch.object(worker.codex_user_runner, "read_task_result", return_value=durable) as read:
            result = worker._safe_runner_diagnostics(remote)

        read.assert_called_once_with("req-123")
        self.assertEqual(result, {
            "request_id": "req-123", "returncode": 1, "elapsed_seconds": 3.5,
            "timed_out": False, "task_type": "scoped_step", "transport": "user_runner",
            "durable_result_present": True,
        })
        self.assertNotIn("api_key", result)
        self.assertNotIn("output_base64", result)

    def test_safe_runner_diagnostics_without_request_id_does_not_read_durable_result(self):
        with patch.object(worker.codex_user_runner, "read_task_result") as read:
            result = worker._safe_runner_diagnostics({"returncode": 124, "timed_out": True})

        read.assert_not_called()
        self.assertIsNone(result["request_id"])
        self.assertFalse(result["durable_result_present"])

    def test_controller_preflight_captures_pipe_output_in_direct_and_bridged_modes(self):
        expected = (
            json.dumps({"type": "item.completed", "item": {
                "type": "agent_message", "text": '{"capability_probe":"PASS"}'
            }}) + "\n"
            + json.dumps({"type": "turn.completed"}) + "\n"
        )
        binding = {
            "role": "image.controller", "profile": "image_controller",
            "model": "gpt-6-luna", "reasoning_effort": "high",
            "model_policy_sha256": "policy-sha",
        }

        for transport in ("direct_codex_user_runner", "user_runner"):
            with self.subTest(transport=transport):
                output = io.StringIO()

                def run_codex(*_args, **kwargs):
                    self.assertIs(kwargs["stdout"], subprocess.PIPE)
                    completed = subprocess.CompletedProcess(
                        ["codex"], 0, stdout=expected
                    )
                    completed.remote = {"returncode": 0, "transport": transport}
                    return completed

                with patch.object(worker, "resolve_codex", return_value=Path("codex")), \
                     patch.object(worker, "codex_exec_command", return_value=["codex", "exec", "-"]), \
                     patch.object(worker.codex_user_runner, "run_codex", side_effect=run_codex), \
                     patch.object(worker.runtime_observability, "now", return_value="now"), \
                     patch.object(worker.runtime_observability, "write_model_execution_receipt", return_value=Path("receipt.json")), \
                     patch.object(worker, "_model_event"), \
                     patch("logical_asset_identity.episode_id", return_value="episode"):
                    rc, receipt = worker.execute_model_call(
                        Path("episode"), "EXACT_CONTROLLER_CAPABILITY_PREFLIGHT",
                        binding, "probe", output_handle=output, sandbox="read-only",
                    )

                self.assertEqual(rc, 0)
                self.assertEqual(output.getvalue(), expected)
                self.assertEqual(
                    codex_critic_runner.recover_completed_agent_json(output.getvalue()),
                    {"capability_probe": "PASS"},
                )
                self.assertEqual(receipt["status"], "SUCCESS")

    def test_image_payload_controller_persists_output_through_pipe(self):
        output = io.StringIO()
        expected = '{"text":"exact frame request"}'
        binding = {
            "role": "image.controller", "profile": "image_controller",
            "model": "gpt-6-luna", "reasoning_effort": "high",
            "model_policy_sha256": "policy-sha",
        }

        def run_codex(*_args, **kwargs):
            self.assertIs(kwargs["stdout"], subprocess.PIPE)
            return subprocess.CompletedProcess(["codex"], 0, stdout=expected)

        with patch.object(worker, "resolve_codex", return_value=Path("codex")), \
             patch.object(worker, "codex_exec_command", return_value=["codex", "exec", "-"]), \
             patch.object(worker.codex_user_runner, "run_codex", side_effect=run_codex), \
             patch.object(worker.runtime_observability, "now", return_value="now"), \
             patch.object(worker.runtime_observability, "write_model_execution_receipt", return_value=Path("receipt.json")), \
             patch.object(worker, "_model_event"), \
             patch("logical_asset_identity.episode_id", return_value="episode"):
            rc, receipt = worker.execute_model_call(
                Path("episode"), "IMAGE_PAYLOAD_REQUEST", binding, "controller prompt",
                output_handle=output, persist_output_stream=True, sandbox="read-only",
            )

        self.assertEqual(rc, 0)
        self.assertEqual(output.getvalue(), expected)
        self.assertEqual(receipt["scoped_output_stream"], expected)


if __name__ == "__main__":
    unittest.main()
