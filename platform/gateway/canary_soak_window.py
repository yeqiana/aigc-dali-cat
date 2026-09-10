from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from platform.gateway.canary_observability_metrics import CanaryMetricsSnapshot


@dataclass(frozen=True)
class CanarySoakSnapshot:
    episode_id: str
    stage_percent: int
    start_time: datetime
    request_count: int
    error_rate: float
    avg_latency_ms: float
    trace_healthy: bool


class CanarySoakWindow:
    """Tracks stability evidence for a canary stage.

    Soak is evidence collection only. It does not promote traffic.
    """

    def __init__(self, stage_percent: int):
        self.stage_percent = stage_percent
        self.start_time = datetime.now(timezone.utc)

    def snapshot(
        self,
        metrics: CanaryMetricsSnapshot,
        *,
        trace_healthy: bool = True,
    ) -> CanarySoakSnapshot:
        return CanarySoakSnapshot(
            episode_id=metrics.episode_id,
            stage_percent=self.stage_percent,
            start_time=self.start_time,
            request_count=metrics.total_requests,
            error_rate=metrics.error_rate,
            avg_latency_ms=metrics.avg_latency_ms,
            trace_healthy=trace_healthy,
        )
