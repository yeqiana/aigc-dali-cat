from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from platform.repository.jsonl_latest_record_store import (
    JsonlLatestRecordStore,
    LatestRecordStore,
)


@dataclass(frozen=True)
class PlatformRecordStores:
    """Persistence bundle for non-authoritative Platform records.

    Execution and Experience records are control-plane observability/learning data.
    They never replace Episode state, gates, ledgers, or other Production Kernel
    authority. MySQL adapters may implement ``LatestRecordStore`` later without
    changing application composition.
    """

    execution: LatestRecordStore | None = None
    experience: LatestRecordStore | None = None

    @property
    def durable(self) -> bool:
        return self.execution is not None or self.experience is not None


def build_platform_record_stores(
    state_root: str | Path | None = None,
    *,
    execution_store: LatestRecordStore | None = None,
    experience_store: LatestRecordStore | None = None,
) -> PlatformRecordStores:
    """Build record stores without inventing a database migration.

    With no explicit stores and no ``state_root`` the historical in-process
    behavior is preserved. Supplying a root opts into append-only JSONL storage.
    Explicit stores win and keep the boundary ready for future MySQL adapters.
    """

    root = Path(state_root).resolve() if state_root is not None else None
    if execution_store is None and root is not None:
        execution_store = JsonlLatestRecordStore(
            root / "executions.jsonl", key_field="execution_id"
        )
    if experience_store is None and root is not None:
        experience_store = JsonlLatestRecordStore(
            root / "experiences.jsonl", key_field="experience_id"
        )
    return PlatformRecordStores(
        execution=execution_store,
        experience=experience_store,
    )
