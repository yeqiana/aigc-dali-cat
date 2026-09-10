from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanaryMetricsSnapshot:
    episode_id: str
    runtime: str
    total_requests: int = 0
    success_count: int = 0
    failed_count: int = 0
    avg_latency_ms: float = 0
    error_rate: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class CanaryObservabilityMetrics:
    """Canary runtime observability collector.

    Only collects migration evidence. It does not control traffic.
    """

    def collect(self, episode_id: str, runtime: str, metrics: dict[str, Any]) -> CanaryMetricsSnapshot:
        total = metrics.get("total_requests", 0)
        failed = metrics.get("failed_count", 0)
        return CanaryMetricsSnapshot(
            episode_id=episode_id,
            runtime=runtime,
            total_requests=total,
            success_count=metrics.get("success_count", 0),
            failed_count=failed,
            avg_latency_ms=metrics.get("avg_latency_ms", 0),
            error_rate=(failed / total) if total else 0,
            metadata=metrics,
        )
