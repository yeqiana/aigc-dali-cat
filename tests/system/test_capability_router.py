"""P4 deterministic task routing and shadow-only contract tests."""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import capability_router as router
import product_review_adapter
import runtime_router
import runtime_scheduler


UTC = dt.timezone.utc
NOW = dt.datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def model(provider, name, capabilities, *, runtime="WORK", reasoning=("medium", "high")):
    return router.ModelCapability(provider, name, runtime, frozenset(capabilities),
                                  tuple(reasoning), True, "structured_output" in capabilities,
                                  None, "deterministic test fixture")


def request(task="text_generation", **kwargs):
    return router.CapabilityRouteRequest(
        request_id=kwargs.pop("request_id", "fixture-1"), task_type=task,
        execution_domain="test", stage="TEST", agent="fixture", **kwargs)


TEXT = {"text_input", "structured_output", "high_reasoning"}


class CapabilityRouterTests(unittest.TestCase):
    def test_required_capability_filter(self):
        rows = (model("WORK", "text", TEXT), model("codex_user_runner", "other", {"text_input"}, runtime="CODEX"))
        out = router.resolve(request(required_capabilities=("json_schema",)), registry=rows, now=NOW)
        self.assertEqual(out["status"], "NO_ROUTE")
        self.assertTrue(all("missing_required_capability" in row["reasons"] for row in out["rejected_candidates"]))

    def test_forbidden_capability_filter(self):
        rows = (model("WORK", "tool-writer", TEXT | {"write_tools"}),)
        out = router.resolve(request(forbidden_capabilities=("write_tools",)), registry=rows, now=NOW)
        self.assertEqual(out["status"], "NO_ROUTE")
        self.assertEqual(out["rejected_candidates"][0]["reasons"], ["forbidden_capability_present"])

    def test_optional_capability_nonblocking(self):
        rows = (model("WORK", "text", {"text_input"}),)
        out = router.resolve(request(optional_capabilities=("cached_input",)), registry=rows, now=NOW)
        self.assertEqual(out["status"], "ROUTE")
        self.assertEqual(out["matched_optional_capabilities"], [])

    def test_health_ttl_expiry_becomes_unknown_and_selectable(self):
        cache = router.HealthCache(10)
        cache.record("WORK", "text", "HEALTHY", reason="receipt ok", source="runner_receipt", observed_at=NOW)
        before = cache.get("WORK", "text", now=NOW + dt.timedelta(seconds=9))
        after = cache.get("WORK", "text", now=NOW + dt.timedelta(seconds=10))
        self.assertEqual(before.status, "HEALTHY")
        self.assertEqual(after.status, "UNKNOWN")
        out = router.resolve(request(), registry=(model("WORK", "text", {"text_input"}),),
                             health=cache, now=NOW + dt.timedelta(seconds=10))
        self.assertEqual(out["health_status"], "UNKNOWN")
        self.assertEqual(out["status"], "ROUTE")

    def test_technical_failure_health_recovers_on_success(self):
        cache = router.HealthCache(15)
        degraded = router.record_execution_outcome(
            cache, "WORK", None, successful=False, failure_type="technical_failure",
            reason="429 Too Many Requests")
        recovered = router.record_execution_outcome(cache, "WORK", None, successful=True,
                                                    reason="retry2 succeeded")
        self.assertEqual(degraded.status, "DEGRADED")
        self.assertEqual(recovered.status, "HEALTHY")
        quality = router.record_execution_outcome(
            cache, "WORK", None, successful=False, failure_type="quality_failure")
        self.assertEqual(quality.status, "HEALTHY")

    def test_unhealthy_preferred_uses_bounded_fallback(self):
        rows = (model("WORK", "preferred", TEXT), model("codex_user_runner", "fallback", TEXT, runtime="CODEX"))
        cache = router.HealthCache(30)
        cache.record("WORK", "preferred", "DEGRADED", reason="technical failure 429",
                     source="execution_telemetry", observed_at=NOW)
        req = request("critic", request_id="fallback", preferred_provider="WORK",
                      preferred_model="preferred", required_capabilities=tuple(TEXT))
        out = router.resolve(req, registry=rows, health=cache, now=NOW)
        self.assertEqual((out["selected_provider"], out["selected_model"]), ("codex_user_runner", "fallback"))
        self.assertTrue(out["fallback_used"])
        self.assertEqual(out["rejected_candidates"][0]["reasons"], ["provider_unhealthy"])

    def test_no_route_fails_closed(self):
        out = router.resolve(request(required_capabilities=("secret_capability",)),
                             registry=(model("WORK", "text", {"text_input"}),), now=NOW)
        self.assertEqual(out["status"], "NO_ROUTE")
        self.assertIsNone(out["selected_provider"])
        self.assertEqual(out["authority_writes"], 0)

    def test_all_candidates_unavailable_returns_no_route(self):
        rows = (model("WORK", "text", {"text_input"}),
                model("codex_user_runner", "cli", {"text_input"}, runtime="CODEX"))
        cache = router.HealthCache(20)
        for row in rows:
            cache.record(row.provider, row.model, "UNAVAILABLE", reason="host unavailable",
                         source="provider_availability", observed_at=NOW)
        out = router.resolve(request(), registry=rows, health=cache, now=NOW)
        self.assertEqual(out["status"], "NO_ROUTE")
        self.assertTrue(all("provider_unhealthy" in row["reasons"] for row in out["rejected_candidates"]))

    def test_fallback_cycle_is_bounded(self):
        row = model("WORK", "same", {"image_generation"})
        req = request(request_id="cycle", required_capabilities=("text_input",),
                      preferred_provider="WORK", preferred_model="same")
        out = router.resolve(req, registry=(row, row, row, row, row), now=NOW)
        self.assertEqual(out["status"], "NO_ROUTE")
        self.assertLessEqual(out["fallback_depth"], router.MAX_FALLBACK_DEPTH)
        candidates = [(x["provider"], x["model"]) for x in out["rejected_candidates"]]
        self.assertEqual(len(candidates), len(set(candidates)))

    def test_deterministic_same_input_same_route(self):
        rows = (model("WORK", "text", TEXT), model("codex_user_runner", "other", TEXT, runtime="CODEX"))
        req = request("critic", required_capabilities=tuple(TEXT), preferred_provider="WORK")
        one = router.resolve(req, registry=rows, now=NOW)
        two = router.resolve(req, registry=rows, now=NOW)
        fields = ("status", "selected_provider", "selected_model", "selected_runtime",
                  "selection_reason", "rejected_candidates", "policy_sha256",
                  "config_sha256", "capability_registry_sha256", "health_snapshot_sha256")
        self.assertEqual({key: one[key] for key in fields}, {key: two[key] for key in fields})
        self.assertEqual(one["llm_calls"], 0)

    def test_resolver_has_no_dispatch_or_authority_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            before = list(Path(temp).iterdir())
            router.resolve(request(), registry=(model("WORK", "text", {"text_input"}),), now=NOW)
            self.assertEqual(before, list(Path(temp).iterdir()))
        self.assertFalse(hasattr(router, "dispatch"))
        self.assertFalse(hasattr(router, "write_authority"))

    def test_shadow_comparator_and_request_idempotence(self):
        rows = (model("WORK", "text", {"text_input"}),)
        req = request(request_id="same-id")
        with tempfile.TemporaryDirectory() as temp:
            first = router.observe_shadow(req, registry=rows, legacy_provider="WORK",
                                          legacy_model=None, legacy_runtime="WORK",
                                          evidence_root=Path(temp), now=NOW)
            second = router.observe_shadow(req, registry=rows, legacy_provider="WORK",
                                           legacy_model=None, legacy_runtime="WORK",
                                           evidence_root=Path(temp), now=NOW)
            self.assertTrue(first["comparison"]["route_equivalent"])
            self.assertTrue(second["actual_dispatch_unchanged"])
            self.assertEqual(first["evidence_sha256"], second["evidence_sha256"])
            evidence = json.loads(Path(first["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(evidence["comparison"]["actual_dispatch"],
                             {"provider": "WORK", "model": None, "runtime": "WORK"})

    def test_critic_task_policies_story_preimage_final(self):
        story, _, _, _ = router.critic_route_request(
            request_id="story", kind="story-semantic-critic-shadow", stage="P3",
            host_execution="workspace_provider", legacy_provider="WORK", legacy_model=None)
        preimage, _, _, _ = router.critic_route_request(
            request_id="preimage", kind="preimage-semantic-critic-shadow", stage="PREIMAGE",
            host_execution="workspace_provider", legacy_provider="WORK", legacy_model=None)
        final, _, _, _ = router.critic_route_request(
            request_id="final", kind="final-semantic-critic-shadow", stage="FINAL",
            host_execution="codex_user_runner_shadow", legacy_provider="codex_user_runner", legacy_model="vision")
        self.assertNotIn("image_input", story.required_capabilities)
        self.assertNotIn("image_input", preimage.required_capabilities)
        self.assertNotIn("high_reasoning", preimage.required_capabilities)
        self.assertIsNone(preimage.reasoning_requirement)
        self.assertIn("image_input", final.required_capabilities)
        self.assertIn("image_generation", final.forbidden_capabilities)
        self.assertEqual(router.task_policy("text_generation")["required"], ["text_input"])

    def test_story_preimage_final_shadow_routes_use_required_capabilities(self):
        rows = (model("WORK", "host-managed", {"text_input", "structured_output"}, reasoning=()),
                model("codex_user_runner", "fixture-high", TEXT | {"image_input"}, runtime="CODEX"),
                model("codex_cli_subscription", "image", {"image_generation"}, runtime="CODEX", reasoning=()))
        profiles = []
        for request_id, kind, host, provider, model_name in (
            ("story-shadow", "story-semantic-critic-shadow", "workspace_provider", "WORK", None),
            ("preimage-shadow", "preimage-semantic-critic-shadow", "workspace_provider", "WORK", None),
            ("final-shadow", "final-semantic-critic-shadow", "codex_user_runner_shadow", "codex_user_runner", "fixture-high"),
        ):
            req, legacy_provider, legacy_model, legacy_runtime = router.critic_route_request(
                request_id=request_id, kind=kind, stage="P4", host_execution=host,
                legacy_provider=provider, legacy_model=model_name)
            decision = router.resolve(req, registry=rows, now=NOW)
            comparison = router.compare_shadow(req, decision, legacy_provider=legacy_provider,
                                               legacy_model=legacy_model, legacy_runtime=legacy_runtime)
            profiles.append((req, decision, comparison))
        self.assertEqual(profiles[0][1]["selected_provider"], "WORK")
        self.assertEqual(profiles[1][1]["selected_provider"], "WORK")
        self.assertEqual(profiles[2][1]["selected_provider"], "codex_user_runner")
        self.assertTrue(profiles[2][2]["route_equivalent"])
        self.assertTrue(all(row[2]["actual_dispatch_unchanged"] for row in profiles))
        self.assertTrue(all(row[1]["authority_writes"] == 0 and row[1]["llm_calls"] == 0 for row in profiles))

    def test_product_review_shadow_hook_preserves_legacy_request(self):
        source = ROOT / "tests/fixtures/p3_story_semantic/pass_ordinary/story.md"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as temp:
            ep = Path(temp) / "episode"
            ep.mkdir()
            candidate = ep / "meta" / "candidate.json"
            request_path = ep / "meta" / "request.json"
            with patch.object(product_review_adapter, "_validate_attempt"), \
                 patch.object(product_review_adapter, "request_path", return_value=request_path), \
                 patch.object(product_review_adapter, "_request_exists", return_value=False), \
                 patch.object(product_review_adapter, "_write_json"), \
                 patch.object(product_review_adapter.episode_performance, "safe_begin_named_span"), \
                 patch.object(runtime_router, "capability_route_shadow") as observe:
                prepared = product_review_adapter.prepare(
                    ep, kind="story-semantic-critic-shadow", runtime="WORK", attempt=1,
                    prompt="fixture only", source_paths=[source], candidate_path=candidate,
                    host_execution="workspace_provider")
            self.assertEqual(prepared["host_execution"], "workspace_provider")
            self.assertEqual(prepared["review_execution_contract"]["host_execution"], "workspace_provider")
            self.assertNotIn("effective_execution_target", prepared)
            self.assertNotIn("capability_route_decision", prepared)
            observe.assert_called_once()
            route_request = observe.call_args.args[0]
            self.assertEqual(route_request.task_type, "story_semantic_critic")
            self.assertEqual(observe.call_args.kwargs["legacy_provider"], "WORK")

    def test_shadow_observation_error_does_not_block_legacy_request(self):
        source = ROOT / "tests/fixtures/p3_story_semantic/pass_ordinary/story.md"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as temp:
            ep = Path(temp) / "episode"
            ep.mkdir()
            with patch.object(product_review_adapter, "_validate_attempt"), \
                 patch.object(product_review_adapter, "request_path", return_value=ep / "meta/request.json"), \
                 patch.object(product_review_adapter, "_request_exists", return_value=False), \
                 patch.object(product_review_adapter, "_write_json"), \
                 patch.object(product_review_adapter.episode_performance, "safe_begin_named_span"), \
                 patch.object(runtime_router, "capability_route_shadow", side_effect=OSError("shadow unavailable")):
                prepared = product_review_adapter.prepare(
                    ep, kind="preimage-semantic-critic-shadow", runtime="WORK", attempt=1,
                    prompt="fixture only", source_paths=[source], candidate_path=ep / "meta/candidate.json",
                    host_execution="workspace_provider")
            self.assertEqual(prepared["host_execution"], "workspace_provider")

    def test_final_critic_hook_keeps_codex_legacy_route_and_image_requirement(self):
        source = ROOT / "tests/fixtures/p3_story_semantic/pass_ordinary/story.md"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as temp:
            ep = Path(temp) / "episode"
            ep.mkdir()
            with patch.object(product_review_adapter, "_validate_attempt"), \
                 patch.object(product_review_adapter, "request_path", return_value=ep / "meta/request.json"), \
                 patch.object(product_review_adapter, "_request_exists", return_value=False), \
                 patch.object(product_review_adapter, "_write_json"), \
                 patch.object(product_review_adapter.episode_performance, "safe_begin_named_span"), \
                 patch.object(runtime_router, "capability_route_shadow") as observe:
                prepared = product_review_adapter.prepare(
                    ep, kind="final-semantic-critic-shadow", runtime="WORK", attempt=1,
                    prompt="fixture only", source_paths=[source], candidate_path=ep / "meta/candidate.json",
                    host_execution="codex_user_runner_shadow")
            self.assertEqual(prepared["host_execution"], "codex_user_runner_shadow")
            self.assertEqual(observe.call_args.kwargs["legacy_provider"], "codex_user_runner")
            self.assertIn("image_input", observe.call_args.args[0].required_capabilities)
            self.assertIn("image_generation", observe.call_args.args[0].forbidden_capabilities)

    def test_runtime_router_facade_keeps_production_disabled(self):
        config = runtime_router.capability_router_config()
        self.assertTrue(config["shadow_enabled"])
        self.assertFalse(config["production_enabled"])
        self.assertEqual(config["health_ttl_seconds"], router.HEALTH_TTL_SECONDS)

    def test_runtime_scheduler_remains_runnable_owner(self):
        node = {"node_id": "scheduled-critic", "node_type": "review", "depends_on": [],
                "input_contract": {}, "output_contract": {}, "retry_policy": {},
                "priority": "HIGH", "evidence_required": [],
                "execution_policy": {"mode": "serial", "parallel_safe": False,
                                     "resource_class": "text", "max_concurrency": 1}}
        wave = runtime_scheduler.schedule([node])
        legacy_dispatch = json.loads(json.dumps(wave["dispatch"]))
        req = request("text_generation", request_id="scheduled-shadow", required_capabilities=("text_input",))
        with tempfile.TemporaryDirectory() as temp:
            observation = router.observe_shadow(req, registry=(model("WORK", "text", {"text_input"}),),
                                                legacy_provider="WORK", legacy_model="text",
                                                legacy_runtime="WORK", evidence_root=Path(temp), now=NOW)
        self.assertEqual(wave["dispatch"], legacy_dispatch)
        self.assertEqual(wave["dispatch"][0]["node_id"], "scheduled-critic")
        self.assertTrue(observation["comparison"]["actual_dispatch_unchanged"])
        self.assertFalse(hasattr(router, "dispatch"))

    def test_current_registry_has_no_fabricated_providers(self):
        providers = {row.provider for row in router.build_registry(cli_model=("gpt-5.6-terra", "high"))}
        self.assertEqual(providers, {"WORK", "codex_user_runner", "codex_cli_subscription"})


if __name__ == "__main__":
    unittest.main()
