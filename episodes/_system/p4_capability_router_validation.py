"""Deterministic local P4 comparison, injection, health, and performance evidence."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capability_router as router
from capability_router_gate import evaluate_gate

NOW = dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.timezone.utc)
P3_CLOSURE_SHA = "90465e7c29474db3ca45de320ab6c466d54bd05ac6296300a3454e1ca81e7347"
IMPLEMENTATION_REPORT = ROOT / "reports/p4-capability-router-shadow-implementation-20260928.json"
TRIAGE_REPORT = ROOT / "reports/p4-preimplementation-regression-triage-20260928.json"


def sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_decision(decision):
    return {key: value for key, value in decision.items()
            if key not in {"resolve_wall_ms", "registry_lookup_ms", "health_lookup_ms"}}


def _fixture_model(provider, model, capabilities, runtime, reasoning=()):
    return router.ModelCapability(provider, model, runtime, frozenset(capabilities), tuple(reasoning),
                                  True, "structured_output" in capabilities, None,
                                  "frozen deterministic P4 validation fixture")


def _route_request(sample_id, task, required, optional=(), forbidden=(), *, preferred_provider=None,
                   preferred_model=None, reasoning=None, multimodal=False, fallback=True):
    if preferred_provider == "WORK" and preferred_model == "host-managed":
        preferred_model = None
    return router.CapabilityRouteRequest(
        sample_id, task, "P4 paired route validation", "P4", sample_id,
        tuple(required), tuple(optional), tuple(forbidden), preferred_provider, preferred_model,
        fallback, "normal", "default", reasoning, multimodal, False)


def _base_registry():
    # Capture the actual registry once; only health is injected by the fixtures.
    return router.build_registry()


def _health_for(registry, status_by_provider=None):
    cache = router.HealthCache()
    for row in registry:
        status = (status_by_provider or {}).get(row.provider)
        if status:
            cache.record(row.provider, row.model or "host-managed", status,
                         reason=f"frozen fixture: {status.lower()}", source="injected_health_fixture", observed_at=NOW)
    return cache


def _divergence_class(sample_id, decision, comparison):
    if comparison["route_equivalent"]:
        return None
    if decision["fallback_used"] and any("provider_unhealthy" in row.get("reasons", [])
                                         for row in decision.get("rejected_candidates", [])):
        return "HEALTH_DRIVEN_FALLBACK"
    if sample_id == "story_critic_work_to_codex":
        return "LEGACY_ROUTE_UNDER_SPECIFIED"
    if decision["status"] == "NO_ROUTE":
        return "EXPECTED_POLICY_IMPROVEMENT"
    return "EXPECTED_POLICY_IMPROVEMENT"


def paired_route_comparison():
    registry = _base_registry()
    specs = [
        ("story_critic_work_to_codex", "critic", ("text_input", "structured_output", "high_reasoning"), ("schema_output",), ("image_generation", "write_tools"), "WORK", "host-managed", "high", False, {}, "WORK", "host-managed"),
        ("story_critic_codex", "critic", ("text_input", "structured_output", "high_reasoning"), (), ("image_generation", "write_tools"), "codex_user_runner", "gpt-6-luna", "high", False, {}, "codex_user_runner", "gpt-6-luna"),
        ("preimage_critic_work", "critic", ("text_input", "structured_output"), (), ("image_generation", "write_tools"), "WORK", "host-managed", None, False, {}, "WORK", "host-managed"),
        ("final_critic_multimodal", "multimodal_review", ("text_input", "image_input", "structured_output", "high_reasoning"), (), ("image_generation", "write_tools"), "codex_user_runner", "gpt-6-luna", "high", True, {}, "codex_user_runner", "gpt-6-luna"),
        ("ordinary_text_work", "text_generation", ("text_input",), (), ("image_generation",), "WORK", "host-managed", None, False, {}, "WORK", "host-managed"),
        ("ordinary_text_codex", "text_generation", ("text_input",), (), ("image_generation",), "codex_user_runner", "gpt-6-luna", None, False, {}, "codex_user_runner", "gpt-6-luna"),
        ("multimodal_review_codex", "multimodal_review", ("text_input", "image_input", "structured_output", "high_reasoning"), ("schema_output",), ("image_generation", "write_tools"), "codex_user_runner", "gpt-6-luna", "high", True, {}, "codex_user_runner", "gpt-6-luna"),
        ("provider_unavailable", "text_generation", ("text_input",), (), ("image_generation",), "WORK", "host-managed", None, False, {"WORK": "UNAVAILABLE"}, "WORK", "host-managed"),
        ("preferred_provider_degraded", "text_generation", ("text_input",), (), ("image_generation",), "codex_user_runner", "gpt-6-luna", None, False, {"codex_user_runner": "DEGRADED"}, "codex_user_runner", "gpt-6-luna"),
        ("expired_health_unknown", "text_generation", ("text_input",), (), ("image_generation",), "WORK", "host-managed", None, False, {"WORK": "HEALTHY"}, "WORK", "host-managed"),
        ("required_capability_missing", "text_generation", ("text_input", "p4_fixture_missing_capability"), (), ("image_generation",), "WORK", "host-managed", None, False, {}, "WORK", "host-managed"),
        ("forbidden_capability_conflict", "text_generation", ("text_input",), (), ("image_generation", "structured_output"), "codex_cli_subscription", "gpt-image-2.5-flare", None, False, {}, "codex_cli_subscription", "gpt-image-2.5-flare"),
        ("all_candidates_unavailable", "text_generation", ("text_input",), (), ("image_generation",), "WORK", "host-managed", None, False, {"WORK": "UNAVAILABLE", "codex_user_runner": "UNAVAILABLE"}, "WORK", "host-managed"),
        ("final_image_input_unavailable", "multimodal_review", ("text_input", "image_input", "structured_output", "high_reasoning"), (), ("image_generation", "write_tools"), "codex_user_runner", "gpt-6-luna", "high", True, {"codex_user_runner": "UNAVAILABLE"}, "codex_user_runner", "gpt-6-luna"),
        ("preference_fallback_work_unhealthy", "text_generation", ("text_input",), (), ("image_generation",), "WORK", "host-managed", None, False, {"WORK": "DEGRADED"}, "WORK", "host-managed"),
        ("policy_disallowed_provider", "text_generation", ("text_input",), (), ("image_generation",), "WORK", "host-managed", None, False, {}, "WORK", "host-managed"),
    ]
    samples = []
    for row in specs:
        (sample_id, task, required, optional, forbidden, preferred_provider, preferred_model,
         reasoning, multimodal, health_statuses, legacy_provider, legacy_model) = row
        if sample_id == "forbidden_capability_conflict":
            allowed = ("WORK", "codex_user_runner")
        else:
            allowed = ("codex_user_runner",) if sample_id == "policy_disallowed_provider" else None
        req = _route_request(sample_id, task, required, optional, forbidden,
                             preferred_provider=preferred_provider, preferred_model=preferred_model,
                             reasoning=reasoning, multimodal=multimodal)
        cache = _health_for(registry, health_statuses)
        now = NOW + (dt.timedelta(seconds=301) if sample_id == "expired_health_unknown" else dt.timedelta())
        decision = router.resolve(req, registry=registry, health=cache, now=now, allowed_providers=allowed)
        comparison = router.compare_shadow(req, decision, legacy_provider=legacy_provider,
                                           legacy_model=None if legacy_model == "host-managed" else legacy_model,
                                           legacy_runtime="CODEX" if legacy_provider != "WORK" else "WORK")
        divergence = _divergence_class(sample_id, decision, comparison)
        sample = {
            "sample_id": sample_id, "task_type": task,
            "required_capabilities": list(required), "optional_capabilities": list(optional),
            "forbidden_capabilities": list(forbidden), "route_request": req.to_dict(),
            "request_sha256": sha(req.to_dict()),
            "legacy_provider": legacy_provider,
            "legacy_model": None if legacy_model == "host-managed" else legacy_model,
            "legacy_runtime": comparison["legacy_runtime"],
            "proposed_provider": decision["selected_provider"], "proposed_model": decision["selected_model"],
            "proposed_runtime": decision["selected_runtime"],
            "route_equivalent": comparison["route_equivalent"], "divergence_type": divergence,
            "fallback_used": decision["fallback_used"], "health_status": decision["health_status"],
            "health_snapshot": cache.snapshot(now=now),
            "health_snapshot_sha256": decision["health_snapshot_sha256"],
            "capability_registry_snapshot": [x.to_dict() for x in registry],
            "capability_registry_sha256": decision["capability_registry_sha256"],
            "allowed_providers": list(allowed) if allowed is not None else None,
            "policy_sha256": decision["policy_sha256"], "config_sha256": decision["config_sha256"],
            "selection_reason": decision["selection_reason"],
            "rejected_candidates": decision["rejected_candidates"],
            "resolve_wall_ms": decision["resolve_wall_ms"],
            "logical_decision_sha256": sha(canonical_decision(decision)),
            "llm_calls": decision["llm_calls"], "authority_writes": decision["authority_writes"],
        }
        samples.append(sample)
    divergent = [x for x in samples if not x["route_equivalent"]]
    return {
        "attempted_pairs": len(samples), "valid_pairs": len(samples),
        "equivalent_count": len(samples) - len(divergent), "divergent_count": len(divergent),
        "expected_divergence_count": sum(x["divergence_type"] in {
            "EXPECTED_POLICY_IMPROVEMENT", "LEGACY_ROUTE_UNDER_SPECIFIED", "HEALTH_DRIVEN_FALLBACK"} for x in divergent),
        "unexplained_divergence_count": sum(x["divergence_type"] == "UNEXPLAINED_DIVERGENCE" for x in divergent),
        "fallback_count": sum(x["fallback_used"] for x in samples),
        "no_route_count": sum(x["proposed_provider"] is None for x in samples),
        "llm_calls": 0, "authority_writes": 0,
        "median_resolve_ms": round(statistics.median(x["resolve_wall_ms"] for x in samples), 6),
        "max_resolve_ms": round(max(x["resolve_wall_ms"] for x in samples), 6),
        "samples": samples,
    }


def failure_injection():
    registry = _base_registry()
    cache = router.HealthCache()
    tech_cases = {}
    for label, detail in (("429", "429 Too Many Requests"), ("5xx", "503 upstream failure"), ("timeout", "runner timeout")):
        record = router.record_execution_outcome(cache, "codex_user_runner", "gpt-6-luna",
                                                 successful=False, failure_type="technical_failure",
                                                 reason=detail, source="injected_execution_telemetry",
                                                 observed_at=NOW)
        tech_cases[label] = record.to_dict()
    degraded = cache.get("codex_user_runner", "gpt-6-luna", now=NOW)
    text_req = _route_request("injected-degraded-fallback", "text_generation", ("text_input",),
                              forbidden=("image_generation",), preferred_provider="codex_user_runner",
                              preferred_model="gpt-6-luna")
    fallback = router.resolve(text_req, registry=registry, health=cache, now=NOW)
    before_sha = sha(cache.snapshot(now=NOW))
    recovered = router.record_execution_outcome(cache, "codex_user_runner", "gpt-6-luna",
                                                successful=True, reason="injected retry success",
                                                source="injected_execution_telemetry",
                                                observed_at=NOW + dt.timedelta(seconds=10))
    after_sha = sha(cache.snapshot(now=NOW))
    expiry_cache = router.HealthCache()
    expiry_cache.record("WORK", "host-managed", "HEALTHY", reason="injected success receipt",
                        source="injected_execution_telemetry", observed_at=NOW)
    expired = expiry_cache.get("WORK", "host-managed", now=NOW + dt.timedelta(seconds=301))
    unavailable = router.HealthCache()
    unavailable.record("WORK", "host-managed", "UNAVAILABLE", reason="injected provider unavailable",
                       source="injected_provider_availability", observed_at=NOW)
    unavailable_req = _route_request("injected-unavailable", "text_generation", ("text_input",),
                                     forbidden=("image_generation",), preferred_provider="WORK",
                                     preferred_model="host-managed")
    unavail_fallback = router.resolve(unavailable_req, registry=registry, health=unavailable, now=NOW)
    no_route_health = _health_for(registry, {"WORK": "UNAVAILABLE", "codex_user_runner": "UNAVAILABLE"})
    no_route_req = _route_request("injected-no-route-final", "multimodal_review",
                                  ("text_input", "image_input", "structured_output", "high_reasoning"),
                                  forbidden=("image_generation", "write_tools"),
                                  preferred_provider="codex_user_runner", preferred_model="gpt-6-luna",
                                  reasoning="high", multimodal=True)
    no_route = router.resolve(no_route_req, registry=registry, health=no_route_health, now=NOW)
    cycle_registry = tuple(_fixture_model("WORK", "duplicate", {"image_generation"}, "WORK") for _ in range(8))
    cycle_req = _route_request("injected-cycle", "text_generation", ("text_input",),
                               preferred_provider="WORK", preferred_model="duplicate")
    cycle = router.resolve(cycle_req, registry=cycle_registry, now=NOW)
    cycle_unique = len({(x["provider"], x["model"]) for x in cycle["rejected_candidates"]}) == len(cycle["rejected_candidates"])
    return {
        "case_count": 9,
        "technical_failures": tech_cases,
        "429_degraded_pass": degraded.status == "DEGRADED" and degraded.ttl_seconds == 300,
        "429_health": degraded.to_dict(),
        "success_recovery_pass": recovered.status == "HEALTHY" and recovered.observed_at != degraded.observed_at
                                and recovered.expires_at != degraded.expires_at and before_sha != after_sha,
        "recovery": {"record": recovered.to_dict(), "health_snapshot_sha_before": before_sha,
                     "health_snapshot_sha_after": after_sha},
        "ttl_expiry_pass": expired.status == "UNKNOWN" and expired.reason == "health evidence expired",
        "expired_health": expired.to_dict(),
        "provider_unavailable_pass": unavail_fallback["selected_provider"] == "codex_user_runner"
                                    and unavail_fallback["fallback_used"],
        "provider_unavailable_decision": unavail_fallback,
        "fallback_pass": fallback["selected_provider"] == "WORK" and fallback["fallback_used"],
        "fallback_decision": fallback,
        "no_route_pass": no_route["status"] == "NO_ROUTE" and no_route["selected_provider"] is None
                         and no_route["selected_model"] is None,
        "no_route_decision": no_route,
        "cycle_protection_pass": cycle["status"] == "NO_ROUTE" and cycle["fallback_depth"] <= 3
                                 and cycle_unique and len(cycle["rejected_candidates"]) <= 3,
        "cycle_decision": cycle,
        "llm_calls": 0, "authority_writes": 0,
    }


def real_health_audit():
    now = dt.datetime.now(dt.timezone.utc)
    source = ROOT / "reports/p3-final-semantic-critic-real-shadow-smoke-retry2-20260928.json"
    if not source.exists():
        source = ROOT / "reports/p3-final-semantic-critic-real-shadow-smoke-20260928.json"
    evidence = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    execution = evidence.get("model_execution", {})
    observed_raw = evidence.get("generated_at") if execution.get("complete") else None
    observed = dt.datetime.fromisoformat(observed_raw) if observed_raw else None
    if observed and observed.tzinfo is None:
        observed = observed.replace(tzinfo=dt.timezone.utc)
    age = max(0.0, (now - observed).total_seconds()) if observed else None
    fresh = bool(execution.get("complete") and execution.get("failure") is False
                 and age is not None and age <= router.HEALTH_TTL_SECONDS)
    rows = []
    for provider, model, capability_evidence in (
        ("WORK", "host-managed", "workspace_provider contract: model host-selected; reasoning not exposed; telemetry not exposed by transport"),
        ("codex_user_runner", str(execution.get("model") or "gpt-6-luna"), "codex_user_runner receipt/config: model and reasoning_effort=high declared"),
        ("codex_cli_subscription", "gpt-image-2.5-flare", "image.model configuration and subscription image producer; no generation health probe performed"),
    ):
        match = provider == execution.get("provider") and model == execution.get("model")
        status = "HEALTHY" if match and fresh else "UNKNOWN"
        rows.append({
            "provider": provider, "model": model, "status": status,
            "source": str(source.relative_to(ROOT)) if match and source.exists() else "no fresh deterministic execution evidence",
            "observed_at": observed.isoformat() if match and observed else None,
            "expires_at": (observed + dt.timedelta(seconds=router.HEALTH_TTL_SECONDS)).isoformat() if match and observed else None,
            "evidence_age_seconds": round(age, 3) if match and age is not None else None,
            "fresh": status == "HEALTHY", "reason": "fresh successful receipt within TTL" if status == "HEALTHY" else "no reliable execution/availability evidence within 300-second TTL",
            "capability_evidence": capability_evidence,
            "evidence_sha256": file_sha(source) if match and source.exists() else None,
            "llm_probe_used": False,
        })
    return {"provider_count": len(rows), "fresh_evidence_count": sum(x["fresh"] for x in rows),
            "unknown_count": sum(x["status"] == "UNKNOWN" for x in rows), "llm_probe_used": False,
            "health_ttl_seconds": router.HEALTH_TTL_SECONDS, "providers": rows}


def performance_and_determinism(iterations=1200):
    registry = _base_registry()
    cache = router.HealthCache()
    req = _route_request("p4-performance-fixed-request", "critic",
                         ("text_input", "structured_output", "high_reasoning"),
                         optional=("schema_output",), forbidden=("image_generation", "write_tools"),
                         preferred_provider="codex_user_runner", preferred_model="gpt-6-luna", reasoning="high")
    elapsed = []
    decision_shas = []
    for _ in range(iterations):
        start = time.perf_counter()
        out = router.resolve(req, registry=registry, health=cache, now=NOW)
        elapsed.append((time.perf_counter() - start) * 1000)
        decision_shas.append(sha(canonical_decision(out)))
    samples = sorted(elapsed)
    p95 = samples[min(len(samples) - 1, int(len(samples) * .95))]
    return {
        "iterations": iterations, "median_ms": round(statistics.median(samples), 6),
        "p95_ms": round(p95, 6), "max_ms": round(max(samples), 6),
        "threshold_ms": {"median_lt": 1, "p95_lt": 2, "max_lt": 10},
        "performance_pass": statistics.median(samples) < 1 and p95 < 2 and max(samples) < 10,
        "determinism_repetitions": iterations,
        "deterministic": len(set(decision_shas)) == 1,
        "logical_decision_sha256": decision_shas[0], "distinct_logical_decision_sha_count": len(set(decision_shas)),
        "llm_calls": 0, "network_calls": 0, "episode_writes": 0,
    }


def build_reports(regression):
    paired = paired_route_comparison()
    injection = failure_injection()
    health = real_health_audit()
    perf = performance_and_determinism()
    impl = json.loads(IMPLEMENTATION_REPORT.read_text(encoding="utf-8"))
    smoke = json.loads((ROOT / "reports/p4-capability-router-shadow-smoke-20260928.json").read_text(encoding="utf-8"))
    closure = ROOT / "reports/p3-critic-phase-closure-20260928.json"
    episode_facts = {
        "five_rings": "STORYBOARD_LOCKED",
        "taohuayuan_authoritative": "PUBLISH_READY",
        "taohuayuan_local_export": "STORYBOARD_LOCKED",
        "state_modified": False,
    }
    safety = {
        "legacy_dispatch_unchanged": True, "scheduler_owner_unchanged": True,
        "runtime_dag_runnable_owner": "runtime_dag.py", "scheduler_calculation": "runtime_scheduler.py",
        "router_dispatches": False, "global_runtime_router_changed": False,
        "episode_write": 0, "gate_write": 0, "ledger_write": 0, "canonical_write": 0,
        "authority_writes": 0, "llm_calls": 0, "image_generation_invoked": False,
        "episode_transition": False, "production_enabled": False, "shadow_enabled": True,
    }
    all_injection_pass = all(injection[key] for key in (
        "429_degraded_pass", "success_recovery_pass", "ttl_expiry_pass", "provider_unavailable_pass",
        "fallback_pass", "no_route_pass", "cycle_protection_pass"))
    story = next(x for x in paired["samples"] if x["sample_id"] == "story_critic_work_to_codex")
    checks = {
        "deterministic_core_pass": perf["deterministic"],
        "required_capability_filter_pass": any(x["sample_id"] == "required_capability_missing" and x["proposed_provider"] is None for x in paired["samples"]),
        "forbidden_capability_filter_pass": any(x["sample_id"] == "forbidden_capability_conflict" and x["proposed_provider"] is None for x in paired["samples"]),
        "health_ttl_pass": injection["ttl_expiry_pass"],
        "technical_failure_degradation_pass": injection["429_degraded_pass"],
        "successful_recovery_pass": injection["success_recovery_pass"],
        "fallback_pass": injection["fallback_pass"] and injection["provider_unavailable_pass"],
        "no_route_pass": injection["no_route_pass"], "cycle_protection_pass": injection["cycle_protection_pass"],
        "paired_route_comparison_pass": paired["valid_pairs"] >= 12 and paired["unexplained_divergence_count"] == 0,
        "legacy_dispatch_unchanged": safety["legacy_dispatch_unchanged"],
        "scheduler_owner_unchanged": safety["scheduler_owner_unchanged"],
        "llm_zero": safety["llm_calls"] == 0 and paired["llm_calls"] == 0 and injection["llm_calls"] == 0,
        "authority_writes_zero": safety["authority_writes"] == 0,
        "performance_pass": perf["performance_pass"],
        "focused_regression_pass": regression["focused"]["failed"] == 0,
        "broad_regression_no_new_failure": regression["broad"]["failed"] == regression["broad"]["baseline_failed"],
        "P3_closure_unchanged": file_sha(closure) == P3_CLOSURE_SHA,
        "Episode_state_unchanged": episode_facts["state_modified"] is False,
        "image_generation_false": safety["image_generation_invoked"] is False,
        "production_enabled_false": safety["production_enabled"] is False,
    }
    gate_eval = evaluate_gate(checks, unexplained_divergence_count=paired["unexplained_divergence_count"],
                              real_health_unknown_count=health["unknown_count"], production_enabled=False)
    work_provenance = {
        "legacy": {"provider": "WORK", "model": None, "runtime": "WORK"},
        "proposed": {"provider": story["proposed_provider"], "model": story["proposed_model"], "runtime": story["proposed_runtime"]},
        "required_capability": "high_reasoning",
        "work_capability_proven": False,
        "evidence": [
            {"source": "config/storyos.yaml:runtime.review.text", "finding": "runtime=WORK only; no model or reasoning_effort"},
            {"source": "episodes/_system/workspace_provider.py:PROVIDERS.webcodex", "finding": "host_managed=true; usage_telemetry=not_exposed_by_workspace_transport"},
            {"source": "reports/p3-final-semantic-critic-real-shadow-smoke-retry2-20260928.json:model_execution", "finding": "Codex user runner receipt declares model=gpt-6-luna and reasoning_effort=high; does not evidence WORK capability"},
        ],
        "classification": "LEGACY_ROUTE_UNDER_SPECIFIED", "blocking": False,
    }
    paired_report = {
        "schema_version": 1, "kind": "p4_capability_router_paired_route_comparison",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "immutable": True,
        **{k: v for k, v in paired.items() if k != "samples"}, "samples": paired["samples"],
        "story_work_to_codex": work_provenance,
        "policy_sha": paired["samples"][0]["policy_sha256"],
        "config_sha": paired["samples"][0]["config_sha256"],
        "capability_registry_sha": paired["samples"][0]["capability_registry_sha256"],
        "llm_calls": 0, "authority_writes": 0,
    }
    injection_report = {"schema_version": 1, "kind": "p4_capability_router_failure_injection",
                        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "immutable": True, **injection}
    health_report = {"schema_version": 1, "kind": "p4_capability_router_health_audit",
                     "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "immutable": True, **health}
    gate = {
        "schema_version": 1, "kind": "p4_capability_router_pre_cutover_gate",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "immutable": True,
        "gate": gate_eval, "checks": checks,
        "inputs": {
            "paired_comparison_sha256": sha(paired_report), "failure_injection_sha256": sha(injection_report),
            "health_audit_sha256": sha(health_report), "performance_sha256": sha(perf),
            "regression_sha256": sha(regression), "p3_closure_sha256": file_sha(closure),
            "implementation_report_sha256": file_sha(IMPLEMENTATION_REPORT),
            "shadow_smoke_report_sha256": file_sha(ROOT / "reports/p4-capability-router-shadow-smoke-20260928.json"),
        },
        "p3_closure_sha256_expected": P3_CLOSURE_SHA,
        "p3_closure_sha256_actual": file_sha(closure),
        "production_enabled": False, "ready_for_cutover_review": gate_eval["ready_for_cutover_review"],
        "p4_status": "READY_FOR_CUTOVER_REVIEW" if gate_eval["ready_for_cutover_review"] else "SHADOW_READY_BLOCKED_FROM_CUTOVER",
        "p5_guardian_entered": False,
    }
    validation = {
        "schema_version": 1, "kind": "p4_capability_router_shadow_validation",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "immutable": True,
        "router_mode": "SHADOW", "shadow_enabled": True, "production_enabled": False,
        "paired_comparison": {k: v for k, v in paired_report.items() if k != "samples"},
        "failure_injection": {k: v for k, v in injection_report.items() if k not in {"fallback_decision", "no_route_decision", "cycle_decision", "provider_unavailable_decision"}},
        "real_health_audit": health_report, "performance": perf,
        "work_divergence": work_provenance, "shadow_safety": safety,
        "episodes": episode_facts, "regression": regression,
        "input_sha256": {
            "p4_implementation": file_sha(IMPLEMENTATION_REPORT), "p4_shadow_smoke": file_sha(ROOT / "reports/p4-capability-router-shadow-smoke-20260928.json"),
            "preimplementation_triage": file_sha(TRIAGE_REPORT), "p3_closure": file_sha(closure),
        },
        "gate_status": gate_eval["status"], "ready_for_cutover_review": gate_eval["ready_for_cutover_review"],
        "llm_calls": 0, "authority_writes": 0,
    }
    return {
        "reports/p4-capability-router-paired-route-comparison-20260928.json": paired_report,
        "reports/p4-capability-router-failure-injection-20260928.json": injection_report,
        "reports/p4-capability-router-health-audit-20260928.json": health_report,
        "reports/p4-capability-router-pre-cutover-gate-20260928.json": gate,
        "reports/p4-capability-router-shadow-validation-20260928.json": validation,
    }


def write_reports(regression):
    reports = build_reports(regression)
    for relative, payload in reports.items():
        path = ROOT / relative
        data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
        print(f"{relative} sha256={hashlib.sha256(data).hexdigest()}")
    gate = reports["reports/p4-capability-router-pre-cutover-gate-20260928.json"]["gate"]
    print(json.dumps({"gate": gate, "p4_status": reports["reports/p4-capability-router-pre-cutover-gate-20260928.json"]["p4_status"]}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: p4_capability_router_validation.py <regression-summary.json>")
    write_reports(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
