#!/usr/bin/env python3
"""SELECT-only plan for the explicit UNKNOWN Recovery Authorization table."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from platform.repository.mysql import schema_v2

TABLE = "TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION"
STEP = "create_generation_unknown_recovery_authorization"


def plan(connection) -> dict:
    base = {"migration_performed": False, "ddl_authorized": False,
            "backup_verified": False, "production_dispatch_performed": False}
    identity = connection.query_one(
        "SELECT DATABASE() AS db, @@lower_case_table_names AS case_mode") or {}
    if identity.get("db") != schema_v2.DATABASE_NAME or identity.get("case_mode") != 0:
        return {**base, "status": "BLOCKED", "reason": "DATABASE_IDENTITY_OR_CASE_MODE_MISMATCH"}
    rows = connection.query_all(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
        (schema_v2.DATABASE_NAME, TABLE)) or []
    if any(str(row.get("TABLE_NAME")) == TABLE for row in rows):
        return {**base, "status": "ALREADY_INSTALLED", "reason": "NO_DDL_NEEDED"}
    ddl = dict(schema_v2.DDL_STEPS).get(STEP)
    if not ddl or not ddl.startswith(f"CREATE TABLE IF NOT EXISTS {TABLE} ("):
        return {**base, "status": "BLOCKED", "reason": "CANONICAL_DDL_STEP_MISSING_OR_DRIFTED"}
    return {**base, "status": "PLAN_READY_NOT_AUTHORIZED", "reason": "RECOVERY_AUTHORITY_TABLE_ABSENT",
            "ddl_steps": [{"name": STEP, "sha256": hashlib.sha256(ddl.encode("utf-8")).hexdigest()}],
            "required_before_ddl": ["VERIFIED_BACKUP_RESTORE", "MAINTENANCE_APPROVAL",
                                    "SCHEDULERS_QUIESCED", "RECHECK_SCHEMA",
                                    "CONTROLLED_MIGRATION", "POSTCHECK"]}


def main() -> int:
    try:
        import storage_config
        from platform.repository.mysql.mysql_connection import MySqlConnection
        connection = MySqlConnection(**storage_config.mysql_connection_kwargs(
            {"database": schema_v2.DATABASE_NAME}))
        try:
            result = plan(connection)
        finally:
            connection.close()
    except Exception:
        result = {"status": "BLOCKED", "reason": "SCHEMA_QUERY_FAILED",
                  "migration_performed": False, "ddl_authorized": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"PLAN_READY_NOT_AUTHORIZED", "ALREADY_INSTALLED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
