from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platform.operations.runtime_health_monitoring import RuntimeHealthSnapshot


AlertLevel = Literal["INFO", "WARNING", "CRITICAL"]
IncidentStatus = Literal["OPEN", "RESOLVED"]


@dataclass(frozen=True)
class RuntimeAlert:
    level: AlertLevel
    reason: str
    health_score: float


@dataclass(frozen=True)
class RuntimeIncident:
    incident_id: str
    status: IncidentStatus
    alert_level: AlertLevel
    reason: str


class RuntimeAlertManager:
    """Convert runtime health signals into alerts and incidents."""

    def evaluate(self, snapshot: RuntimeHealthSnapshot) -> RuntimeAlert:
        if snapshot.status == "UNHEALTHY":
            return RuntimeAlert("CRITICAL", "runtime_unhealthy", snapshot.health_score)

        if snapshot.status == "DEGRADED":
            return RuntimeAlert("WARNING", "runtime_degraded", snapshot.health_score)

        return RuntimeAlert("INFO", "runtime_healthy", snapshot.health_score)

    def create_incident(self, alert: RuntimeAlert, incident_id: str) -> RuntimeIncident:
        status: IncidentStatus = "OPEN" if alert.level == "CRITICAL" else "RESOLVED"
        return RuntimeIncident(
            incident_id=incident_id,
            status=status,
            alert_level=alert.level,
            reason=alert.reason,
        )
