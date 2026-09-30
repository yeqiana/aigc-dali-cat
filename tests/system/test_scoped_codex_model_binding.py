"""Scoped workers consume explicit Model Policy bindings without starting Codex."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
import scoped_codex_worker as worker


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


if __name__ == "__main__":
    unittest.main()
