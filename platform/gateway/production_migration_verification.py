from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


VerificationStatus = Literal["VERIFIED", "FAILED"]


@dataclass(frozen=True)
class ProductionMigrationVerificationResult:
    episode_id: str
    status: VerificationStatus
    checks: tuple[str, ...]
    failed_checks: tuple[str, ...]


class ProductionMigrationVerifier:
    """Final verification layer after V3 becomes primary runtime.

    This verifies migration consistency only. It does not change runtime state.
    """

    def verify(
        self,
        *,
        episode_id: str,
        primary_runtime: str,
        gateway_runtime: str,
        trace_healthy: bool,
        memory_available: bool,
        workflow_available: bool,
    ) -> ProductionMigrationVerificationResult:
        checks: list[str] = []
        failed: list[str] = []

        if primary_runtime == "V3_RUNTIME":
            checks.append("primary_runtime_v3")
        else:
            failed.append("primary_runtime_not_v3")

        if gateway_runtime == "V3_RUNTIME":
            checks.append("gateway_routes_v3")
        else:
            failed.append("gateway_not_v3")

        if trace_healthy:
            checks.append("trace_healthy")
        else:
            failed.append("trace_unhealthy")

        if memory_available:
            checks.append("memory_available")
        else:
            failed.append("memory_unavailable")

        if workflow_available:
            checks.append("workflow_available")
        else:
            failed.append("workflow_unavailable")

        return ProductionMigrationVerificationResult(
            episode_id=episode_id,
            status="VERIFIED" if not failed else "FAILED",
            checks=tuple(checks),
            failed_checks=tuple(failed),
        )
