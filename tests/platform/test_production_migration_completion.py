from platform.gateway.production_migration_completion import ProductionMigrationCompletion


def test_production_migration_completed():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V3_RUNTIME",
    )

    assert result.status == "COMPLETED"
    assert result.primary_runtime == "V3_RUNTIME"


def test_production_migration_blocked_when_audit_failed():
    result = ProductionMigrationCompletion().complete(
        audit_verified=False,
        primary_runtime="V3_RUNTIME",
    )

    assert result.status == "BLOCKED"


def test_production_migration_blocked_when_v3_not_primary():
    result = ProductionMigrationCompletion().complete(
        audit_verified=True,
        primary_runtime="V2_RUNTIME",
    )

    assert result.status == "BLOCKED"
