from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from platform.gateway.canary_promotion_gate import CanaryPromotionGateResult
from platform.gateway.canary_soak_window import CanarySoakSnapshot


@dataclass(frozen=True)
class CanaryPromotionEvidence:
    episode_id: str
    stage_percent: int
    decision: str
    reasons: tuple[str, ...]
    request_count: int
    error_rate: float
    avg_latency_ms: float
    generated_at: datetime


def build_promotion_evidence(
    soak: CanarySoakSnapshot,
    decision: CanaryPromotionGateResult,
    *,
    generated_at: datetime,
) -> CanaryPromotionEvidence:
    return CanaryPromotionEvidence(
        episode_id=soak.episode_id,
        stage_percent=soak.stage_percent,
        decision=decision.action,
        reasons=decision.reasons,
        request_count=soak.request_count,
        error_rate=soak.error_rate,
        avg_latency_ms=soak.avg_latency_ms,
        generated_at=generated_at,
    )
