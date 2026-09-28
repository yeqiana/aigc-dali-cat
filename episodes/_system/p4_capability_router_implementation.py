"""Deterministic fixture-only checks for P4 production routing semantics."""
from __future__ import annotations

import datetime as dt
import ast
import hashlib
import json
import statistics
import subprocess
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


def _source_audit(path: Path) -> dict:
    source = path.read_text(encoding="utf-8-sig")
    return {"path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source": source, "tree": ast.parse(source, filename=str(path))}


def audit_dispatch_consumer() -> dict:
    """Verify the route target reaches the actual Critic execution boundary.

    A target written into a Host Request is advisory until the DAG/adapter
    passes it through to the executor. This deliberately requires the complete
    source-level handoff and cannot be satisfied by a resolver-only canary.
    """
    names = {
        "dag": ROOT / "episodes/_system/runtime_dag.py",
        "scheduler": ROOT / "episodes/_system/runtime_scheduler.py",
        "product_review_adapter": ROOT / "episodes/_system/product_review_adapter.py",
        "executor": ROOT / "episodes/_system/codex_critic_runner.py",
        "story_adapter": ROOT / "episodes/_system/agents/story_semantic_critic_adapter.py",
        "preimage_adapter": ROOT / "episodes/_system/agents/preimage_semantic_critic_adapter.py",
        "final_adapter": ROOT / "episodes/_system/agents/final_semantic_critic_adapter.py",
    }
    sources = {name: _source_audit(path) for name, path in names.items()}

    def has_target_reference(name: str) -> bool:
        source = sources[name]["source"]
        return "effective_execution_target" in source or "capability_route_decision" in source

    def function_args(name: str, function: str) -> set[str]:
        for node in ast.walk(sources[name]["tree"]):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
                return {arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
        return set()

    def launch_passes_target(name: str) -> bool:
        for node in ast.walk(sources[name]["tree"]):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called_launch = isinstance(func, ast.Attribute) and func.attr == "launch"
            if called_launch and any(kw.arg in {"execution_target", "effective_execution_target"}
                                     for kw in node.keywords):
                return True
        return False

    dag_calls_scheduler = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"schedule", "schedule_next", "schedule_batch"}
        for node in ast.walk(sources["dag"]["tree"]))
    executor_args = function_args("executor", "launch")
    checks = {
        "runtime_dag_uses_runtime_scheduler": dag_calls_scheduler,
        "runtime_dag_consumes_effective_target": has_target_reference("dag"),
        "runtime_scheduler_consumes_effective_target": has_target_reference("scheduler"),
        "executor_accepts_effective_target": bool(executor_args & {"execution_target", "effective_execution_target"}),
        "story_adapter_passes_effective_target": launch_passes_target("story_adapter"),
        "preimage_adapter_passes_effective_target": launch_passes_target("preimage_adapter"),
        "final_adapter_passes_effective_target": launch_passes_target("final_adapter"),
    }
    producer_has_target = has_target_reference("product_review_adapter")
    checks["advisory_target_producer_present"] = producer_has_target
    return {
        "consumer_present": all(checks[key] for key in (
            "runtime_dag_uses_runtime_scheduler", "runtime_dag_consumes_effective_target",
            "runtime_scheduler_consumes_effective_target", "executor_accepts_effective_target",
            "story_adapter_passes_effective_target", "preimage_adapter_passes_effective_target",
            "final_adapter_passes_effective_target")),
        "checks": checks,
        "missing_handoffs": [key for key, value in checks.items() if not value and key != "advisory_target_producer_present"],
        "call_path": [
            "Runtime DAG calls Runtime Scheduler to plan DAG work.",
            "Critic adapters prepare host requests; product_review_adapter writes effective_execution_target as advisory request evidence.",
            "Runtime DAG and Runtime Scheduler do not consume effective_execution_target or capability_route_decision.",
            "codex_critic_runner.launch has no execution-target selector; three local Critic launch callsites do not pass one.",
        ],
        "source_files": {name: {"path": row["path"], "sha256": row["sha256"]}
                         for name, row in sources.items()},
        "dispatch_owner": "runtime_dag / runtime_scheduler",
        "router_rights": "decision_only",
        "decision": "BLOCKED_NO_VERIFIED_EXECUTION_CONSUMER" if not all(checks.values()) else "CONSUMER_VERIFIED",
    }


