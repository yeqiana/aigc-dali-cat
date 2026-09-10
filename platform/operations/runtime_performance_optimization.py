from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PerformanceStatus = Literal["OPTIMAL", "DEGRADED", "BOTTLENECK"]


@dataclass(frozen=True)
class RuntimePerformanceSnapshot:
    agent_latency_ms: float
    workflow_latency_ms: float
    tool_latency_ms: float
    queue_wait_ms: float
    throughput_per_minute: float
    status: PerformanceStatus
    reasons: tuple[str, ...]


class RuntimePerformanceOptimizer:
    """Evaluates V3 runtime performance signals.

    This module observes and analyzes performance only. It does not mutate
    runtime configuration or execute optimization actions.
    """

    def evaluate(
        self,
        *,
        agent_latency_ms: float,
        workflow_latency_ms: float,
        tool_latency_ms: float,
        queue_wait_ms: float,
        throughput_per_minute: float,
    ) -> RuntimePerformanceSnapshot:
        reasons: list[str] = []

        if queue_wait_ms > 5000:
            reasons.append("queue_wait_high")
        if tool_latency_ms > 10000:
            reasons.append("tool_latency_high")
        if workflow_latency_ms > 30000:
            reasons.append("workflow_latency_high")

        if len(reasons) >= 2:
            status: PerformanceStatus = "BOTTLENECK"
        elif reasons:
            status = "DEGRADED"
        else:
            status = "OPTIMAL"

        return RuntimePerformanceSnapshot(
            agent_latency_ms=agent_latency_ms,
            workflow_latency_ms=workflow_latency_ms,
            tool_latency_ms=tool_latency_ms,
            queue_wait_ms=queue_wait_ms,
            throughput_per_minute=throughput_per_minute,
            status=status,
            reasons=tuple(reasons),
        )
