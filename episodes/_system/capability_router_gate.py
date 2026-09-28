"""Independent, side-effect-free P4 pre-cutover Gate evaluation."""
from __future__ import annotations


MANDATORY_CHECKS = (
    "deterministic_core_pass",
    "required_capability_filter_pass",
    "forbidden_capability_filter_pass",
    "health_ttl_pass",
    "technical_failure_degradation_pass",
    "successful_recovery_pass",
    "fallback_pass",
    "no_route_pass",
    "cycle_protection_pass",
    "paired_route_comparison_pass",
    "legacy_dispatch_unchanged",
    "scheduler_owner_unchanged",
    "llm_zero",
    "authority_writes_zero",
    "performance_pass",
    "focused_regression_pass",
    "broad_regression_no_new_failure",
    "P3_closure_unchanged",
    "Episode_state_unchanged",
    "image_generation_false",
    "production_enabled_false",
)


def evaluate_gate(checks: dict, *, unexplained_divergence_count: int,
                  real_health_unknown_count: int, production_enabled: bool) -> dict:
    """Evaluate the Gate without changing runtime flags or writing authority."""
    missing = [name for name in MANDATORY_CHECKS if checks.get(name) is not True]
    blockers = list(missing)
    if int(unexplained_divergence_count) > 0:
        blockers.append("unexplained_divergence_count > 0")
    if production_enabled:
        blockers.append("production_enabled must remain false")
    warnings = (["REAL_PROVIDER_HEALTH_CURRENTLY_UNKNOWN"]
                if int(real_health_unknown_count) > 0 else [])
    if blockers:
        status, ready = "BLOCKED", False
    elif warnings:
        status, ready = "CONDITIONAL", True
    else:
        status, ready = "PASS", True
    return {
        "status": status,
        "ready_for_cutover_review": ready,
        "mandatory_checks": {name: checks.get(name) is True for name in MANDATORY_CHECKS},
        "mandatory_checks_pass": not missing,
        "unexplained_divergence_count": int(unexplained_divergence_count),
        "warnings": warnings,
        "blockers": blockers,
        "production_enabled": bool(production_enabled),
    }
