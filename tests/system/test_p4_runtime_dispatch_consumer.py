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
import runtime_dag
import runtime_scheduler


class _FakeCriticAdapter:
    """Adapter seam used to prove the DAG/Scheduler target reaches the executor."""
    def __init__(self, *, legacy, observed):
        self.legacy = legacy
        self.observed = observed

    def execute_shadow_request(self, episode_dir, *, attempt, dispatch_authorization, **_kwargs):
        selected = codex_critic_runner.consume_scheduler_authorization(
            task_type=dispatch_authorization["task_type"], legacy_target=self.legacy,
            dispatch_authorization=dispatch_authorization,
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def fake_run(cmd, *, stdout, **kwargs):
                self.observed["cmd"] = list(cmd)
                stdout.write('{"type":"turn.completed","usage":{}}\n')
                return SimpleNamespace(returncode=0, remote={"request_id": "fixture"})

            with patch.object(codex_critic_runner.codex_user_runner, "run_codex", side_effect=fake_run):
                result = codex_critic_runner.launch(
                    "fixture critic request", codex=Path("codex"), root=root, timeout=1,
                    log_path=root / "critic.jsonl", model=self.legacy["model"],
                    execution_target=selected, dispatch_authorization=dispatch_authorization,
                )
        self.observed.update({
            "adapter_target": selected,
            "scheduler_authorized_target": result.scheduler_authorized_target,
            "actual_dispatch_target": result.actual_dispatch_target,
            "router_proposed_target": dispatch_authorization.get("router_proposed_target"),
        })
        return {"actual_dispatch_target": result.actual_dispatch_target}


class P4RuntimeDispatchConsumerTests(unittest.TestCase):
    def setUp(self):
        self.legacy = {"provider": "codex_user_runner", "model": "legacy-model", "runtime": "CODEX"}
        self.fallback = {"provider": "codex_user_runner", "model": "fallback-model", "runtime": "CODEX"}

    @staticmethod
    def decision(action, target=None, *, health="HEALTHY"):
        return {"effective_action": action, "effective_route": target,
                "health_status": health}

    def dispatch(self, *, action, production, target=None, health="HEALTHY", task="story_semantic_critic"):
        observed = {}
        adapter = _FakeCriticAdapter(legacy=self.legacy, observed=observed)
        result = runtime_dag.dispatch_critic_runnable(
            task, adapter=adapter, episode_dir=Path("fixture-episode"), attempt=1,
            legacy_target=self.legacy,
            route_decision=self.decision(action, target, health=health),
            production_enabled=production,
        )
        return result, observed

    def test_production_off_shadow_fallback_keeps_legacy_at_fake_executor(self):
        result, observed = self.dispatch(action="FALLBACK", production=False, target=self.fallback)
        self.assertEqual(result["scheduler_authorization"]["reason"], "PRODUCTION_DISABLED")
        self.assertEqual(observed["actual_dispatch_target"], self.legacy)
        self.assertEqual(observed["cmd"][observed["cmd"].index("-m") + 1], "legacy-model")
        self.assertNotEqual(observed["router_proposed_target"], observed["actual_dispatch_target"])

    def test_production_keep_legacy_reaches_fake_executor(self):
        result, observed = self.dispatch(action="KEEP_LEGACY", production=True)
        self.assertEqual(result["scheduler_authorized_target"], self.legacy)
        self.assertEqual(observed["actual_dispatch_target"], self.legacy)

    def test_production_fallback_target_reaches_fake_executor_and_receipt(self):
        result, observed = self.dispatch(action="FALLBACK", production=True, target=self.fallback)
        self.assertEqual(result["scheduler_authorized_target"], self.fallback)
        self.assertEqual(observed["scheduler_authorized_target"], self.fallback)
        self.assertEqual(observed["adapter_target"], self.fallback)
        self.assertEqual(observed["actual_dispatch_target"], self.fallback)
        self.assertEqual(observed["cmd"][observed["cmd"].index("-m") + 1], "fallback-model")

    def test_no_route_fails_closed_before_adapter_and_runner(self):
        observed = {}
        adapter = _FakeCriticAdapter(legacy=self.legacy, observed=observed)
        result = runtime_dag.dispatch_critic_runnable(
            "final_semantic_critic", adapter=adapter, episode_dir=Path("fixture"), attempt=1,
            legacy_target=self.legacy, route_decision=self.decision("NO_ROUTE"),
            production_enabled=True,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["adapter_called"])
        self.assertFalse(result["runner_called"])
        self.assertEqual(observed, {})

    def test_unknown_legacy_health_keeps_legacy(self):
        result, observed = self.dispatch(action="FALLBACK", production=True,
                                         target=self.fallback, health="UNKNOWN")
        self.assertEqual(result["scheduler_authorization"]["reason"], "UNKNOWN_HEALTH_KEEPS_LEGACY")
        self.assertEqual(observed["actual_dispatch_target"], self.legacy)

    def test_unsupported_task_bypasses_critic_dispatch_path(self):
        observed = {}
        adapter = _FakeCriticAdapter(legacy=self.legacy, observed=observed)
        result = runtime_dag.dispatch_critic_runnable(
            "world_prepare", adapter=adapter, episode_dir=Path("fixture"), attempt=1,
            legacy_target=self.legacy,
            route_decision=self.decision("FALLBACK", self.fallback), production_enabled=True,
        )
        self.assertEqual(result["status"], "BYPASS")
        self.assertFalse(result["adapter_called"])
        self.assertEqual(observed, {})

    def test_scheduler_authorization_is_pure_and_explicit(self):
        result = runtime_scheduler.authorize_critic_dispatch(
            task_type="story_semantic_critic", legacy_target=self.legacy,
            route_decision=self.decision("FALLBACK", self.fallback), production_enabled=True,
        )
        self.assertEqual(result["action"], "FALLBACK")
        self.assertEqual(result["execution_target"], self.fallback)
        self.assertTrue(result["scheduler_authorized"])


if __name__ == "__main__":
    unittest.main()
