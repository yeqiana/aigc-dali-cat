from platform.operations.post_migration_operations import PostMigrationOperations


def test_post_migration_operations_ready():
    result = PostMigrationOperations().evaluate(
        primary_runtime="V3_RUNTIME",
        runtime_health=True,
        agent_reliability=True,
        memory_health=True,
        trace_health=True,
    )

    assert result.status == "READY"
    assert result.reasons == ()


def test_post_migration_operations_degraded_when_trace_failed():
    result = PostMigrationOperations().evaluate(
        primary_runtime="V3_RUNTIME",
        runtime_health=True,
        agent_reliability=True,
        memory_health=True,
        trace_health=False,
    )

    assert result.status == "DEGRADED"
    assert "trace_unhealthy" in result.reasons
