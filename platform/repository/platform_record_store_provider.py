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
    mysql_connection=None,
) -> PlatformRecordStores:
    """Build non-authoritative Platform record stores.

    No arguments preserves the historical in-process behavior. ``state_root``
    opts into append-only JSONL. ``mysql_connection`` opts into the shared
    ``platform_latest_record`` table created by the normal idempotent schema.
    Explicit stores always win. JSONL and MySQL implicit modes are mutually
    exclusive so a deployment cannot silently split Execution and Experience.
    """

    if state_root is not None and mysql_connection is not None:
        raise ValueError("state_root and mysql_connection are mutually exclusive")
    root = Path(state_root).resolve() if state_root is not None else None
    if mysql_connection is not None and (execution_store is None or experience_store is None):
        from platform.repository.mysql.mysql_latest_record_store import MySqlLatestRecordStore
        if execution_store is None:
            execution_store = MySqlLatestRecordStore(
                mysql_connection, namespace="execution", key_field="execution_id"
            )
        if experience_store is None:
            experience_store = MySqlLatestRecordStore(
                mysql_connection, namespace="experience", key_field="experience_id"
            )
    if execution_store is None and root is not None:
        execution_store = JsonlLatestRecordStore(root / "executions.jsonl", key_field="execution_id")
    if experience_store is None and root is not None:
        experience_store = JsonlLatestRecordStore(root / "experiences.jsonl", key_field="experience_id")
    return PlatformRecordStores(
        execution=execution_store,
        experience=experience_store,
    )
