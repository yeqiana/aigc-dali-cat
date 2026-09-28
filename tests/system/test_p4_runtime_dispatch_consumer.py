from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import codex_critic_runner


class P4RuntimeDispatchConsumerTests(unittest.TestCase):
    def setUp(self):
        self.legacy = {"provider": "codex_user_runner", "model": "legacy-model", "runtime": "CODEX"}

    @staticmethod
    def decision(action, target=None):
        return {"effective_action": action, "effective_route": target}

    def test_production_off_keeps_legacy_even_when_shadow_proposes_fallback(self):
        actual = codex_critic_runner.effective_execution_target(
            task_type="story_semantic_critic", legacy_target=self.legacy,
            route_decision=self.decision("FALLBACK", {
                "provider": "codex_user_runner", "model": "proposed-model", "runtime": "CODEX"}),
            production_enabled=False,
        )
        self.assertEqual(actual, self.legacy)

    def test_production_keep_legacy_keeps_original_target(self):
        actual = codex_critic_runner.effective_execution_target(
            task_type="story_semantic_critic", legacy_target=self.legacy,
            route_decision=self.decision("KEEP_LEGACY"), production_enabled=True,
            scheduler_authorized=True,
        )
        self.assertEqual(actual, self.legacy)

    def test_fallback_target_reaches_final_codex_command_and_receipt(self):
        fallback = codex_critic_runner.effective_execution_target(
            task_type="story_semantic_critic", legacy_target=self.legacy,
            route_decision=self.decision("FALLBACK", {
                "provider": "codex_user_runner", "model": "fallback-model", "runtime": "CODEX"}),
            production_enabled=True, scheduler_authorized=True,
        )
        captured = {}

        def fake_run(cmd, *, stdout, **kwargs):
            captured["cmd"] = list(cmd)
            stdout.write('{"type":"turn.completed","usage":{}}\n')
            return SimpleNamespace(returncode=0, remote={"request_id": "fake"})

        with tempfile.TemporaryDirectory() as temp, patch.object(codex_critic_runner.codex_user_runner,
                                                                  "run_codex", side_effect=fake_run):
            root = Path(temp)
            result = codex_critic_runner.launch(
                "fixture", codex=Path("codex"), root=root, timeout=1,
                log_path=root / "critic.jsonl", model="legacy-model",
                execution_target=fallback,
            )

        self.assertEqual(captured["cmd"][captured["cmd"].index("-m") + 1], "fallback-model")
        self.assertEqual(result.execution_target, fallback)
        self.assertEqual(result.actual_dispatch_target, fallback)

    def test_no_route_refuses_execution_before_runner_launch(self):
        called = False

        def fake_run(*_args, **_kwargs):
            nonlocal called
            called = True
            return SimpleNamespace(returncode=0, remote={})

        with patch.object(codex_critic_runner.codex_user_runner, "run_codex", side_effect=fake_run):
            with self.assertRaisesRegex(codex_critic_runner.ExecutionTargetRejected, "NO_ROUTE"):
                selected = codex_critic_runner.effective_execution_target(
                    task_type="final_semantic_critic", legacy_target=self.legacy,
                    route_decision=self.decision("NO_ROUTE"), production_enabled=True,
                    scheduler_authorized=True,
                )
                codex_critic_runner.launch("fixture", codex=Path("codex"), root=Path.cwd(), timeout=1,
                                           execution_target=selected)
        self.assertFalse(called)

    def test_unsupported_task_bypasses_router_and_keeps_legacy(self):
        actual = codex_critic_runner.effective_execution_target(
            task_type="world_prepare", legacy_target=self.legacy,
            route_decision=self.decision("FALLBACK", {
                "provider": "codex_user_runner", "model": "wrong-model", "runtime": "CODEX"}),
            production_enabled=True,
        )
        self.assertEqual(actual, self.legacy)

    def test_production_target_requires_scheduler_authorization(self):
        with self.assertRaisesRegex(codex_critic_runner.ExecutionTargetRejected, "Scheduler"):
            codex_critic_runner.effective_execution_target(
                task_type="story_semantic_critic", legacy_target=self.legacy,
                route_decision=self.decision("FALLBACK", {
                    "provider": "codex_user_runner", "model": "fallback-model", "runtime": "CODEX"}),
                production_enabled=True,
            )


if __name__ == "__main__":
    unittest.main()
