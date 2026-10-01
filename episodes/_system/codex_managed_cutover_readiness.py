#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only pre-cutover gate for the StoryOS CODEX_MANAGED target mode.

This module never changes production.mode. It separates code/runtime readiness
from the irreversible product decision to make CODEX_MANAGED the configured
default. Phase5A must be supplied explicitly as PASS before readiness can be
declared.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import generation_attempt_authority
import p4_capability_router_implementation
import production_mode
import storyos_config



def evaluate(*, phase5a_status: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    config = cfg if isinstance(cfg, dict) else storyos_config.load_config()
    phase5a = str(phase5a_status or "").strip().upper()
    configured_mode = str(storyos_config.get_path(config, "production.mode", "")).strip().upper()
    execution_mode = str(storyos_config.get_path(config, "runtime.execution_mode", "")).strip().lower()

    p4 = p4_capability_router_implementation.audit_dispatch_consumer()
    p4_checks = p4.get("checks") if isinstance(p4.get("checks"), dict) else {}

    target_runtime = production_mode.runtime_for_mode("CODEX_MANAGED")

    checks = {
        "phase5a_pass": phase5a == "PASS",
        "current_mode_is_not_silently_cut_over": configured_mode in {"COLLABORATIVE", "CODEX_MANAGED"},
        "target_mode_maps_to_codex": target_runtime == "CODEX",
        "production_execution_mode_is_dag": execution_mode == "dag",
        "runtime_scheduler_is_dispatch_owner": p4.get("dispatch_owner") == "runtime_dag / runtime_scheduler",
        "p4_router_is_decision_only": p4.get("router_rights") == "decision_only",
        "p4_dispatch_consumer_verified": p4.get("decision") == "CONSUMER_VERIFIED",
        "p4_runtime_dag_uses_scheduler": p4_checks.get("runtime_dag_uses_runtime_scheduler") is True,
        "p4_scheduler_consumes_authorized_target": p4_checks.get("runtime_scheduler_consumes_effective_target") is True,
        "max_two_real_generation_attempts": (
            generation_attempt_authority.MAX_REAL_IMAGE_GENERATION_ATTEMPTS_PER_ASSET == 2
        ),
    }

    code_checks = {k: v for k, v in checks.items() if k != "phase5a_pass"}
    code_ready = all(code_checks.values())
    ready_for_cutover = code_ready and checks["phase5a_pass"]

    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": 1,
        "kind": "codex_managed_pre_cutover_readiness",
        "status": "READY_FOR_CUTOVER" if ready_for_cutover else "BLOCKED",
        "code_readiness": "PASS" if code_ready else "BLOCKED",
        "phase5a_status": phase5a,
        "configured_production_mode": configured_mode,
        "target_production_mode": "CODEX_MANAGED",
        "checks": checks,
        "blockers": blockers,
        "dispatch_owner": p4.get("dispatch_owner"),
        "router_rights": p4.get("router_rights"),
        "max_real_generation_attempts_per_asset":
            generation_attempt_authority.MAX_REAL_IMAGE_GENERATION_ATTEMPTS_PER_ASSET,
        "mutation_performed": False,
        "note": (
            "This is a read-only readiness gate. It does not change production.mode. "
            "Actual cutover remains forbidden until Phase5A is PASS."
        ),
    }


def self_test() -> None:
    cfg = storyos_config.load_config()
    row = evaluate(phase5a_status="BLOCKED", cfg=cfg)
    assert row["mutation_performed"] is False
    assert row["status"] == "BLOCKED"
    assert row["max_real_generation_attempts_per_asset"] == 2
    print("CODEX_MANAGED PRE-CUTOVER READINESS SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("evaluate")
    p.add_argument("--phase5a-status", required=True, choices=["PASS", "BLOCKED"])
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    print(json.dumps(evaluate(phase5a_status=args.phase5a_status), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
