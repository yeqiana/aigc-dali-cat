#!/usr/bin/env python3
"""Read-only Production Revision schema admission audit (never migrates).

Run from the canonical checkout via:
  python scripts/storyos_production_env.py scripts/storyos_revision_schema_preflight.py

This script performs SELECT queries only. It neither creates a Revision nor
calls CREATE/ALTER/UPDATE/DELETE, GET_LOCK or real image providers.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform.repository.mysql.schema_v2 import DATABASE_NAME  # noqa: E402

REVISION_TABLES = (
    "TB_PRODUCTION_REVISION",
    "TB_PRODUCTION_REVISION_HEAD",
    "TB_PRODUCTION_REVISION_FRAME",
    "TB_PRODUCTION_REVISION_VISUAL_ADMISSION",
    "TB_GENERATION_ATTEMPT",
    "TB_GENERATION_ASSET_STATE",
)
REQUIRED_STATES = (
    "PREPARING", "CREATED", "PREPARED", "VISUAL_LOCK_PENDING",
    "READY", "ACTIVE", "RETIRED", "FAILED",
)


def audit_schema(connection, *, expected_database: str = DATABASE_NAME) -> dict:
    """Only SELECT from DATABASE() and information_schema; no DDL or writes."""
    report = {
        "status": "BLOCKED",
        "read_only": True,
        "sql_writes": 0,
        "provider_calls": 0,
        "expected_database": expected_database,
    }
    try:
        selected = connection.query_one("SELECT DATABASE() AS selected_database") or {}
        actual = str(selected.get("selected_database") or "")
        report["database_matches"] = actual.casefold() == expected_database.casefold()
        if not report["database_matches"]:
            report["reason"] = "PRODUCTION_REVISION_SCHEMA_WRONG_DATABASE"
            return report

        rows = connection.query_all(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN "
            "(%s,%s,%s,%s,%s,%s)", REVISION_TABLES,
        ) or []
        existing = {str(r.get("TABLE_NAME") or "").upper() for r in rows}
        missing = sorted(set(REVISION_TABLES) - existing)
        report["present_table_count"] = len(REVISION_TABLES) - len(missing)
        report["required_table_count"] = len(REVISION_TABLES)
        report["missing_tables"] = missing
        if missing:
            report["reason"] = "PRODUCTION_REVISION_SCHEMA_TABLES_MISSING"
            return report

        constraints = connection.query_all(
            "SELECT CHECK_CLAUSE FROM information_schema.CHECK_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA=DATABASE() AND "
            "CONSTRAINT_NAME=%s",
            ("CHECK_TB_PRODUCTION_REVISION_STATUS",),
        ) or []
        clause = str((constraints[0] if constraints else {}).get("CHECK_CLAUSE") or "").upper()
        missing_states = [state for state in REQUIRED_STATES if f"'{state}'" not in clause]
        report["missing_revision_states"] = missing_states
        if missing_states:
            report["reason"] = "PRODUCTION_REVISION_SCHEMA_LIFECYCLE_MIGRATION_REQUIRED"
            return report
        report.update({
            "status": "SCHEMA_READONLY_VERIFIED",
            "reason": "SCHEMA_ONLY_NOT_A_PRODUCTION_RELEASE_GATE",
        })
    except Exception as exc:
        # Database exceptions sometimes embed connection details. Do not echo.
        report["reason"] = "PRODUCTION_REVISION_SCHEMA_QUERY_FAILED"
        report["error_type"] = type(exc).__name__
    return report


def main() -> int:
    import storage_config
    from platform.repository.mysql.mysql_connection import MySqlConnection

    connection = None
    try:
        settings = storage_config.mysql_connection_kwargs()
        if not settings.get("password"):
            result = {"status": "BLOCKED", "read_only": True, "sql_writes": 0,
                      "provider_calls": 0,
                      "reason": "PRODUCTION_REVISION_SCHEMA_CREDENTIAL_MISSING"}
        else:
            connection = MySqlConnection(**settings)
            result = audit_schema(connection)
    except Exception as exc:
        result = {"status": "BLOCKED", "read_only": True, "sql_writes": 0,
                  "provider_calls": 0, "reason": "PRODUCTION_REVISION_SCHEMA_CONNECTION_FAILED",
                  "error_type": type(exc).__name__}
    finally:
        if connection is not None:
            connection.close()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "SCHEMA_READONLY_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
