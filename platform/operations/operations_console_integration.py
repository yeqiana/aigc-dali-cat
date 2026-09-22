from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ConsoleStatus = Literal["AVAILABLE", "DEGRADED", "UNAVAILABLE"]


@dataclass(frozen=True)
class OperationsConsoleView:
    runtime: str
    status: ConsoleStatus
    dashboard_endpoint: str
    capabilities: tuple[str, ...]
    readonly: bool


class OperationsConsoleIntegration:
    """Adapter between operations observability and Web Console.

    This layer only exposes operational data. It does not execute runtime
    changes, recovery actions, or configuration mutations.
    """

    def build_view(
        self,
        *,
        runtime: str,
        dashboard_endpoint: str = "/api/operations/dashboard",
        available: bool = True,
    ) -> OperationsConsoleView:
        status: ConsoleStatus = "AVAILABLE" if available else "UNAVAILABLE"

        return OperationsConsoleView(
            runtime=runtime,
            status=status,
            dashboard_endpoint=dashboard_endpoint,
            capabilities=(
                "health_view",
                "incident_view",
                "cost_view",
                "performance_view",
                "learning_view",
                "evolution_proposal_view",
            ),
            readonly=True,
        )
