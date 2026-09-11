#!/usr/bin/env python3
"""V2.6.2 closure chain: artifact-save collision, CODEX_HOME recovery, and the
bounded continuous host loop that finally wires image dispatch into the main entry."""
from __future__ import annotations
import os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_runner
import image_artifact_collector
import image_model_policy
import product_runtime_adapter
import workflow_runner

CALL_ID = "exec-863861d5-1e96-49b1-9908-139a45c06cb4"
# Exact signature captured from meta/image-workers/01-9ae48137181c-a1.jsonl (episode 10-03).
COLLISION_LINE = (
    "WARN codex_image_generation_extension::tool: failed to save generated image: "
    "当文件已存在时，无法创建该文件。 (os error 183) call_id=" + CALL_ID +
    " output_dir=C:\\Users\\79873\\.codex\\generated_images\\01a08efd-3a7f-78d2-a60c-b15adc497218"
)
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"q" * 64


class ArtifactSaveCollisionTests(unittest.TestCase):
    def test_collision_is_a_provider_technical_failure(self):
        self.assertEqual(image_model_policy.classify_backend_error(COLLISION_LINE),
                         image_model_policy.ARTIFACT_SAVE_COLLISION)

    def test_collision_is_not_charged_as_content_repair(self):
        import image_scheduler
        self.assertEqual(image_scheduler.classify_error(COLLISION_LINE),
                         image_model_policy.ARTIFACT_SAVE_COLLISION)
        self.assertNotIn(image_model_policy.ARTIFACT_SAVE_COLLISION,
                         image_scheduler.NON_REGENERATING_FAILURE_CODES)

    def test_collision_does_not_masquerade_as_model_unavailable(self):
        code = image_model_policy.classify_backend_error(COLLISION_LINE)
        self.assertNotIn(code, {image_model_policy.MODEL_UNAVAILABLE,
                                image_model_policy.RATE_LIMIT_429,
                                image_model_policy.BACKEND_5XX})

    def test_call_id_is_extracted_for_secondary_recovery(self):
        self.assertEqual(image_artifact_collector._call_ids(COLLISION_LINE), [CALL_ID])

    def test_recovery_root_follows_codex_home(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {"CODEX_HOME": td}):
                self.assertEqual(image_artifact_collector.generated_images_root(),
                                 Path(td) / "generated_images")
            self.assertEqual(image_artifact_collector.generated_images_root(),
                             Path.home() / ".codex" / "generated_images")

    def test_recovery_finds_artifact_named_after_call_id(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory(prefix="repository-") as wd:
            hidden = Path(home) / "generated_images" / "thread-xyz" / f"{CALL_ID}.png"
            hidden.parent.mkdir(parents=True)
            hidden.write_bytes(PNG_BYTES)
            log = Path(wd) / "worker.jsonl"
            log.write_text(COLLISION_LINE, encoding="utf-8")
            with patch.dict(os.environ, {"CODEX_HOME": home}):
                self.assertEqual(image_artifact_collector.recover_codex_generated(log, Path(wd)),
                                 hidden.resolve())


class LocalImageDispatchTests(unittest.TestCase):
    def test_codex_image_executor_is_local(self):
        for name in ("GENERATE_IMAGES", "RETRY_TECHNICAL_FAILURES", "REPAIR_FAILED_IMAGES"):
            self.assertEqual(episode_runner.local_image_action({"action": name, "executor": "CODEX_IMAGE"}), name)

    def test_host_owned_actions_stay_with_the_host(self):
        rows = [{"action": "GENERATE_IMAGES", "executor": "WORK"},
                {"action": "REVIEW_GENERATED_IMAGES", "executor": "CODEX_IMAGE"},
                {"action": "PRODUCT_REVIEW", "executor": "CODEX_IMAGE"},
                {"action": "VISUAL_LOCK", "executor": "WORK"},
                {"action": "COMPLETE"}, {}, None, "GENERATE_IMAGES"]
        for row in rows:
            self.assertIsNone(episode_runner.local_image_action(row), row)

    def test_non_local_action_is_refused(self):
        with self.assertRaises(ValueError):
            episode_runner.run_local_image_action(Path("ep"), {"action": "VISUAL_LOCK", "executor": "WORK"})

    def test_run_local_image_action_dispatches_and_refreshes_next_action(self):
        calls, refreshed = [], []

        class FakeScheduler:
            @staticmethod
            def retry_tech(ep): calls.append(("retry_tech", str(ep)))

            @staticmethod
            def run_scheduler_async(ep, workers, timeout, codex):
                calls.append(("scheduler", workers, codex))
                return 7

        class FakeBatch:
            @staticmethod
            def should_use(ep): return False

            @staticmethod
            def run(ep, workers, timeout, codex):
                calls.append(("batch", workers))
                return 9

        class FakeConfig:
            @staticmethod
            def load_config(): return {"production": {"max_inflight_images": 3}}

            @staticmethod
            def get_path(data, dotted, default=None): return data["production"]["max_inflight_images"]

        def fake_write(ep):
            refreshed.append(str(ep))
            return {}

        modules = {"image_scheduler": FakeScheduler, "batch_scheduler": FakeBatch, "storyos_config": FakeConfig}
        with patch.dict(sys.modules, modules), \
                patch.object(episode_runner.next_action, "write", side_effect=fake_write), \
                patch.object(episode_runner.runtime_timeout_policy, "seconds", return_value=123):
            rc = episode_runner.run_local_image_action(Path("ep"), {"action": "GENERATE_IMAGES", "executor": "CODEX_IMAGE"})
            self.assertEqual(rc, 7)
            self.assertEqual(calls, [("scheduler", 3, None)])
            self.assertEqual(refreshed, ["ep"])

            calls.clear(); refreshed.clear()
            rc = episode_runner.run_local_image_action(Path("ep"), {"action": "RETRY_TECHNICAL_FAILURES", "executor": "CODEX_IMAGE"})
            self.assertEqual(rc, 7)
            self.assertEqual(calls, [("retry_tech", "ep"), ("scheduler", 3, None)])
            self.assertEqual(refreshed, ["ep"])


class ContinuousHostLoopTests(unittest.TestCase):
    def test_switch_is_read_from_config(self):
        with patch.object(workflow_runner.storyos_config, "get_path", return_value=True):
            self.assertTrue(workflow_runner.continuous_host_loop_enabled())
        with patch.object(workflow_runner.storyos_config, "get_path", return_value=None):
            self.assertFalse(workflow_runner.continuous_host_loop_enabled())

    def test_loop_runs_local_action_then_resumes_dag(self):
        seen, rc_seq = [], [product_runtime_adapter.HOST_ACTION_REQUIRED_RC, 0]

        def fake_step(ep):
            seen.append("step")
            return True, "GENERATE_IMAGES rc=0"

        def fake_dag(ep, **kw):
            seen.append("dag")
            return rc_seq.pop(0)

        with patch.object(workflow_runner, "host_loop_step", side_effect=fake_step), \
                patch.object(workflow_runner.runtime_dag, "execute", side_effect=fake_dag):
            rc, note = workflow_runner.advance_host_loop(Path("ep"), codex=None, timeout=1800, run_id="r", trace_id="t")
        self.assertEqual(rc, 0)
        # The DAG keeps returning HOST_WAIT until the host-owned step appears, so the loop
        # alternates action/DAG until the DAG answers with something else.
        self.assertEqual(seen, ["step", "dag", "step", "dag"])
        self.assertIn("GENERATE_IMAGES", note)

    def test_loop_hands_back_when_host_owns_pending_action(self):
        with patch.object(workflow_runner, "host_loop_step", return_value=(False, "VISUAL_LOCK")), \
                patch.object(workflow_runner.runtime_dag, "execute", side_effect=AssertionError("DAG must not resume without a local action")):
            rc, note = workflow_runner.advance_host_loop(Path("ep"), codex=None, timeout=1800, run_id="r", trace_id="t")
        self.assertEqual(rc, product_runtime_adapter.HOST_ACTION_REQUIRED_RC)
        self.assertIn("VISUAL_LOCK", note)

    def test_loop_is_bounded(self):
        with patch.object(workflow_runner, "host_loop_step", return_value=(True, "GENERATE_IMAGES rc=0")), \
                patch.object(workflow_runner.runtime_dag, "execute", return_value=product_runtime_adapter.HOST_ACTION_REQUIRED_RC):
            rc, note = workflow_runner.advance_host_loop(Path("ep"), codex=None, timeout=1800, run_id="r", trace_id="t", max_cycles=2)
        self.assertEqual(rc, product_runtime_adapter.HOST_ACTION_REQUIRED_RC)
        self.assertIn("max_cycles=2", note)

    def test_execute_cycle_prefers_the_local_image_action(self):
        action = {"action": "GENERATE_IMAGES", "executor": "CODEX_IMAGE"}
        with patch.object(episode_runner.next_action, "write", return_value=action), \
                patch.object(episode_runner, "run_local_image_action", return_value=5) as runner, \
                patch.object(episode_runner.runtime_dag, "execute", side_effect=AssertionError("DAG must not run for a local image action")):
            self.assertEqual(episode_runner.execute_cycle(Path("ep")), 5)
        runner.assert_called_once()

    def test_execute_cycle_falls_back_to_dag(self):
        with patch.object(episode_runner.next_action, "write", return_value={"action": "VISUAL_LOCK", "executor": "WORK"}), \
                patch.object(episode_runner.runtime_dag, "execute", return_value=product_runtime_adapter.HOST_ACTION_REQUIRED_RC):
            self.assertEqual(episode_runner.execute_cycle(Path("ep")), product_runtime_adapter.HOST_ACTION_REQUIRED_RC)


if __name__ == "__main__":
    unittest.main()
