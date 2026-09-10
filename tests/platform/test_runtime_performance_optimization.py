from platform.operations.runtime_performance_optimization import RuntimePerformanceOptimizer


def test_runtime_performance_optimal():
    result = RuntimePerformanceOptimizer().evaluate(
        agent_latency_ms=1000,
        workflow_latency_ms=5000,
        tool_latency_ms=1000,
        queue_wait_ms=100,
        throughput_per_minute=10,
    )

    assert result.status == "OPTIMAL"


def test_runtime_performance_detects_bottleneck():
    result = RuntimePerformanceOptimizer().evaluate(
        agent_latency_ms=1000,
        workflow_latency_ms=40000,
        tool_latency_ms=20000,
        queue_wait_ms=8000,
        throughput_per_minute=1,
    )

    assert result.status == "BOTTLENECK"
    assert "queue_wait_high" in result.reasons
