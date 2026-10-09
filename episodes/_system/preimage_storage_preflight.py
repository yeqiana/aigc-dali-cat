#!/usr/bin/env python3
"""Read-only V2 schema admission probe. Never creates/migrates databases."""
from __future__ import annotations

import argparse
import json

import storage_config
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DATABASE_NAME

REQUIRED_TABLES = frozenset({
    "TB_SCHEMA_VERSION",
    "TB_EPISODE_STATE",
    "TB_RUNTIME_REVIEW_REQUEST",
    "TB_EPISODE_CONTRACT",
})


def inspect() -> dict:
    """Inspect exact schema identity, without exposing host/user/credentials."""
    connection = None
    try:
        kwargs = storage_config.mysql_connection_kwargs(
            {"database": "information_schema"})
        connection = MySqlConnection(**kwargs)
        rows = connection.query_all("SHOW DATABASES")
        names = {
            str(next(iter(row.values())))
            for row in rows if isinstance(row, dict) and row
        }
        exact = DATABASE_NAME in names
        if not exact:
            return {
                "status": "V2_SCHEMA_MISSING",
                "v2_schema": DATABASE_NAME,
                "case_only_schema_present": any(
                    x.casefold() == DATABASE_NAME.casefold() for x in names),
                "schema_check_passed": False,
                "production_authority_granted": False,
                "read_only": True,
            }
        tables = connection.query_all(
            "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s",
            (DATABASE_NAME,))
        existing = {
            str(row.get("TABLE_NAME") or row.get("table_name") or "")
            for row in tables if isinstance(row, dict)
        }
        missing = sorted(REQUIRED_TABLES - existing)
        return {
            "status": "V2_TABLES_MISSING" if missing else "V2_SCHEMA_PRESENT_UNATTESTED",
            "v2_schema": DATABASE_NAME,
            "missing_required_tables": missing,
            "schema_check_passed": not bool(missing),
            "production_authority_granted": False,
            "read_only": True,
        }
    except Exception as exc:
        return {
            "status": "V2_SCHEMA_PROBE_FAILED",
            "error_type": type(exc).__name__,
            "schema_check_passed": False,
                "production_authority_granted": False,
            "read_only": True,
        }
    finally:
        if connection is not None:
            connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check",))
    parser.parse_args()
    result = inspect()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "V2_SCHEMA_PRESENT_UNATTESTED" else 22


if __name__ == "__main__":
    raise SystemExit(main())
