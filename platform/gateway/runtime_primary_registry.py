from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


RuntimePrimary = Literal["V2_RUNTIME", "V3_RUNTIME"]


@dataclass(frozen=True)
class RuntimePrimaryRecord:
    primary_runtime: RuntimePrimary
    previous_runtime: RuntimePrimary | None
    reason: str
    updated_at: str


class RuntimePrimaryRegistry:
    """Stores current production runtime ownership.

    This registry only represents runtime routing truth. It does not replace
    episode state, release manifest, or migration evidence.
    """

    def __init__(self, primary_runtime: RuntimePrimary = "V2_RUNTIME"):
        self._record = RuntimePrimaryRecord(
            primary_runtime=primary_runtime,
            previous_runtime=None,
            reason="initial_runtime",
            updated_at=self._now(),
        )

    def get(self) -> RuntimePrimaryRecord:
        return self._record

    def promote_to(
        self,
        runtime: RuntimePrimary,
        *,
        reason: str = "production_migration_finalized",
    ) -> RuntimePrimaryRecord:
        if runtime == self._record.primary_runtime:
            return self._record

        self._record = RuntimePrimaryRecord(
            primary_runtime=runtime,
            previous_runtime=self._record.primary_runtime,
            reason=reason,
            updated_at=self._now(),
        )
        return self._record

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
