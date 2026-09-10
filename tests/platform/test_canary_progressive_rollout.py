from platform.gateway.canary_auto_rollback import CanaryRollbackPolicy
from platform.gateway.canary_observability_metrics import CanaryMetricsSnapshot
from platform.gateway.canary_progressive_rollout import (
    CanaryProgressiveRollout,
    CanaryProgressiveRolloutController,
    CanaryRolloutPlan,
)
from platform.gateway.canary_runtime_gateway import CanaryRuntimeGateway


def snapshot(*, total: int = 20, failed: int = 0, latency: float = 100) -> CanaryMetricsSnapshot:
    return CanaryMetricsSnapshot(
        episode_id="10-02",
        runtime="V3_RUNTIME",
        total_requests=total,
        success_count=total - failed,
        failed_count=failed,
        avg_latency_ms=latency,
        error_rate=(failed / total) if total else 0,
    )


def test_rollout_starts_at_first_stage():
    rollout = CanaryProgressiveRollout()

    decision = rollout.evaluate(snapshot(total=0), current_percent=0)

    assert decision.action == "PROMOTE"
    assert decision.next_percent == 1


def test_rollout_holds_until_stage_has_enough_samples():
    rollout = CanaryProgressiveRollout(
        CanaryRolloutPlan(min_requests_per_stage=20),
        CanaryRollbackPolicy(min_sample_size=5),
    )

    decision = rollout.evaluate(snapshot(total=10), current_percent=1)

    assert decision.action == "HOLD"
    assert decision.next_percent == 1
    assert decision.reasons == ("insufficient_stage_sample_size",)


def test_rollout_promotes_healthy_stage():
    rollout = CanaryProgressiveRollout(
        CanaryRolloutPlan(min_requests_per_stage=20),
        CanaryRollbackPolicy(max_error_rate=0.05, min_sample_size=5),
    )

    decision = rollout.evaluate(snapshot(total=20), current_percent=1)

    assert decision.action == "PROMOTE"
    assert decision.next_percent == 5


def test_rollout_rolls_back_on_unhealthy_metrics():
    rollout = CanaryProgressiveRollout(
        CanaryRolloutPlan(min_requests_per_stage=20),
        CanaryRollbackPolicy(max_error_rate=0.05, min_sample_size=5),
    )

    decision = rollout.evaluate(snapshot(total=20, failed=2), current_percent=10)

    assert decision.action == "ROLLBACK"
    assert decision.next_percent == 0
    assert "error_rate_exceeded" in decision.reasons


def test_rollout_rolls_back_on_trace_failure():
    rollout = CanaryProgressiveRollout(
        CanaryRolloutPlan(min_requests_per_stage=20),
        CanaryRollbackPolicy(min_sample_size=5),
    )

    decision = rollout.evaluate(
        snapshot(total=20),
        current_percent=25,
        trace_healthy=False,
    )

    assert decision.action == "ROLLBACK"
    assert "trace_unhealthy" in decision.reasons


def test_rollout_marks_100_percent_complete():
    rollout = CanaryProgressiveRollout(
        CanaryRolloutPlan(min_requests_per_stage=20),
        CanaryRollbackPolicy(min_sample_size=5),
    )

    decision = rollout.evaluate(snapshot(total=20), current_percent=100)

    assert decision.action == "COMPLETE"
    assert decision.next_percent == 100


def test_controller_applies_promote_and_rollback_to_gateway():
    rollout = CanaryProgressiveRollout(
        CanaryRolloutPlan(min_requests_per_stage=20),
        CanaryRollbackPolicy(max_error_rate=0.05, min_sample_size=5),
    )
    controller = CanaryProgressiveRolloutController()
    gateway = CanaryRuntimeGateway()

    promote = rollout.evaluate(snapshot(total=0), current_percent=0)
    promoted = controller.apply(promote, gateway)
    assert promoted.enabled is True
    assert promoted.percent == 1

    rollback = rollout.evaluate(snapshot(total=20, failed=2), current_percent=1)
    rolled_back = controller.apply(rollback, gateway)
    assert rolled_back.enabled is False
    assert rolled_back.percent == 0


def test_gateway_percentage_routing_uses_stable_buckets():
    gateway = CanaryRuntimeGateway(canary_enabled=True, canary_percent=10)

    first = gateway.route("10-02", request_key="request-42")
    second = gateway.route("10-02", request_key="request-42")
    assert first == second

    targets = {
        gateway.route("10-02", request_key=f"request-{index}").target
        for index in range(200)
    }
    assert targets == {"V2_RUNTIME", "V3_RUNTIME"}

    gateway.configure(enabled=True, percent=100)
    assert gateway.route("10-02", request_key="any").target == "V3_RUNTIME"

    gateway.configure(enabled=False, percent=0)
    assert gateway.route("10-02", request_key="any").target == "V2_RUNTIME"
