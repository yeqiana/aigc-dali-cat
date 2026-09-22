from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_identity
import storage_config

from platform.repository.mysql.schema_v2 import DATABASE_NAME


def mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]


def _repository():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_production_recovery_journal_repository import (
        MySqlProductionRecoveryJournalRepository,
    )

    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return connection, MySqlProductionRecoveryJournalRepository(connection)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def update_transaction(
    ep: Path,
    transaction_id: str,
    phase: str,
    *,
    details: dict | None = None,
) -> dict:
    """Merge and persist one recovery transaction in MySQL.

    JSON/dual compatibility writing stays in production_recovery._journal; this
    module owns only the MySQL document authority.
    """
    ep = Path(ep).resolve()
    current_mode = mode()
    if current_mode == "json":
        return {"mode": current_mode, "mysql_written": False}
    episode_id = episode_identity.storage_episode_id(ep)
    connection, repository = _repository()
    try:
        with connection.transaction():
            existing = repository.get(transaction_id)
            existing_episode_id = (
                str(existing.get("episode_id") or "").strip()
                if isinstance(existing, dict)
                else ""
            )
            if existing_episode_id and existing_episode_id != str(episode_id):
                raise ValueError(
                    "production recovery transaction belongs to another episode"
                )
            document = (
                dict(existing.get("document") or {})
                if isinstance(existing, dict)
                else {}
            )
            document.setdefault("transaction_id", str(transaction_id))
            document.setdefault("created_at", now())
            document.update(
                {
                    "phase": str(phase),
                    "updated_at": now(),
                    **dict(details or {}),
                }
            )
            result = repository.upsert(episode_id, transaction_id, document)
        return {"mode": current_mode, "mysql_written": True, **result}
    finally:
        connection.close()


def load_transaction(ep: Path, transaction_id: str) -> dict | None:
    ep = Path(ep).resolve()
    if mode() == "json":
        return None
    episode_id = episode_identity.storage_episode_id(ep)
    connection, repository = _repository()
    try:
        row = repository.get(transaction_id)
        if not row:
            return None
        existing_episode_id = str(row.get("episode_id") or "").strip()
        if existing_episode_id and existing_episode_id != str(episode_id):
            raise ValueError(
                "production recovery transaction belongs to another episode"
            )
        document = row.get("document")
        return document if isinstance(document, dict) else None
    finally:
        connection.close()
