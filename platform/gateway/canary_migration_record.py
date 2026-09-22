from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CanaryMigrationRecord:
    episode_id: str
    from_runtime: str
    to_runtime: str
    decision: str
    created_at: str

    @classmethod
    def create(cls, episode_id: str, decision: str, to_runtime: str) -> "CanaryMigrationRecord":
        return cls(
            episode_id=episode_id,
            from_runtime="V2_RUNTIME",
            to_runtime=to_runtime,
            decision=decision,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
