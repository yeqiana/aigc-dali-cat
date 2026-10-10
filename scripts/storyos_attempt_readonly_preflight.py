#!/usr/bin/env python3
"""Read-only Episode Generation Attempt triage.

This command never reserves/releases an Attempt, changes a lease, or dispatches
images. Use the authenticated production-env wrapper; do not substitute a
JSON/fixture projection for MySQL Authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform.repository.mysql.schema_v2 import DATABASE_NAME


def canonical_episode(raw: str, *, root: Path = ROOT) -> tuple[Path, str]:
    root = Path(root).resolve()
    folder = Path(raw)
    episode = (folder if folder.is_absolute() else root / folder).resolve()
    allowed = root / "episodes"
    if not episode.is_dir() or not episode.is_relative_to(allowed):
        raise ValueError("ATTEMPT_READONLY_EPISODE_PATH_INVALID")
    return episode, episode.relative_to(allowed).as_posix()


def inspect_attempt_history(connection, *, episode_id: str) -> dict:
    result = {"read_only": True, "sql_writes": 0, "model_calls": 0,
              "status": "BLOCKED", "episode_id": episode_id}
    try:
        identity = connection.query_one(
            "SELECT DATABASE() AS selected_database, @@lower_case_table_names AS case_mode"
        ) or {}
        if (identity.get("selected_database") != DATABASE_NAME
                or identity.get("case_mode") != 0):
            result["reason"] = "ATTEMPT_READONLY_DATABASE_IDENTITY_MISMATCH"
            return result
        result["database_identity_verified"] = True
        attempts = connection.query_all(
            "SELECT LOGICAL_ASSET_KEY, ATTEMPT_INDEX, STATUS FROM TB_GENERATION_ATTEMPT "
            "WHERE EPISODE_ID=%s ORDER BY LOGICAL_ASSET_KEY, ATTEMPT_INDEX",
            (episode_id,),
        ) or []
        asset_states = connection.query_all(
            "SELECT LOGICAL_ASSET_KEY, ATTEMPTS_CONSUMED, ACTIVE_ATTEMPT_INDEX "
            "FROM TB_GENERATION_ASSET_STATE WHERE EPISODE_ID=%s ORDER BY LOGICAL_ASSET_KEY",
            (episode_id,),
        ) or []
        counts = dict(sorted(Counter(str(row.get("STATUS") or "UNKNOWN") for row in attempts).items()))
        unknown = sorted({
            str(row.get("LOGICAL_ASSET_KEY") or "") for row in attempts
            if str(row.get("STATUS") or "") == "OUTCOME_UNKNOWN"
        })
        active_statuses = {"RESERVED", "DISPATCH_COMMITTED"}
        known_terminal = {"SUCCEEDED", "FAILED_AFTER_DISPATCH", "OUTCOME_UNKNOWN",
                          "RELEASED_PRE_DISPATCH"}
        active = sorted({
            str(row.get("LOGICAL_ASSET_KEY") or "") for row in attempts
            if str(row.get("STATUS") or "") in active_statuses
        } | {
            str(row.get("LOGICAL_ASSET_KEY") or "") for row in asset_states
            if row.get("ACTIVE_ATTEMPT_INDEX") is not None
        })
        unverified = sorted({
            str(row.get("LOGICAL_ASSET_KEY") or "") for row in attempts
            if str(row.get("STATUS") or "") not in active_statuses | known_terminal
        })
        blocked_assets = set(unknown) | set(active) | set(unverified)
        status = ("OUTCOME_UNKNOWN_BLOCKED" if unknown else
                  "ACTIVE_ATTEMPT_BLOCKED" if active else
                  "UNVERIFIED_ATTEMPT_STATUS_BLOCKED" if unverified else
                  "ATTEMPT_HISTORY_READ_ONLY")
        result.update({
            "status": status,
            "attempt_rows": len(attempts),
            "asset_state_rows": len(asset_states),
            "attempt_status_counts": counts,
            "outcome_unknown_assets": unknown,
            "active_attempt_assets": active,
            "unverified_status_assets": unverified,
            "attempt_budget": [{
                "logical_asset_key": str(row.get("LOGICAL_ASSET_KEY") or ""),
                "attempts_consumed": int(row.get("ATTEMPTS_CONSUMED") or 0),
                "active_attempt_index": row.get("ACTIVE_ATTEMPT_INDEX"),
            } for row in asset_states
              if str(row.get("LOGICAL_ASSET_KEY") or "") in blocked_assets],
            "production_authorization": False,
        })
    except Exception as exc:
        # Exceptions may contain driver credentials. Only expose the class.
        result["reason"] = "ATTEMPT_READONLY_MYSQL_QUERY_FAILED"
        result["error_type"] = type(exc).__name__
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args(argv)
    try:
        _folder, episode_id = canonical_episode(args.episode)
        import storage_config
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.schema_v2 import DATABASE_NAME
        settings = storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
        if not settings.get("password"):
            raise ValueError("ATTEMPT_READONLY_MYSQL_CREDENTIAL_MISSING")
        db = MySqlConnection(**settings)
        try:
            result = inspect_attempt_history(db, episode_id=episode_id)
        finally:
            db.close()
    except Exception as exc:
        result = {"status": "BLOCKED", "read_only": True, "sql_writes": 0,
                  "model_calls": 0, "reason": "ATTEMPT_READONLY_PREFLIGHT_FAILED",
                  "error_type": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "ATTEMPT_HISTORY_READ_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
