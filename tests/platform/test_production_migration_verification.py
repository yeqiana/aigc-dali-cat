from platform.gateway.production_migration_verification import ProductionMigrationVerifier


def test_production_migration_verification_passes_for_v3_primary():
    result = ProductionMigrationVerifier().verify(
        episode_id="10-02",
        primary_runtime="V3_RUNTIME",
        gateway_runtime="V3_RUNTIME",
        trace_healthy=True,
        memory_available=True,
        workflow_available=True,
    )

    assert result.status == "VERIFIED"
    assert result.failed_checks == ()


def test_production_migration_verification_fails_when_gateway_not_v3():
    result = ProductionMigrationVerifier().verify(
        episode_id="10-02",
        primary_runtime="V3_RUNTIME",
        gateway_runtime="V2_RUNTIME",
        trace_healthy=True,
        memory_available=True,
        workflow_available=True,
    )

    assert result.status == "FAILED"
    assert "gateway_not_v3" in result.failed_checks
