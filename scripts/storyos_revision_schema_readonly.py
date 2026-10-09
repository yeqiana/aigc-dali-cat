#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed, SELECT-only Production Revision schema admission report.

Run via scripts/storyos_production_env.py. Never creates tables, migrates,
grants permissions, changes Episode/Attempt/Review state, or prints credentials.
A READY report covers schema presence only: it never authorizes image dispatch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from platform.repository.mysql.schema_v2 import DATABASE_NAME

REVISION_TABLES = (
    "TB_PRODUCTION_REVISION",
    "TB_PRODUCTION_REVISION_HEAD",
    "TB_PRODUCTION_REVISION_FRAME",
    "TB_PRODUCTION_REVISION_VISUAL_ADMISSION",
)
DEPENDENCIES = ("TB_GENERATION_ATTEMPT", "TB_REVIEW_RECORD")
REQUIRED_STATES = (
    "CREATED", "PREPARED", "VISUAL_LOCK_PENDING", "READY", "ACTIVE", "RETIRED",
)
CONSTRAINT = "CHECK_TB_PRODUCTION_REVISION_STATUS"


def inspect_revision_schema(connection) -> dict:
    """Only SELECT metadata from the caller's existing authorized connection."""
    info = connection.query_one(
        "SELECT DATABASE() AS db, @@lower_case_table_names AS case_mode, VERSION() AS version"
    )
    if not info or info.get("db") != DATABASE_NAME or info.get("case_mode") != 0:
        return {
            "status": "BLOCKED", "reason": "DATABASE_IDENTITY_OR_CASE_MODE_MISMATCH",
            "schema_matches": False, "revision_tables": {}, "dependencies": {},
            "lifecycle_constraint_ready": False,
        }
    names = REVISION_TABLES + DEPENDENCIES
    placeholders = ",".join(["%s"] * len(names))
    records = connection.query_all(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        f"WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN ({placeholders})",
        (DATABASE_NAME, *names),
    ) or []
    existing = {str(row["TABLE_NAME"]) for row in records}
    revision_tables = {name: name in existing for name in REVISION_TABLES}
    dependencies = {name: name in existing for name in DEPENDENCIES}
    ready_check = False
    if revision_tables["TB_PRODUCTION_REVISION"]:
        rows = connection.query_all(
            "SELECT CHECK_CLAUSE FROM information_schema.CHECK_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA=%s AND CONSTRAINT_NAME=%s",
            (DATABASE_NAME, CONSTRAINT),
        ) or []
        clause = str((rows[0] if rows else {}).get("CHECK_CLAUSE") or "").upper()
        ready_check = all(f"'{state}'" in clause for state in REQUIRED_STATES)
    ready = all(revision_tables.values()) and all(dependencies.values()) and ready_check
    return {
        "status": "READY_FOR_FURTHER_ADMISSION" if ready else "BLOCKED",
        "reason": "SCHEMA_PRESENT_REQUIRES_VISUAL_LOCK_AND_AUTHORITY" if ready
                  else "PRODUCTION_REVISION_SCHEMA_INCOMPLETE",
        "schema_matches": True,
        "mysql_version": str(info.get("version") or ""),
        "revision_tables": revision_tables,
        "dependencies": dependencies,
        "lifecycle_constraint_ready": ready_check,
        "migration_performed": False,
        "production_activation_performed": False,
    }


def main() -> int:
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from episodes._system import storage_config

    conn = None
    try:
        conn = MySqlConnection(
            **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
        )
        result = inspect_revision_schema(conn)
    except Exception:
        # Do not log exception strings: DSNs and credentials can appear in errors.
        result = {
            "status": "BLOCKED", "reason": "SCHEMA_READONLY_QUERY_FAILED",
            "migration_performed": False, "production_activation_performed": False,
        }
    finally:
        if conn is not None:
            conn.close()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "READY_FOR_FURTHER_ADMISSION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