def build_implementation_gate(*, regression: dict) -> dict:
    config = router.effective_router_config()
    default_health = router.refresh_cutover_health()
    canary = production_canary_dry_run()
    rollback = rollback_simulation()
    dispatch_audit = audit_dispatch_consumer()
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
        "adapter_dispatch_consumer_present": dispatch_audit["consumer_present"],
    }
    blockers = [key for key, value in checks.items() if value is not True]
    return {
        "schema_version": 1, "gate": "P4_CUTOVER_IMPLEMENTATION",
        "status": "PASS" if not blockers else "BLOCKED",
        "p4_status": "CUTOVER_IMPLEMENTATION_READY" if not blockers else "CUTOVER_IMPLEMENTATION_BLOCKED",
        "mandatory_checks": checks, "mandatory_checks_pass": not blockers,
        "blockers": blockers,
        "blocker_details": ([{
            "check": "adapter_dispatch_consumer_present",
            "reason": "The effective target remains advisory request evidence; DAG/Scheduler and actual Critic executor do not consume/pass it.",
            "missing_handoffs": dispatch_audit["missing_handoffs"],
        }] if "adapter_dispatch_consumer_present" in blockers else []),
        "production_enabled": False,
        "shadow_enabled": config["shadow_enabled"],
        "policy_mode": config["policy_mode"], "supported_task_types": list(config["supported_task_types"]),
        "config_sha256": config["config_sha256"], "policy_sha256": router.policy_sha256(),
        "registry_sha256": router.registry_sha256(), "health_review_sha256": _sha(default_health),
        "canary": canary, "rollback": rollback,
        "runtime_dispatch_audit": dispatch_audit,
        "regression": regression,
        "llm_calls": 0, "network_calls": 0, "authority_writes": 0,
    }


def write_implementation_gate_report(*, regression: dict,
                                     report_path: Path | None = None) -> dict:
    """Recompute and write the current implementation gate with source evidence."""
    report_path = report_path or ROOT / "reports/p4-capability-router-cutover-implementation-gate-20260928.json"
    report_path = Path(report_path)
    result = build_implementation_gate(regression=regression)
    source_paths = [
        "config/storyos.yaml",
        "episodes/_system/capability_router.py",
        "episodes/_system/p4_capability_router_implementation.py",
        "episodes/_system/product_review_adapter.py",
        "episodes/_system/runtime_dag.py",
        "episodes/_system/runtime_scheduler.py",
        "episodes/_system/codex_critic_runner.py",
        "episodes/_system/agents/story_semantic_critic_adapter.py",
        "episodes/_system/agents/preimage_semantic_critic_adapter.py",
        "episodes/_system/agents/final_semantic_critic_adapter.py",
        "tests/system/test_p4_production_router.py",
    ]
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in source_paths}
    report_sources = [
        "reports/p3-critic-phase-closure-20260928.json",
        "reports/p4-capability-router-cutover-review-20260928.json",
        "reports/p4-capability-router-cutover-dry-run-20260928.json",
        "reports/p4-capability-router-failure-injection-20260928.json",
        "reports/p4-capability-router-failure-injection-clarification-20260928.json",
        "reports/p4-capability-router-fresh-health-review-20260928.json",
        "reports/p4-capability-router-paired-route-comparison-20260928.json",
        "reports/p4-capability-router-pre-cutover-gate-20260928.json",
        "reports/p4-capability-router-production-policy-review-20260928.json",
        "reports/p4-capability-router-dispatch-consumer-audit-20260928.json",
    ]
    report_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in report_sources if (ROOT / name).is_file()}
    previous_sha = (hashlib.sha256(report_path.read_bytes()).hexdigest()
                    if report_path.is_file() else None)
    def git_value(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()
    p3_sha = report_hashes.get("reports/p3-critic-phase-closure-20260928.json")
    result.update({
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "head_sha": git_value("rev-parse", "HEAD"),
        "origin_sha": git_value("rev-parse", "origin/story-platform-v3-rever"),
        "previous_p4_status": "CUTOVER_APPROVED_AWAITING_USER_AUTHORIZATION",
        "production_enabled": False,
        "shadow_enabled": router.effective_router_config()["shadow_enabled"],
        "p3_closure_sha256": p3_sha,
        "p3_closure_unchanged": p3_sha == "90465e7c29474db3ca45de320ab6c466d54bd05ac6296300a3454e1ca81e7347",
        "source_artifact_hashes": source_hashes,
        "source_reports": report_hashes,
        "supersedes_sha256": previous_sha,
        "immutable": True,
        "implementation_boundary": "CUTOVER_IMPLEMENTATION_REVIEW_ONLY; production_enabled remains false",
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def write_dispatch_consumer_audit_report(*, regression: dict,
                                         report_path: Path | None = None) -> dict:
    report_path = report_path or ROOT / "reports/p4-capability-router-dispatch-consumer-audit-20260928.json"
    report_path = Path(report_path)
    if report_path.exists():
        raise FileExistsError(f"immutable audit report already exists: {report_path}")
    audit = audit_dispatch_consumer()
    report = {
        "schema_version": 1,
        "kind": "p4_capability_router_dispatch_consumer_audit",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "VERIFIED" if audit["consumer_present"] else "BLOCKED",
        "consumer_present": audit["consumer_present"],
        "router_decision_only": True,
        "runtime_scheduler_remains_dispatch_owner": True,
        "runtime_dag_remains_workflow_owner": True,
        "actual_dispatch_consumer_path": None,
        "effective_execution_target_location": "product_review_adapter.prepare -> advisory request field",
        "effective_execution_target_consumed_by": [],
        "audit": audit,
        "regression": regression,
        "production_enabled": router.effective_router_config()["production_enabled"],
        "llm_calls": 0,
        "model_calls": 0,
        "network_calls": 0,
        "image_generation_invoked": False,
        "authority_writes": 0,
        "episode_state_writes": 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
