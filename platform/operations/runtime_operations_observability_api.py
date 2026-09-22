from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeOperationsView:
    """Read-only operations view exposed to dashboard/API layers.

    This layer aggregates operations evidence only. It does not mutate runtime
    state or trigger production actions.
    """

    runtime: str
    status: str
    health: str
    incidents: int
    reliability: str
    cost: str
    performance: str
    learning: str


class RuntimeOperationsObservabilityAPI:
    """Adapter between Operations Control Plane and console/API consumers."""

    def build_view(self, snapshot: Any) -> RuntimeOperationsView:
        return RuntimeOperationsView(
            runtime=snapshot.runtime,
            status=snapshot.operations_status,
            health=snapshot.health_status,
            incidents=snapshot.incident_count,
            reliability=snapshot.reliability_status,
            cost=snapshot.cost_status,
            performance=snapshot.performance_status,
            learning=snapshot.learning_status,
        )
