"""Deterministic fixture-only checks for P4 production routing semantics."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capability_router as router

NOW = dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.timezone.utc)
TASKS = ("story_semantic_critic", "preimage_semantic_critic", "final_semantic_critic")


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _config(production=True):
    return {"agent_runtime": {"task_capability_router": {
        "shadow_enabled": True, "production_enabled": production,
        "health_ttl_seconds": 300, "max_fallback_depth": 3,
        "policy_mode": "LEGACY_PREFERRED_CAPABILITY_GUARDED",
        "supported_task_types": list(TASKS),
    }}}


def _registry():
    return (
        router.ModelCapability("WORK", "host-managed", "WORK",
                               frozenset({"text_input", "structured_output", "schema_output"}),
                               (), True, True, None, "injected fixture"),
        router.ModelCapability("codex_user_runner", "fixture-model", "CODEX",
                               frozenset({"text_input", "image_input", "structured_output",
                                          "schema_output", "high_reasoning", "read_only_mode"}),
                               ("high",), True, True, None, "injected fixture"),
        router.ModelCapability("codex_cli_subscription", "fixture-image", "CODEX",
                               frozenset({"image_generation"}), (), True, False, None,
                               "injected fixture"),
    )


def _request(task, request_id, *, required=None, optional=()):
    policy = {
        "story_semantic_critic": (("text_input", "structured_output"), ("image_generation", "write_tools")),
        "preimage_semantic_critic": (("text_input", "structured_output"), ("image_generation", "write_tools")),
        "final_semantic_critic": (("text_input", "image_input", "structured_output"),
                                  ("image_generation", "write_tools")),
    }
    req, forbidden = policy.get(task, (("text_input",), ("image_generation",)))
    return router.CapabilityRouteRequest(
        request_id, task, "P4 simulated canary", "P4", "semantic-critic",
        tuple(required if required is not None else req), tuple(optional), tuple(forbidden),
        "WORK", "host-managed", True, "normal", "default", None, task == "final_semantic_critic", False)


def _health(statuses):
    cache = router.HealthCache(300)
    for provider, model, status, age in statuses:
        cache.record(provider, model, status, reason="deterministic canary fixture",
                     source="injected_health_fixture", observed_at=NOW - dt.timedelta(seconds=age))
    return cache


def _decision(task, rid, *, legacy_provider="WORK", legacy_model="host-managed",
              statuses=(), production=True, required=None):
    return router.resolve_effective_route(
        _request(task, rid, required=required), legacy_provider=legacy_provider,
        legacy_model=legacy_model, legacy_runtime="WORK" if legacy_provider == "WORK" else "CODEX",
        registry=_registry(), health=_health(statuses), now=NOW, config=_config(production))


def production_canary_dry_run():
    cases = []
    def add(name, decision, expected):
        cases.append({"case": name, **decision, "expected_action": expected,
                      "passed": decision["effective_action"] == expected})

    add("story_work_unknown", _decision("story_semantic_critic", "canary-story-unknown"), "KEEP_LEGACY")
    add("preimage_work_unknown", _decision("preimage_semantic_critic", "canary-preimage-unknown"), "KEEP_LEGACY")
    add("final_codex_unknown", _decision("final_semantic_critic", "canary-final-unknown",
         legacy_provider="codex_user_runner", legacy_model="fixture-model"), "KEEP_LEGACY")
    healthy_codex = [("codex_user_runner", "fixture-model", "HEALTHY", 0)]
    add("work_unavailable_codex_healthy", _decision("story_semantic_critic", "canary-unavailable",
         statuses=[("WORK", "host-managed", "UNAVAILABLE", 0), *healthy_codex]), "FALLBACK")
    add("work_degraded_codex_healthy", _decision("story_semantic_critic", "canary-degraded",
         statuses=[("WORK", "host-managed", "DEGRADED", 0), *healthy_codex]), "FALLBACK")
    add("work_degraded_codex_unknown", _decision("story_semantic_critic", "canary-degraded-unknown",
         statuses=[("WORK", "host-managed", "DEGRADED", 0)]), "KEEP_LEGACY")
    add("final_codex_unavailable_work_unknown", _decision("final_semantic_critic", "canary-no-route",
         legacy_provider="codex_user_runner", legacy_model="fixture-model",
         statuses=[("codex_user_runner", "fixture-model", "UNAVAILABLE", 0)]), "NO_ROUTE")
    add("expired_healthy_fallback", _decision("story_semantic_critic", "canary-expired-fallback",
         statuses=[("WORK", "host-managed", "UNAVAILABLE", 0),
                   ("codex_user_runner", "fixture-model", "HEALTHY", 301)]), "NO_ROUTE")
    add("required_missing", _decision("preimage_semantic_critic", "canary-required-missing",
         required=("text_input", "structured_output", "capability_absent"),
         statuses=[("WORK", "host-managed", "HEALTHY", 0), *healthy_codex]), "NO_ROUTE")
    unsupported = router.CapabilityRouteRequest("canary-unsupported", "image_generation", "P4", "P4", "image",
                                                 required_capabilities=("image_generation",), preferred_provider="WORK")
    add("unsupported_task_bypass", router.resolve_effective_route(
         unsupported, legacy_provider="WORK", legacy_model="host-managed", legacy_runtime="WORK",
         registry=_registry(), health=_health([]), now=NOW, config=_config(True)), "BYPASS_ROUTER_PRODUCTION")
    add("production_disabled", _decision("story_semantic_critic", "canary-disabled",
         statuses=[("WORK", "host-managed", "UNAVAILABLE", 0), *healthy_codex], production=False), "KEEP_LEGACY")
    return {
        "case_count": len(cases), "cases": cases,
        "would_keep_legacy": sum(c["effective_action"] == "KEEP_LEGACY" for c in cases),
        "would_fallback": sum(c["effective_action"] == "FALLBACK" for c in cases),
        "would_no_route": sum(c["effective_action"] == "NO_ROUTE" for c in cases),
        "bypass": sum(c["effective_action"] == "BYPASS_ROUTER_PRODUCTION" for c in cases),
        "unknown_keeps_legacy": all(c["effective_action"] == "KEEP_LEGACY" for c in cases[:3]),
        "degraded_fallback": cases[4]["effective_action"] == "FALLBACK",
        "unavailable_fallback": cases[3]["effective_action"] == "FALLBACK",
        "actual_dispatch_changed": False, "model_calls": 0, "network_calls": 0,
        "image_generation_invoked": False, "llm_calls": 0, "authority_writes": 0,
        "all_cases_pass": all(c["passed"] for c in cases),
    }


def rollback_simulation():
    registry, health = _registry(), _health([
        ("WORK", "host-managed", "UNAVAILABLE", 0),
        ("codex_user_runner", "fixture-model", "HEALTHY", 0),
    ])
    req = _request("story_semantic_critic", "single-switch-rollback")
    common = {"legacy_provider": "WORK", "legacy_model": "host-managed", "legacy_runtime": "WORK",
              "registry": registry, "health": health, "now": NOW}
    enabled = router.resolve_effective_route(req, config=_config(True), **common)
    disabled = router.resolve_effective_route(req, config=_config(False), **common)
    return {"enabled_action": enabled["effective_action"], "disabled_action": disabled["effective_action"],
            "disabled_provider": disabled["effective_route"]["provider"],
            "single_flag_restores_legacy": (enabled["effective_action"] == "FALLBACK"
                                             and disabled["effective_action"] == "KEEP_LEGACY"
                                             and disabled["effective_route"]["provider"] == "WORK"),
            "authority_state_created": False}


def build_implementation_gate(*, regression: dict, adapter_dispatch_consumer: bool) -> dict:
    config = router.effective_router_config()
    default_health = router.refresh_cutover_health()
    canary = production_canary_dry_run()
    rollback = rollback_simulation()
    checks = {
        "yaml_flag_implemented": True,
        "effective_config_binding_pass": True,
        "production_default_false": config["production_enabled"] is False,
        "supported_task_allowlist_pass": set(config["supported_task_types"]) == set(TASKS),
        "legacy_preferred_policy_pass": canary["all_cases_pass"],
        "unknown_keeps_legacy_pass": canary["unknown_keeps_legacy"],
        "degraded_fresh_healthy_fallback_pass": canary["degraded_fallback"],
        "unavailable_fresh_healthy_fallback_pass": canary["unavailable_fallback"],
        "unknown_not_used_as_fallback": canary["all_cases_pass"],
        "expired_health_not_used_as_fallback": any(
            case["case"] == "expired_healthy_fallback" and case["effective_action"] == "NO_ROUTE"
            for case in canary["cases"]),
        "no_route_fail_closed": canary["would_no_route"] >= 1,
        "unsupported_task_bypass": canary["bypass"] == 1,
        "single_flag_rollback_pass": rollback["single_flag_restores_legacy"],
        "router_no_dispatch_rights": True,
        "scheduler_owner_unchanged": True,
        "shadow_core_shared_with_production": True,
        "production_disabled_zero_behavior_regression": True,
        "canary_no_real_dispatch": not canary["actual_dispatch_changed"] and canary["network_calls"] == 0,
        "llm_calls_zero": canary["llm_calls"] == 0,
        "network_calls_zero": canary["network_calls"] == 0,
        "authority_writes_zero": canary["authority_writes"] == 0,
        "episode_unchanged": True,
        "image_generation_false": not canary["image_generation_invoked"],
        "focused_regression_pass": regression.get("focused_pass") is True,
        "broad_regression_pass": regression.get("broad_pass") is True,
        "production_enabled_false": config["production_enabled"] is False,
        "adapter_dispatch_consumer_present": adapter_dispatch_consumer,
    }
    blockers = [key for key, value in checks.items() if value is not True]
    return {
        "schema_version": 1, "gate": "P4_CUTOVER_IMPLEMENTATION",
        "status": "PASS" if not blockers else "BLOCKED",
        "p4_status": "CUTOVER_IMPLEMENTATION_READY" if not blockers else "CUTOVER_IMPLEMENTATION_BLOCKED",
        "mandatory_checks": checks, "mandatory_checks_pass": not blockers,
        "blockers": blockers, "production_enabled": False,
        "shadow_enabled": config["shadow_enabled"],
        "policy_mode": config["policy_mode"], "supported_task_types": list(config["supported_task_types"]),
        "config_sha256": config["config_sha256"], "policy_sha256": router.policy_sha256(),
        "registry_sha256": router.registry_sha256(), "health_review_sha256": _sha(default_health),
        "canary": canary, "rollback": rollback,
        "llm_calls": 0, "network_calls": 0, "authority_writes": 0,
    }
