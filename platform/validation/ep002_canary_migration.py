from dataclasses import dataclass
from typing import Any


@dataclass
class CanaryMigrationResult:
    episode_id: str
    mode: str
    canary_enabled: bool
    traffic_percent: int
    decision: str
    details: dict[str, Any]


class EP002CanaryMigration:
    """EP002 V3 Canary Migration controller.

    Canary only. Does not replace V2.7 production runtime.
    """

    def enable(self, episode_id: str, traffic_percent: int = 0) -> CanaryMigrationResult:
        return CanaryMigrationResult(
            episode_id=episode_id,
            mode="CANARY",
            canary_enabled=True,
            traffic_percent=traffic_percent,
            decision="CANARY_READY",
            details={
                "v2_runtime": "ACTIVE",
                "v3_runtime": "CANARY",
                "switch_mode": "dual_run",
            },
        )
