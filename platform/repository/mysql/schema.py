"""Compatibility schema entry for the remaining platform_latest_record table.

Runtime Event / Trace / Artifact have moved to schema_v2 TB_* tables.  This
module must never recreate the retired lowercase event_log / trace_span /
artifact_index tables after the storage cutover.
"""

from __future__ import annotations

from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DATABASE_NAME, apply_schema as apply_v2_schema


CREATE_PLATFORM_LATEST_RECORD_TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS " + DATABASE_NAME + ".platform_latest_record ("
    "namespace VARCHAR(64) NOT NULL,"
    "record_key VARCHAR(128) NOT NULL,"
    "payload JSON NOT NULL,"
    "created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),"
    "updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),"
    "PRIMARY KEY (namespace, record_key),"
    "KEY idx_platform_latest_record_updated_at (updated_at)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
)


def apply_schema(connection: MySqlConnection) -> list[str]:
    """Apply canonical V2 schema plus the still-used latest-record table."""
    steps = apply_v2_schema(connection)
    connection.execute(CREATE_PLATFORM_LATEST_RECORD_TABLE_SQL)
    return [*steps, "create_platform_latest_record"]
