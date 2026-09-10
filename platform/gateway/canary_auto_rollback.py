from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from platform.gateway.canary_observability_metrics import CanaryMetricsSnapshot
from platform.gateway.canary_runtime_gateway import CanaryRouteResult, CanaryRuntimeGateway


RollbackAction = Literal["KEEP_CANARY", "ROLLBACK_TO_V2"]


@dataclass(frozen=True)
class CanaryRollbackPolicy:
    max_error_rate: float = 0.05
    max_avg_latency_ms: float = 30_000
    min_sample_size: int = 5
    rollback_on_trace_failure: bool = True

    def validate(self) -> None:
        if not 0 <= self.max_error_rate <= 1:
            raise ValueError("max_error_rate must be between 0 and 1")
        if self.max_avg_latency_ms < 0:
            raise ValueError("max_avg_latency_ms must be non-negative")
        if self.min_sample_size < 1:
            raise ValueError("min_sample_size must be at least 1")


@dataclass(frozen=True)
class CanaryRollbackDecision:
    episode_id: str
    action: RollbackAction
    reasons: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def should_rollback(self) -> bool:
        return self.action == "ROLLBACK_TO_V2"


class CanaryAutoRollbackPolicy:
    """Evaluate canary health and decide whether to fall back to V2.

    This component is deliberately decision-only. It never mutates the runtime
    gateway, episode state, workflow state, or production artifacts.
    """

    def __init__(self, policy: CanaryRollbackPolicy | None = None) -> None:
        self.policy = policy or CanaryRollbackPolicy()
        self.policy.validate()

    def evaluate(
        self,
        snapshot: CanaryMetricsSnapshot,
        *,
        trace_healthy: bool = True,
    ) -> CanaryRollbackDecision:
        reasons: list[str] = []

        if snapshot.total_requests < self.policy.min_sample_size:
            return CanaryRollbackDecision(
                episode_id=snapshot.episode_id,
                action="KEEP_CANARY",
                reasons=("insufficient_sample_size",),
                metrics=self._metrics(snapshot, trace_healthy),
            )

        if snapshot.error_rate > self.policy.max_error_rate:
            reasons.append("error_rate_exceeded")

        if snapshot.avg_latency_ms > self.policy.max_avg_latency_ms:
            reasons.append("latency_exceeded")

        if self.policy.rollback_on_trace_failure and not trace_healthy:
            reasons.append("trace_unhealthy")

        action: RollbackAction = "ROLLBACK_TO_V2" if reasons else "KEEP_CANARY"
        return CanaryRollbackDecision(
            episode_id=snapshot.episode_id,
            action=action,
            reasons=tuple(reasons) if reasons else ("canary_healthy",),
            metrics=self._metrics(snapshot, trace_healthy),
        )

    @staticmethod
    def _metrics(snapshot: CanaryMetricsSnapshot, trace_healthy: bool) -> dict[str, Any]:
        return {
            "runtime": snapshot.runtime,
            "total_requests": snapshot.total_requests,
            "success_count": snapshot.success_count,
            "failed_count": snapshot.failed_count,
            "error_rate": snapshot.error_rate,
            "avg_latency_ms": snapshot.avg_latency_ms,
            "trace_healthy": trace_healthy,
        }


class CanaryRollbackController:
    """Apply an already-reviewed rollback decision to the canary gateway only.

    The controller intentionally limits the blast radius to gateway routing.
    It does not mutate episode state, workflow state, or production artifacts.
    """

    def apply(
        self,
        decision: CanaryRollbackDecision,
        gateway: CanaryRuntimeGateway,
    ) -> CanaryRouteResult | None:
        if not decision.should_rollback:
            return None

        gateway.configure(enabled=False, percent=0)
        return gateway.route(decision.episode_id)
