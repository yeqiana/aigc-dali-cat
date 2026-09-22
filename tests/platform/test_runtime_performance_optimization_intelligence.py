from platform.operations.runtime_performance_optimization_intelligence import (
    RuntimePerformanceOptimizationIntelligence,
)


def test_performance_bottleneck_detection():
    engine = RuntimePerformanceOptimizationIntelligence()

    result = engine.analyze(
        runtime="v3-runtime",
        latency_ms=400,
        throughput=10,
        queue_delay_ms=2000,
    )

    assert result.bottleneck == "QUEUE"
    assert result.status == "DEGRADED"


def test_optimal_performance():
    engine = RuntimePerformanceOptimizationIntelligence()

    result = engine.analyze(
        runtime="v3-runtime",
        latency_ms=100,
        throughput=10,
        queue_delay_ms=10,
    )

    assert result.status == "OPTIMAL"
