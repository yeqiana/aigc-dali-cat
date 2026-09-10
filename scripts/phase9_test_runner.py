"""
Phase 9 Runtime Operations temporary pytest adapter.

Purpose:
- Avoid project top-level `platform/` shadowing Python stdlib `platform`.
- Bootstrap pytest from repository root.
- Keep Runtime Operations validation isolated without changing package layout.

This is a temporary validation adapter for P9.24.1.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def isolate_project_platform() -> str:
    """Remove repository root before importing pytest to protect stdlib platform."""
    project_str = str(PROJECT_ROOT)

    while project_str in sys.path:
        sys.path.remove(project_str)

    return project_str


def restore_project_root(project_str: str) -> None:
    """Restore repository root after pytest itself has loaded."""
    if project_str not in sys.path:
        sys.path.insert(0, project_str)


def run() -> int:
    os.chdir(PROJECT_ROOT)

    project_str = isolate_project_platform()

    import pytest

    restore_project_root(project_str)

    test_args = [
        "-p",
        "scripts.phase9_pytest_plugin",

        # Runtime Core
        "tests/platform/test_runtime_health_monitoring.py",
        "tests/platform/test_runtime_alert_incident_management.py",
        "tests/platform/test_runtime_recovery_self_healing.py",
        "tests/platform/test_runtime_reliability_engineering.py",

        # Runtime Governance
        "tests/platform/test_runtime_cost_governance.py",
        "tests/platform/test_runtime_cost_optimization_governance.py",
        "tests/platform/test_runtime_error_budget_management.py",
        "tests/platform/test_runtime_capacity_planning_scaling_governance.py",
        "tests/platform/test_runtime_performance_optimization.py",
        "tests/platform/test_runtime_policy_enforcement_layer.py",

        # Runtime Intelligence
        "tests/platform/test_runtime_operations_control_plane.py",
        "tests/platform/test_runtime_operations_observability_api.py",
        "tests/platform/test_runtime_operations_automation_engine.py",
        "tests/platform/test_runtime_operations_slo_sla_management.py",
        "tests/platform/test_runtime_intelligence_decision_engine.py",
    ]

    return pytest.main(test_args)


if __name__ == "__main__":
    raise SystemExit(run())
