#!/usr/bin/env python3
"""Read-only audit of JSON columns in the configured MySQL database.

The audit never selects JSON values. It reports only row counts and byte
aggregates, so it is safe to run against a live runtime database.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import storage_config  # noqa: E402
from platform.repository.mysql.mysql_connection import MySqlConnection  # noqa: E402
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES  # noqa: E402
from scripts.phase9_runtime_launcher import load_runtime_env_file  # noqa: E402


def _quote_identifier(value: str) -> str:
    return "`" + str(value).replace("`", "``") + "`"


def audit(connection, threshold: int = MAX_INLINE_PAYLOAD_BYTES) -> dict:
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    columns = connection.query_all(
        "SELECT TABLE_NAME, COLUMN_NAME "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND DATA_TYPE='json' "
        "ORDER BY TABLE_NAME, ORDINAL_POSITION"
    )
    rows = []
    for column in columns:
        table = str(column["TABLE_NAME"])
        name = str(column["COLUMN_NAME"])
        table_sql = _quote_identifier(table)
        column_sql = _quote_identifier(name)
        result = connection.query_one(
            f"SELECT COUNT(*) AS total_rows, "
            f"COALESCE(SUM(OCTET_LENGTH({column_sql})), 0) AS total_bytes, "
            f"COALESCE(MAX(OCTET_LENGTH({column_sql})), 0) AS max_bytes, "
            f"SUM(CASE WHEN OCTET_LENGTH({column_sql}) > %s THEN 1 ELSE 0 END) AS oversized_rows "
            f"FROM {table_sql}",
            (threshold,),
        ) or {}
        rows.append({
            "table": table,
            "column": name,
            "total_rows": int(result.get("total_rows") or 0),
            "total_bytes": int(result.get("total_bytes") or 0),
            "max_bytes": int(result.get("max_bytes") or 0),
            "oversized_rows": int(result.get("oversized_rows") or 0),
        })
    rows.sort(key=lambda item: (-item["max_bytes"], -item["total_bytes"], item["table"], item["column"]))
    return {
        "database": connection.health_check().get("database"),
        "threshold_bytes": threshold,
        "json_columns": len(rows),
        "oversized_columns": sum(1 for row in rows if row["oversized_rows"]),
        "rows": rows,
        "read_only": True,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, default=MAX_INLINE_PAYLOAD_BYTES)
    parser.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = parser.parse_args(argv)
    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs())
    try:
        result = audit(connection, args.threshold)
        result["runtime_env_keys"] = list(loaded)
        result["secret_values_printed"] = False
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
