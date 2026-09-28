"""P4 guarded production policy tests use injected local health and registry only."""
from __future__ import annotations

import datetime as dt
import copy
import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
import capability_router as router
import p4_capability_router_implementation as impl
import runtime_router
import runtime_scheduler
import storyos_config
import product_review_adapter
from unittest.mock import patch

NOW = impl.NOW


class P4ProductionRouterTests(unittest.TestCase):
    def route(self, task="story_semantic_critic", provider="WORK", model="host-managed", statuses=(),
              production=True, required=None):
        return impl._decision(task, "test-route", legacy_provider=provider, legacy_model=model,
                              statuses=statuses, production=production, required=required)

    def test_production_flag_defaults_false(self):
        self.assertFalse(router.effective_router_config()["production_enabled"])

    def test_yaml_config_controls_router_mode(self):
        config = impl._config(True)
        self.assertTrue(router.effective_router_config(config)["production_enabled"])
        self.assertEqual(router.effective_router_config(config)["policy_mode"],
                         "LEGACY_PREFERRED_CAPABILITY_GUARDED")

    def test_config_validation_rejects_invalid_router_settings(self):
        config = copy.deepcopy(storyos_config.load_config())
        config["agent_runtime"]["task_capability_router"]["production_enabled"] = "true"
        self.assertTrue(any("production_enabled must be a bool" in error
                            for error in storyos_config.validate(config)))

    def test_unsupported_task_bypasses_router(self):
        result = self.route("story_semantic_critic")
        req = router.CapabilityRouteRequest("unsupported-p4", "image_generation", "P4", "P4", "image",
                                            required_capabilities=("image_generation",))
        bypass = router.resolve_effective_route(req, legacy_provider="WORK", legacy_model="host-managed",
            legacy_runtime="WORK", registry=impl._registry(), health=impl._health([]), now=NOW,
            config=impl._config(True))
        self.assertEqual(bypass["effective_action"], "BYPASS_ROUTER_PRODUCTION")
        self.assertEqual(result["effective_action"], "KEEP_LEGACY")

    def test_unknown_legacy_keeps_legacy(self):
        self.assertEqual(self.route()["effective_action"], "KEEP_LEGACY")

    def test_unknown_candidate_never_used_as_fallback(self):
        result = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0)])
        self.assertEqual(result["effective_action"], "NO_ROUTE")
        self.assertTrue(all(row["reasons"] for row in result["rejected_candidates"]))

    def test_expired_health_never_used_as_fallback(self):
        result = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                                     ("codex_user_runner", "fixture-model", "HEALTHY", 301)])
        self.assertEqual(result["effective_action"], "NO_ROUTE")

    def test_degraded_uses_fresh_healthy_fallback(self):
        result = self.route(statuses=[("WORK", "host-managed", "DEGRADED", 0),
                                     ("codex_user_runner", "fixture-model", "HEALTHY", 0)])
        self.assertEqual(result["effective_action"], "FALLBACK")
        self.assertEqual(result["effective_route"]["provider"], "codex_user_runner")

    def test_unavailable_uses_fresh_healthy_fallback(self):
        result = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                                     ("codex_user_runner", "fixture-model", "HEALTHY", 0)])
        self.assertEqual(result["effective_action"], "FALLBACK")

    def test_no_route_fail_closed(self):
        result = self.route("final_semantic_critic", provider="codex_user_runner", model="fixture-model",
                            statuses=[("codex_user_runner", "fixture-model", "UNAVAILABLE", 0)])
        self.assertEqual(result["effective_action"], "NO_ROUTE")
        self.assertIsNone(result["effective_route"]["provider"])
        self.assertIsNone(result["effective_route"]["model"])

    def test_story_high_reasoning_is_optional(self):
        req, *_ = router.critic_route_request(request_id="story-contract",
            kind="story-semantic-critic-shadow", stage="STORY", host_execution="workspace_provider",
            legacy_provider="WORK", legacy_model=None)
        self.assertNotIn("high_reasoning", req.required_capabilities)
        self.assertIn("high_reasoning", req.optional_capabilities)

    def test_preimage_policy_required_capabilities(self):
        req, *_ = router.critic_route_request(request_id="preimage-contract",
            kind="preimage-semantic-critic-shadow", stage="PREIMAGE", host_execution="workspace_provider",
            legacy_provider="WORK", legacy_model=None)
        self.assertEqual(set(req.required_capabilities), {"text_input", "structured_output"})

    def test_final_policy_requires_image_input(self):
        req, *_ = router.critic_route_request(request_id="final-contract",
            kind="final-semantic-critic-shadow", stage="FINAL", host_execution="codex_user_runner_shadow",
            legacy_provider="codex_user_runner", legacy_model="fixture-model")
        self.assertTrue({"text_input", "image_input", "structured_output"}.issubset(req.required_capabilities))

    def test_production_false_matches_legacy_route(self):
        result = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                                      ("codex_user_runner", "fixture-model", "HEALTHY", 0)],
                            production=False)
        self.assertEqual(result["effective_action"], "KEEP_LEGACY")
        self.assertEqual(result["effective_route"], result["legacy_route"])
        self.assertFalse(result["actual_dispatch_changed"])

    def test_single_switch_rollback(self):
        self.assertTrue(impl.rollback_simulation()["single_flag_restores_legacy"])

    def test_router_never_dispatches(self):
        result = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                                      ("codex_user_runner", "fixture-model", "HEALTHY", 0)])
        self.assertEqual(result["effective_action"], "FALLBACK")
        self.assertFalse(result["actual_dispatch_changed"])
        self.assertEqual(result["llm_calls"], 0)

    def test_scheduler_remains_owner(self):
        source = Path(runtime_scheduler.__file__).read_text(encoding="utf-8")
        self.assertIn("plans dependency release and worker slots only", source)
        result = runtime_scheduler.schedule([{"node_id": "p4-owner-check", "node_type": "review",
            "depends_on": [], "input_contract": {}, "output_contract": {}, "retry_policy": {},
            "priority": "HIGH", "evidence_required": [],
            "execution_policy": {"mode": "serial", "parallel_safe": False,
                                 "resource_class": "text", "max_concurrency": 1}}])
        self.assertEqual(result["dispatch"][0]["node_id"], "p4-owner-check")
        self.assertTrue(runtime_router.capability_router_config()["shadow_enabled"])

    def test_dispatch_consumer_gate_is_derived_from_actual_execution_path(self):
        audit = impl.audit_dispatch_consumer()
        self.assertFalse(audit["consumer_present"])
        self.assertTrue(audit["checks"]["advisory_target_producer_present"])
        self.assertTrue(audit["checks"]["runtime_dag_uses_runtime_scheduler"])
        self.assertFalse(audit["checks"]["runtime_dag_consumes_effective_target"])
        self.assertFalse(audit["checks"]["executor_accepts_effective_target"])
        self.assertIn("runtime_dag_consumes_effective_target", audit["missing_handoffs"])
        self.assertTrue(any(row["path"].endswith("/codex_critic_runner.py")
                            for row in audit["source_files"].values()))

    def test_implementation_gate_keeps_real_dispatch_consumer_blocker(self):
        gate = impl.build_implementation_gate(regression={
            "focused_pass": True, "broad_pass": True,
        })
        self.assertFalse(gate["mandatory_checks"]["adapter_dispatch_consumer_present"])
        self.assertIn("adapter_dispatch_consumer_present", gate["blockers"])
        self.assertEqual(gate["p4_status"], "CUTOVER_IMPLEMENTATION_BLOCKED")
        self.assertFalse(gate["production_enabled"])

    def test_canary_dry_run_never_dispatches(self):
        result = impl.production_canary_dry_run()
        self.assertGreaterEqual(result["case_count"], 10)
        self.assertTrue(result["all_cases_pass"])
        self.assertFalse(result["actual_dispatch_changed"])
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertFalse(result["image_generation_invoked"])

    def test_adapter_production_branch_returns_target_without_dispatch(self):
        source = ROOT / "tests/fixtures/p3_story_semantic/pass_ordinary/story.md"
        registry = impl._registry()
        health = router.HealthCache(300)
        observed = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)
        health.record("WORK", "host-managed", "UNAVAILABLE", reason="injected", source="fixture", observed_at=observed)
        health.record("codex_user_runner", "fixture-model", "HEALTHY", reason="injected", source="fixture", observed_at=observed)
        real_config = router.effective_router_config()
        production_config = {**real_config, "production_enabled": True}
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as temp:
            ep = Path(temp) / "episode"
            ep.mkdir()
            candidate = ep / "meta/candidate.json"
            request_path = ep / "meta/request.json"
            with (patch.object(router, "effective_router_config", return_value=production_config),
                  patch.object(router, "build_registry", return_value=registry),
                  patch.object(router, "process_health_cache", return_value=health),
                  patch.object(router, "ROOT", Path(temp)),
                  patch.object(product_review_adapter, "_validate_attempt"),
                  patch.object(product_review_adapter, "request_path", return_value=request_path),
                  patch.object(product_review_adapter, "_request_exists", return_value=False),
                  patch.object(product_review_adapter, "_write_json"),
                  patch.object(product_review_adapter.episode_performance, "safe_begin_named_span")):
                prepared = product_review_adapter.prepare(
                    ep, kind="story-semantic-critic-shadow", runtime="WORK", attempt=1,
                    prompt="fixture only", source_paths=[source], candidate_path=candidate,
                    host_execution="workspace_provider", request_metadata={"stage": "STORY"})
        self.assertEqual(prepared["effective_execution_target"]["provider"], "codex_user_runner")
        self.assertEqual(prepared["capability_route_decision"]["effective_action"], "FALLBACK")
        self.assertTrue(prepared["scheduler_dispatch_required"])
        self.assertFalse(prepared["actual_dispatch_changed"])

    def test_cutover_recheck_never_enables_production(self):
        result = router.cutover_recheck(gate_path=ROOT / "missing-p4-gate.json",
                                        p3_closure_sha256="frozen")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["production_enabled"])

    def test_route_determinism(self):
        first = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                                     ("codex_user_runner", "fixture-model", "HEALTHY", 0)])
        second = self.route(statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                                      ("codex_user_runner", "fixture-model", "HEALTHY", 0)])
        for key in ("effective_action", "effective_route", "reason", "rejected_candidates",
                    "policy_sha256", "config_sha256", "registry_sha256", "health_snapshot_sha256"):
            self.assertEqual(first[key], second[key])


if __name__ == "__main__":
    unittest.main()
