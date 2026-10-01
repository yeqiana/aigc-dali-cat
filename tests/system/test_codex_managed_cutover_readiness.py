from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_managed_cutover_readiness as gate


def _cfg(mode: str = "COLLABORATIVE", execution_mode: str = "dag") -> dict:
    return {
        "production": {"mode": mode},
        "runtime": {"execution_mode": execution_mode},
    }


def _p4_ok() -> dict:
    return {
        "checks": {
            "runtime_dag_uses_runtime_scheduler": True,
            "runtime_scheduler_consumes_effective_target": True,
        },
        "dispatch_owner": "runtime_dag / runtime_scheduler",
        "router_rights": "decision_only",
        "decision": "CONSUMER_VERIFIED",
    }


def test_code_can_be_ready_while_phase5a_still_blocks_actual_cutover():
    with mock.patch.object(gate.p4_capability_router_implementation, "audit_dispatch_consumer", return_value=_p4_ok()):
        row = gate.evaluate(phase5a_status="BLOCKED", cfg=_cfg())
    assert row["code_readiness"] == "PASS"
    assert row["status"] == "BLOCKED"
    assert row["blockers"] == ["phase5a_pass"]
    assert row["mutation_performed"] is False
    assert row["configured_production_mode"] == "COLLABORATIVE"


def test_phase5a_pass_makes_readiness_ready_without_mutating_mode():
    with mock.patch.object(gate.p4_capability_router_implementation, "audit_dispatch_consumer", return_value=_p4_ok()):
        row = gate.evaluate(phase5a_status="PASS", cfg=_cfg())
    assert row["status"] == "READY_FOR_CUTOVER"
    assert row["configured_production_mode"] == "COLLABORATIVE"
    assert row["target_production_mode"] == "CODEX_MANAGED"
    assert row["mutation_performed"] is False


def test_non_dag_execution_blocks_readiness():
    with mock.patch.object(gate.p4_capability_router_implementation, "audit_dispatch_consumer", return_value=_p4_ok()):
        row = gate.evaluate(phase5a_status="PASS", cfg=_cfg(execution_mode="legacy"))
    assert row["status"] == "BLOCKED"
    assert row["checks"]["production_execution_mode_is_dag"] is False


def test_p4_must_remain_provider_runner_decision_only():
    p4 = _p4_ok()
    p4["router_rights"] = "model_and_provider"
    with mock.patch.object(gate.p4_capability_router_implementation, "audit_dispatch_consumer", return_value=p4):
        row = gate.evaluate(phase5a_status="PASS", cfg=_cfg())
    assert row["status"] == "BLOCKED"
    assert row["checks"]["p4_router_is_decision_only"] is False


def test_generation_hard_cap_is_part_of_gate():
    with mock.patch.object(gate.p4_capability_router_implementation, "audit_dispatch_consumer", return_value=_p4_ok()), \
         mock.patch.object(gate.generation_attempt_authority, "MAX_REAL_IMAGE_GENERATION_ATTEMPTS_PER_ASSET", 3):
        row = gate.evaluate(phase5a_status="PASS", cfg=_cfg())
    assert row["status"] == "BLOCKED"
    assert row["checks"]["max_two_real_generation_attempts"] is False
