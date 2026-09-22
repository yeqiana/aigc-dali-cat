from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_identity
import storage_config

from platform.repository.mysql.schema_v2 import DATABASE_NAME


class ProductionLedgerAuthorityIncomplete(RuntimeError):
    """Compatibility exception retained for callers from the pre-cutover era."""


def mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]


def assert_full_authority_available() -> None:
    """The complete ledger is now losslessly persisted in MySQL.

    TB_PRODUCTION_LEDGER_AUTHORITY is the document authority; typed
    TB_PRODUCTION_FRAME/TB_PRODUCTION_ATTEMPT remain query projections.
    """
    return None


def _repositories():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_production_attempt_repository import (
        MySqlProductionAttemptRepository,
    )
    from platform.repository.mysql.mysql_production_frame_repository import (
        MySqlProductionFrameRepository,
    )
    from platform.repository.mysql.mysql_production_ledger_authority_repository import (
        MySqlProductionLedgerAuthorityRepository,
    )

    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return (
        connection,
        MySqlProductionLedgerAuthorityRepository(connection),
        MySqlProductionFrameRepository(connection),
        MySqlProductionAttemptRepository(connection),
    )


def _contract_sha(frame: dict) -> str | None:
    attempts = frame.get("attempts") or []
    if not attempts:
        return None
    request = (attempts[-1] or {}).get("request") or {}
    direct = request.get("frame_contract_sha256")
    if direct:
        return str(direct)
    nested = request.get("frame_contract") or {}
    value = nested.get("contract_sha256")
    return str(value) if value else None


def _attempt_record(
    episode_id: str,
    frame_no: int,
    attempt_no: int,
    attempt: dict,
) -> dict:
    request = attempt.get("request") or {}
    provider_attempt = attempt.get("provider_attempt") or {}
    error = attempt.get("error") or {}
    return {
        "attempt_id": str(attempt.get("attempt_id") or ""),
        "episode_id": episode_id,
        "frame_no": int(frame_no),
        "attempt_no": int(attempt_no),
        "attempt_kind": str(attempt.get("kind") or "unknown"),
        "status": str(attempt.get("result") or "pending"),
        "provider": provider_attempt.get("provider"),
        "model": provider_attempt.get("model") or request.get("model"),
        "artifact_id": None,
        "error_code": error.get("code"),
        "elapsed_ms": provider_attempt.get("elapsed_ms"),
        "start_time": attempt.get("started_at"),
        "end_time": attempt.get("completed_at"),
        "payload": attempt,
    }


def _persist_projection(episode_id: str, data: dict, frames_repo, attempts_repo) -> tuple[int, int]:
    frame_count = 0
    attempt_count = 0
    for raw_key, frame in sorted((data.get("frames") or {}).items()):
        if not isinstance(frame, dict):
            continue
        frame_no = int(frame.get("number") or raw_key)
        attempts = [
            row for row in (frame.get("attempts") or [])
            if isinstance(row, dict)
        ]
        for index, attempt in enumerate(attempts, 1):
            record = _attempt_record(episode_id, frame_no, index, attempt)
            if not record["attempt_id"]:
                # Historical ledgers can contain placeholder attempts. They stay
                # losslessly available in the authority BLOB but are not valid
                # typed attempt identities.
                continue
            attempts_repo.upsert(record)
            attempt_count += 1
        frames_repo.upsert({
            "episode_id": episode_id,
            "frame_no": frame_no,
            "status": str(frame.get("status") or "PENDING"),
            "approved_artifact_id": None,
            "current_attempt_id": (
                str(attempts[-1].get("attempt_id"))
                if attempts and attempts[-1].get("attempt_id")
                else None
            ),
            "contract_sha256": _contract_sha(frame),
        })
        frame_count += 1
    return frame_count, attempt_count


def persist_authority(ep: Path, data: dict) -> dict:
    """Persist the complete ledger and its typed query projection atomically."""
    ep = Path(ep).resolve()
    current_mode = mode()
    if current_mode == "json":
        return {
            "mode": current_mode,
            "mysql_written": False,
            "frame_count": 0,
            "attempt_count": 0,
        }
    episode_id = episode_identity.storage_episode_id(ep)
    connection, authority_repo, frames_repo, attempts_repo = _repositories()
    try:
        with connection.transaction():
            authority = authority_repo.upsert(episode_id, data)
            frame_count, attempt_count = _persist_projection(
                episode_id, data, frames_repo, attempts_repo
            )
        return {
            "mode": current_mode,
            "mysql_written": True,
            "frame_count": frame_count,
            "attempt_count": attempt_count,
            **authority,
        }
    finally:
        connection.close()


def persist_projection(ep: Path, data: dict) -> dict:
    """Compatibility API: projections are now written with full authority."""
    return persist_authority(ep, data)


def load_authority(ep: Path) -> dict | None:
    ep = Path(ep).resolve()
    if mode() == "json":
        return None
    episode_id = episode_identity.storage_episode_id(ep)
    connection, authority_repo, _frames_repo, _attempts_repo = _repositories()
    try:
        row = authority_repo.get(episode_id)
        if not row:
            return None
        document = row.get("document")
        return document if isinstance(document, dict) else None
    finally:
        connection.close()
