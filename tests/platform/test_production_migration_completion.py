from platform.gateway.production_migration_completion import ProductionMigrationCompletion


def test_production_migration_completed():
    # Changed 2026-09-15 (W-11): a V3 record used to be sufficient here, which is
    # exactly how "migration completed" was reported over an unconsumed field.
    # A takeover now needs a production-side consumer as well.
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V3_RUNTIME",
        production_consumers=("episodes/_system/runtime_router.py",),
    )

    assert result.status == "COMPLETED"
    assert result.primary_runtime == "V3_RUNTIME"
    assert result.takeover_state == "EFFECTIVE"


def test_production_migration_blocked_without_production_consumer():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V3_RUNTIME",
    )

    assert result.status == "BLOCKED"
    assert result.message == "ownership_recorded_but_no_production_consumer"
    assert result.recorded_ownership is True
    assert result.effective_ownership is False
    assert result.takeover_state == "RECORDED_ONLY"


def test_production_migration_blocked_when_audit_failed():
    result = ProductionMigrationCompletion().complete(
        audit_verified=False,
        primary_runtime="V3_RUNTIME",
        production_consumers=("episodes/_system/runtime_router.py",),
    )

    assert result.status == "BLOCKED"


def test_production_migration_blocked_when_v3_not_primary():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V2_RUNTIME",
        production_consumers=("episodes/_system/runtime_router.py",),
    )

    assert result.status == "BLOCKED"
