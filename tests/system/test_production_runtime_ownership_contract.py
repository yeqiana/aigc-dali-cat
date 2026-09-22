"""A recorded ownership switch is not a production takeover (W-11).

The Phase9 switch wrote V3_RUNTIME into meta/runtime/runtime-primary.json on
2026-09-11 and that write is real. What it did not do is change production: the
kernel reads no ownership field, so it kept running the same engine. The gate
that reported completion was reading the record, and the record agrees with
itself, so nothing in the loop could notice.

These tests pin the two facts apart. They assert behaviour (a record alone must
not complete a migration) rather than the current value of the gap, so they keep
holding after a real takeover lands.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from platform.gateway.production_migration_completion import (
    ProductionMigrationCompletion,
    complete_from_repository,
)
from platform.gateway.production_ownership_consumer import (
    PRODUCTION_ROOTS,
    assess,
)

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_ownership

RECORD = ROOT / "meta" / "runtime" / "runtime-primary.json"


def _write_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


# --- the gate must not accept the record as its own witness -------------------

def test_v3_field_alone_does_not_complete_migration():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V3_RUNTIME",
    )

    assert result.status == "BLOCKED"
    assert result.message == "ownership_recorded_but_no_production_consumer"
    assert result.recorded_ownership is True
    assert result.effective_ownership is False


def test_readiness_separates_recorded_from_effective():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V3_RUNTIME",
    )

    # Both facts are on the result, so a report cannot print one and imply the other.
    assert result.recorded_ownership is True
    assert result.effective_ownership is False
    assert result.takeover_state == "RECORDED_ONLY"


def test_takeover_completes_once_a_production_consumer_exists():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V3_RUNTIME",
        production_consumers=("episodes/_system/runtime_router.py",),
    )

    assert result.status == "COMPLETED"
    assert result.takeover_state == "EFFECTIVE"


# --- gate verdict must track the scanned tree, not a caller's assertion -------

def test_repository_gate_agrees_with_scanned_consumers():
    recorded = json.loads(RECORD.read_text(encoding="utf-8"))["primary_runtime"]
    evidence = assess(ROOT, recorded)
    result = complete_from_repository(
        audit_verified=True, root=ROOT, recorded_runtime=recorded
    )

    assert result.effective_ownership == evidence.effective_ownership
    assert (result.status == "COMPLETED") == evidence.effective_ownership
    assert "episodes/_system/runtime_ownership.py" in evidence.production_consumers
    assert "episodes/_system/runtime_dag.py" in evidence.production_consumers
    assert "episodes/_system/episode_runner.py" in evidence.production_consumers
    assert "episodes/_system/runtime_driver.py" in evidence.production_consumers


def test_kernel_guard_fails_closed_when_record_selects_v2(tmp_path):
    record = tmp_path / "runtime-primary.json"
    record.write_text(json.dumps({
        "primary_runtime": "V2_RUNTIME",
        "previous_runtime": "V3_RUNTIME",
        "reason": "rollback",
        "updated_at": "2026-09-15T00:00:00+00:00",
    }), encoding="utf-8")

    with pytest.raises(runtime_ownership.RuntimeOwnershipError, match="primary_runtime=V2_RUNTIME"):
        runtime_ownership.assert_v3_owner("test", path=record)


def test_kernel_guard_accepts_v3_record(tmp_path):
    record = tmp_path / "runtime-primary.json"
    record.write_text(json.dumps({
        "primary_runtime": "V3_RUNTIME",
        "previous_runtime": "V2_RUNTIME",
        "reason": "production_migration_finalized",
        "updated_at": "2026-09-15T00:00:00+00:00",
    }), encoding="utf-8")

    resolved = runtime_ownership.assert_v3_owner("test", path=record)
    assert resolved.primary_runtime == "V3_RUNTIME"
    assert resolved.v3_effective is True


def test_production_kernel_is_the_scanned_root():
    # 架构收敛 3.1: episodes/_system is the Production Kernel. Scanning anywhere
    # else would ask the control plane whether the control plane took over.
    assert PRODUCTION_ROOTS == ("episodes",)


# --- self-consumption in the control plane is not a takeover ------------------

def test_gateway_self_consumption_is_not_a_takeover(tmp_path):
    root = _write_tree(tmp_path, {
        "platform/gateway/runtime_primary_registry.py": 'PRIMARY = "V3_RUNTIME"\n',
        "platform/gateway/production_migration_completion.py": 'PRIMARY = "V3_RUNTIME"\n',
    })

    evidence = assess(root, "V3_RUNTIME")

    assert evidence.control_plane_consumers  # the loop is visible...
    assert evidence.production_consumers == ()  # ...and still counts for nothing
    assert evidence.effective_ownership is False


def test_production_consumer_is_detected(tmp_path):
    root = _write_tree(tmp_path, {
        "episodes/_system/runtime_router.py": 'PRIMARY = "V3_RUNTIME"\n',
        "platform/gateway/runtime_primary_registry.py": 'PRIMARY = "V3_RUNTIME"\n',
    })

    evidence = assess(root, "V3_RUNTIME")

    assert evidence.production_consumers == ("episodes/_system/runtime_router.py",)
    assert evidence.effective_ownership is True


def test_tests_and_caches_are_not_execution_paths(tmp_path):
    root = _write_tree(tmp_path, {
        "episodes/_system/test_v2_multi_runtime.py": 'PRIMARY = "V2_RUNTIME"\n',
        "episodes/_system/conftest.py": 'PRIMARY = "V2_RUNTIME"\n',
        "episodes/_system/__pycache__/stale.py": 'PRIMARY = "V2_RUNTIME"\n',
        "episodes/_tests/probe.py": 'PRIMARY = "V2_RUNTIME"\n',
    })

    evidence = assess(root, "V3_RUNTIME")

    assert evidence.production_consumers == ()


def test_scan_reports_relative_posix_paths(tmp_path):
    root = _write_tree(tmp_path, {
        "episodes/_system/runtime_router.py": 'PRIMARY = "V3_RUNTIME"\n',
    })

    (consumer,) = assess(root, "V3_RUNTIME").production_consumers

    assert not Path(consumer).is_absolute()
    assert "\\" not in consumer
