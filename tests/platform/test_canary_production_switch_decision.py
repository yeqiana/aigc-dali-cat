from datetime import datetime, timezone

from platform.gateway.canary_production_switch_decision import (
    CanaryProductionSwitchDecision,
    ProductionSwitchPolicy,
)
from platform.gateway.canary_promotion_evidence import CanaryPromotionEvidence


def evidence(stage=100, requests=200, error=0):
    return CanaryPromotionEvidence(
        episode_id="10-02",
        stage_percent=stage,
        decision="PROMOTE",
        reasons=("healthy",),
        request_count=requests,
        error_rate=error,
        avg_latency_ms=100,
        generated_at=datetime.now(timezone.utc),
    )


def test_switch_to_v3_when_canary_ready():
    decision = CanaryProductionSwitchDecision(
        ProductionSwitchPolicy(min_requests=100)
    ).evaluate(evidence())

    assert decision.action == "SWITCH_TO_V3"
    assert decision.target_runtime == "V3_RUNTIME"


def test_block_when_evidence_missing():
    decision = CanaryProductionSwitchDecision(
        ProductionSwitchPolicy(min_requests=100)
    ).evaluate(evidence(requests=10))

    assert decision.action == "BLOCK"


def test_keep_canary_before_full_rollout():
    decision = CanaryProductionSwitchDecision().evaluate(evidence(stage=50))

    assert decision.action == "KEEP_CANARY"
