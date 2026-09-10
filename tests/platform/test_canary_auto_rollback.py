from platform.gateway.canary_auto_rollback import (
    CanaryAutoRollbackPolicy,
    CanaryRollbackController,
    CanaryRollbackPolicy,
)
from platform.gateway.canary_observability_metrics import CanaryMetricsSnapshot
from platform.gateway.canary_runtime_gateway import CanaryRuntimeGateway


def test_keep_canary_when_sample_is_too_small():
    evaluator = CanaryAutoRollbackPolicy(CanaryRollbackPolicy(min_sample_size=5))
    snapshot = CanaryMetricsSnapshot(
        episode_id="10-02",
        runtime="V3_RUNTIME",
        total_requests=2,
        success_count=1,
        failed_count=1,
        avg_latency_ms=100,
        error_rate=0.5,
    )

    decision = evaluator.evaluate(snapshot)

    assert decision.action == "KEEP_CANARY"
    assert decision.reasons == ("insufficient_sample_size",)


def test_rollback_when_error_rate_exceeds_threshold():
    evaluator = CanaryAutoRollbackPolicy(
        CanaryRollbackPolicy(max_error_rate=0.05, min_sample_size=5)
    )
    snapshot = CanaryMetricsSnapshot(
        episode_id="10-02",
        runtime="V3_RUNTIME",
        total_requests=20,
        success_count=18,
        failed_count=2,
        avg_latency_ms=100,
        error_rate=0.1,
    )

    decision = evaluator.evaluate(snapshot)

    assert decision.should_rollback is True
    assert "error_rate_exceeded" in decision.reasons


def test_rollback_when_latency_or_trace_is_unhealthy():
    evaluator = CanaryAutoRollbackPolicy(
        CanaryRollbackPolicy(max_avg_latency_ms=1000, min_sample_size=1)
    )
    snapshot = CanaryMetricsSnapshot(
        episode_id="10-02",
        runtime="V3_RUNTIME",
        total_requests=5,
        success_count=5,
        failed_count=0,
        avg_latency_ms=1500,
        error_rate=0,
    )

    decision = evaluator.evaluate(snapshot, trace_healthy=False)

    assert decision.should_rollback is True
    assert "latency_exceeded" in decision.reasons
    assert "trace_unhealthy" in decision.reasons


def test_controller_routes_back_to_v2_only_on_rollback():
    evaluator = CanaryAutoRollbackPolicy(
        CanaryRollbackPolicy(max_error_rate=0.05, min_sample_size=1)
    )
    gateway = CanaryRuntimeGateway(canary_enabled=True, canary_percent=10)
    snapshot = CanaryMetricsSnapshot(
        episode_id="10-02",
        runtime="V3_RUNTIME",
        total_requests=10,
        success_count=8,
        failed_count=2,
        avg_latency_ms=100,
        error_rate=0.2,
    )

    decision = evaluator.evaluate(snapshot)
    route = CanaryRollbackController().apply(decision, gateway)

    assert route is not None
    assert route.target == "V2_RUNTIME"
    assert gateway.canary_enabled is False
    assert gateway.canary_percent == 0
