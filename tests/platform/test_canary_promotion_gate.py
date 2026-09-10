from datetime import datetime, timezone

from platform.gateway.canary_observability_metrics import CanaryMetricsSnapshot
from platform.gateway.canary_promotion_evidence import build_promotion_evidence
from platform.gateway.canary_promotion_gate import CanaryPromotionGate
from platform.gateway.canary_soak_window import CanarySoakWindow


def metrics(total=100, failed=0, latency=100):
    return CanaryMetricsSnapshot(
        episode_id="10-02",
        runtime="V3_RUNTIME",
        total_requests=total,
        failed_count=failed,
        success_count=total - failed,
        avg_latency_ms=latency,
        error_rate=failed / total if total else 0,
    )


def test_soak_window_collects_stage_evidence():
    soak = CanarySoakWindow(10).snapshot(metrics())

    assert soak.stage_percent == 10
    assert soak.request_count == 100
    assert soak.trace_healthy is True


def test_promotion_gate_promotes_after_soak():
    soak = CanarySoakWindow(10).snapshot(metrics())

    decision = CanaryPromotionGate().evaluate(soak, next_percent=25)

    assert decision.action == "PROMOTE"
    assert decision.next_percent == 25


def test_promotion_gate_holds_for_small_sample():
    soak = CanarySoakWindow(10).snapshot(metrics(total=10))

    decision = CanaryPromotionGate().evaluate(soak, next_percent=25)

    assert decision.action == "HOLD"


def test_promotion_evidence_created():
    soak = CanarySoakWindow(10).snapshot(metrics())
    decision = CanaryPromotionGate().evaluate(soak, next_percent=25)

    evidence = build_promotion_evidence(
        soak,
        decision,
        generated_at=datetime.now(timezone.utc),
    )

    assert evidence.decision == "PROMOTE"
    assert evidence.stage_percent == 10
