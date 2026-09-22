from platform.operations.runtime_health_monitoring import RuntimeHealthMonitor


def test_runtime_health_is_healthy():
    result = RuntimeHealthMonitor().evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=1.0,
        workflow_success_rate=1.0,
        trace_health=True,
        memory_health=True,
    )

    assert result.status == "HEALTHY"
    assert result.health_score == 100


def test_runtime_health_is_degraded_when_trace_failed():
    result = RuntimeHealthMonitor().evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=1.0,
        workflow_success_rate=1.0,
        trace_health=False,
        memory_health=True,
    )

    assert result.status == "DEGRADED"
    assert "trace_unhealthy" in result.reasons
