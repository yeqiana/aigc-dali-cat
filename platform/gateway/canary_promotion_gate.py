from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platform.gateway.canary_soak_window import CanarySoakSnapshot


PromotionAction = Literal["PROMOTE", "HOLD", "ROLLBACK"]


@dataclass(frozen=True)
class CanaryPromotionGateResult:
    action: PromotionAction
    reasons: tuple[str, ...]
    next_percent: int


class CanaryPromotionGate:
    """Decides whether a completed soak stage can move forward."""

    def __init__(
        self,
        *,
        min_requests: int = 100,
        max_error_rate: float = 0.05,
        max_latency_ms: float = 30000,
    ):
        self.min_requests = min_requests
        self.max_error_rate = max_error_rate
        self.max_latency_ms = max_latency_ms

    def evaluate(self, soak: CanarySoakSnapshot, next_percent: int) -> CanaryPromotionGateResult:
        if not soak.trace_healthy:
            return CanaryPromotionGateResult(
                action="ROLLBACK",
                reasons=("trace_unhealthy",),
                next_percent=0,
            )

        if soak.request_count < self.min_requests:
            return CanaryPromotionGateResult(
                action="HOLD",
                reasons=("soak_sample_insufficient",),
                next_percent=soak.stage_percent,
            )

        if soak.error_rate > self.max_error_rate:
            return CanaryPromotionGateResult(
                action="ROLLBACK",
                reasons=("error_rate_exceeded",),
                next_percent=0,
            )

        if soak.avg_latency_ms > self.max_latency_ms:
            return CanaryPromotionGateResult(
                action="ROLLBACK",
                reasons=("latency_exceeded",),
                next_percent=0,
            )

        return CanaryPromotionGateResult(
            action="PROMOTE",
            reasons=("soak_passed",),
            next_percent=next_percent,
        )
