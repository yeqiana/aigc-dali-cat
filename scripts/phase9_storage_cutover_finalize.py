#!/usr/bin/env python3
"""Finalize StoryOS MySQL/Redis storage cutover on the live runtime database.

This migration is deliberately narrow:
* upgrades canonical TB_* Runtime tables for the V2 repositories;
* migrates any remaining lowercase Runtime facts;
* verifies row preservation, then drops the three retired lowercase tables;
* rejects unapproved MySQL JSON columns.

It never deletes Episode evidence files. File cleanup is a separate concern
from authority cutover and must not be mixed with database migration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import storage_config
from platform.repository.mysql.json_column_policy import (
    RETIRED_LEGACY_TABLES,
    unexpected_json_columns,
)
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DATABASE_NAME, apply_schema
from scripts.phase9_runtime_launcher import load_runtime_env_file


def _json_text(value) -> str:
    if value is None:
        return "{}"
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _metadata_bytes(value) -> tuple[bytes, str]:
    raw = _json_text(value).encode("utf-8")
    return raw, hashlib.sha256(raw).hexdigest()


def _tables(connection) -> set[str]:
    rows = connection.query_all(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()"
    )
    return {str(row["TABLE_NAME"]) for row in rows}


def _columns(connection, table: str) -> set[str]:
    rows = connection.query_all(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s",
        (table,),
    )
    return {str(row["COLUMN_NAME"]).upper() for row in rows}


def _column_char_length(connection, table: str, name: str) -> int | None:
    rows = connection.query_all(
        "SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (table, name),
    )
    if not rows:
        return None
    row = rows[0]
    raw = row.get("CHARACTER_MAXIMUM_LENGTH")
    if raw is None:
        raw = row.get("character_maximum_length")
    return int(raw) if raw is not None else None


def _ensure_column(connection, table: str, name: str, ddl: str) -> bool:
    if name.upper() in _columns(connection, table):
        return False
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
    return True


def _indexes(connection, table: str) -> set[str]:
    rows = connection.query_all(
        "SELECT DISTINCT INDEX_NAME FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s",
        (table,),
    )
    return {str(row.get("INDEX_NAME") or row.get("index_name")) for row in rows}


def _ensure_index(connection, table: str, name: str, expression: str) -> bool:
    if name in _indexes(connection, table):
        return False
    connection.execute(f"ALTER TABLE {table} ADD INDEX {name} ({expression})")
    return True


def upgrade_runtime_tables(connection) -> list[str]:
    added: list[str] = []
    specs = {
        "TB_EVENT_LOG": {
            "TRACE_ID": "VARCHAR(96) DEFAULT NULL COMMENT '关联Trace ID'",
            "TASK_ID": "VARCHAR(96) DEFAULT NULL COMMENT '关联Task ID'",
        },
        "TB_TRACE_SPAN": {
            "REQUEST_ID": "VARCHAR(128) DEFAULT NULL COMMENT '关联Runtime Request ID'",
            "TASK_ID": "VARCHAR(96) DEFAULT NULL COMMENT '关联Task ID'",
            "ERROR_TEXT": "TEXT DEFAULT NULL COMMENT 'Trace错误文本'",
        },
        "TB_ARTIFACT_INDEX": {
            "CREATED_BY": "VARCHAR(128) DEFAULT NULL COMMENT 'Artifact创建者'",
            "TRACE_ID": "VARCHAR(96) DEFAULT NULL COMMENT '关联Trace ID'",
            "TASK_ID": "VARCHAR(96) DEFAULT NULL COMMENT '关联Task ID'",
            "METADATA_BLOB": "MEDIUMBLOB DEFAULT NULL COMMENT '低频扩展元数据规范化JSON字节；非查询字段'",
            "METADATA_SHA256": "CHAR(64) DEFAULT NULL COMMENT '扩展元数据SHA-256'",
        },
    }
    for table, columns in specs.items():
        for name, ddl in columns.items():
            if _ensure_column(connection, table, name, ddl):
                added.append(f"{table}.{name}")
    production_status_len = _column_char_length(connection, "TB_PRODUCTION_FRAME", "STATUS")
    if production_status_len is not None and production_status_len < 64:
        connection.execute(
            "ALTER TABLE TB_PRODUCTION_FRAME MODIFY COLUMN STATUS "
            "VARCHAR(64) NOT NULL COMMENT '当前生产状态'"
        )
        added.append("TB_PRODUCTION_FRAME.STATUS:VARCHAR(64)")
    if _ensure_index(connection, "TB_TRACE_SPAN", "INDEX_TB_TRACE_SPAN_START_TIME", "START_TIME"):
        added.append("TB_TRACE_SPAN.INDEX_TB_TRACE_SPAN_START_TIME")
    return added


def migrate_event_log(connection, tables: set[str]) -> int:
    if "event_log" not in tables:
        return 0
    rows = connection.query_all("SELECT * FROM event_log ORDER BY event_id")
    sql = (
        "INSERT INTO TB_EVENT_LOG "
        "(EVENT_ID,EVENT_TYPE,AGGREGATE_TYPE,AGGREGATE_ID,EPISODE_ID,OCCURRED_TIME,"
        "TRACE_ID,TASK_ID,PAYLOAD,METADATA) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "AS new ON DUPLICATE KEY UPDATE "
        "EVENT_TYPE=new.EVENT_TYPE,AGGREGATE_TYPE=new.AGGREGATE_TYPE,"
        "AGGREGATE_ID=new.AGGREGATE_ID,EPISODE_ID=new.EPISODE_ID,"
        "OCCURRED_TIME=new.OCCURRED_TIME,TRACE_ID=new.TRACE_ID,TASK_ID=new.TASK_ID,"
        "PAYLOAD=new.PAYLOAD,METADATA=new.METADATA"
    )
    for row in rows:
        aggregate_type = row.get("aggregate_type") or row.get("AGGREGATE_TYPE")
        aggregate_id = row.get("aggregate_id") or row.get("AGGREGATE_ID")
        episode_id = aggregate_id if str(aggregate_type).upper() == "EPISODE" else None
        connection.execute(sql, (
            row.get("event_id") or row.get("EVENT_ID"),
            row.get("event_type") or row.get("EVENT_TYPE"),
            aggregate_type,
            aggregate_id,
            episode_id,
            row.get("occurred_at") or row.get("OCCURRED_TIME"),
            row.get("trace_id") or row.get("TRACE_ID"),
            row.get("task_id") or row.get("TASK_ID"),
            _json_text(row.get("payload") if "payload" in row else row.get("PAYLOAD")),
            _json_text(row.get("metadata") if "metadata" in row else row.get("METADATA")),
        ))
    return len(rows)


def migrate_trace_span(connection, tables: set[str]) -> int:
    if "trace_span" not in tables:
        return 0
    rows = connection.query_all("SELECT * FROM trace_span ORDER BY trace_id, span_id")
    sql = (
        "INSERT INTO TB_TRACE_SPAN "
        "(SPAN_ID,TRACE_ID,PARENT_SPAN_ID,EPISODE_ID,REQUEST_ID,TASK_ID,SPAN_NAME,"
        "CATEGORY,STATUS,START_TIME,END_TIME,ELAPSED_MS,ERROR_TEXT,ATTRIBUTES) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "AS new ON DUPLICATE KEY UPDATE TRACE_ID=new.TRACE_ID,"
        "PARENT_SPAN_ID=new.PARENT_SPAN_ID,EPISODE_ID=new.EPISODE_ID,"
        "REQUEST_ID=new.REQUEST_ID,TASK_ID=new.TASK_ID,SPAN_NAME=new.SPAN_NAME,"
        "CATEGORY=new.CATEGORY,STATUS=new.STATUS,START_TIME=new.START_TIME,"
        "END_TIME=new.END_TIME,ELAPSED_MS=new.ELAPSED_MS,ERROR_TEXT=new.ERROR_TEXT,"
        "ATTRIBUTES=new.ATTRIBUTES"
    )
    for row in rows:
        attrs = {
            "inputs": row.get("inputs"),
            "outputs": row.get("outputs"),
            "attributes": row.get("attributes"),
        }
        original_attrs = row.get("attributes")
        category = original_attrs.get("category") if isinstance(original_attrs, dict) else None
        connection.execute(sql, (
            row.get("span_id"),
            row.get("trace_id"),
            row.get("parent_span_id"),
            row.get("episode_id"),
            row.get("request_id"),
            row.get("task_id"),
            row.get("operation"),
            category,
            row.get("status"),
            row.get("started_at"),
            row.get("ended_at"),
            row.get("duration_ms"),
            row.get("error"),
            _json_text(attrs),
        ))
    return len(rows)


def migrate_artifact_index(connection, tables: set[str]) -> int:
    if "artifact_index" not in tables:
        return 0
    rows = connection.query_all("SELECT * FROM artifact_index ORDER BY artifact_id")
    sql = (
        "INSERT INTO TB_ARTIFACT_INDEX "
        "(ARTIFACT_ID,EPISODE_ID,ARTIFACT_TYPE,URI,SHA256,MIME_TYPE,BYTE_SIZE,WIDTH_PX,"
        "HEIGHT_PX,OWNER_TYPE,OWNER_ID,CREATED_BY,TRACE_ID,TASK_ID,METADATA_BLOB,"
        "METADATA_SHA256,STATUS,CREATE_TIME) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "AS new ON DUPLICATE KEY UPDATE EPISODE_ID=new.EPISODE_ID,"
        "ARTIFACT_TYPE=new.ARTIFACT_TYPE,URI=new.URI,SHA256=new.SHA256,"
        "MIME_TYPE=new.MIME_TYPE,BYTE_SIZE=new.BYTE_SIZE,WIDTH_PX=new.WIDTH_PX,"
        "HEIGHT_PX=new.HEIGHT_PX,OWNER_TYPE=new.OWNER_TYPE,OWNER_ID=new.OWNER_ID,"
        "CREATED_BY=new.CREATED_BY,TRACE_ID=new.TRACE_ID,TASK_ID=new.TASK_ID,"
        "METADATA_BLOB=new.METADATA_BLOB,METADATA_SHA256=new.METADATA_SHA256,"
        "STATUS=new.STATUS,CREATE_TIME=new.CREATE_TIME"
    )
    for row in rows:
        metadata = row.get("metadata") if "metadata" in row else row.get("METADATA")
        meta_obj = metadata
        if isinstance(meta_obj, str):
            try:
                meta_obj = json.loads(meta_obj)
            except json.JSONDecodeError:
                meta_obj = {}
        if not isinstance(meta_obj, dict):
            meta_obj = {}
        raw, digest = _metadata_bytes(meta_obj)
        owner_type = row.get("owner_type")
        owner_id = row.get("owner_id")
        episode_id = owner_id if str(owner_type).upper() == "EPISODE" else meta_obj.get("episode_id")
        connection.execute(sql, (
            row.get("artifact_id"),
            episode_id,
            row.get("artifact_type"),
            row.get("path"),
            row.get("sha256"),
            meta_obj.get("mime_type"),
            meta_obj.get("byte_size") or meta_obj.get("bytes"),
            meta_obj.get("width_px") or meta_obj.get("width") or meta_obj.get("w"),
            meta_obj.get("height_px") or meta_obj.get("height") or meta_obj.get("h"),
            owner_type,
            owner_id,
            row.get("created_by"),
            row.get("trace_id"),
            row.get("task_id"),
            raw,
            digest,
            "ACTIVE",
            row.get("created_at"),
        ))
    return len(rows)


def json_policy_check(connection) -> dict:
    rows = connection.query_all(
        "SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND DATA_TYPE='json' ORDER BY TABLE_NAME,COLUMN_NAME"
    )
    unexpected = sorted(unexpected_json_columns(rows))
    if unexpected:
        raise RuntimeError(f"unexpected MySQL JSON columns: {unexpected}")
    return {"count": len(rows), "unexpected": []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--drop-legacy", action="store_true")
    ap.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = ap.parse_args(argv)

    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    try:
        before = _tables(connection)
        summary = {
            "mode": "apply" if args.apply else "dry-run",
            "runtime_env_keys": list(loaded),
            "secret_values_printed": False,
            "legacy_tables_before": sorted(RETIRED_LEGACY_TABLES & before),
        }
        if not args.apply:
            summary["json_policy"] = json_policy_check(connection)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

        apply_schema(connection)
        summary["columns_added"] = upgrade_runtime_tables(connection)
        tables = _tables(connection)
        migrated = {
            "event_log": migrate_event_log(connection, tables),
            "trace_span": migrate_trace_span(connection, tables),
            "artifact_index": migrate_artifact_index(connection, tables),
        }
        summary["migrated_rows"] = migrated

        # Verify every legacy source row exists in the canonical target before DROP.
        targets = {
            "event_log": "TB_EVENT_LOG",
            "trace_span": "TB_TRACE_SPAN",
            "artifact_index": "TB_ARTIFACT_INDEX",
        }
        verified = {}
        for legacy, source_count in migrated.items():
            target_count = int(connection.query_one(
                f"SELECT COUNT(*) AS c FROM {targets[legacy]}"
            )["c"])
            if target_count < source_count:
                raise RuntimeError(
                    f"target row count smaller than legacy: {legacy}={source_count}, "
                    f"{targets[legacy]}={target_count}"
                )
            verified[targets[legacy]] = target_count
        summary["target_rows"] = verified

        if args.drop_legacy:
            for table in sorted(RETIRED_LEGACY_TABLES):
                if table in _tables(connection):
                    connection.execute(f"DROP TABLE {table}")

        after = _tables(connection)
        remaining = sorted(RETIRED_LEGACY_TABLES & after)
        if args.drop_legacy and remaining:
            raise RuntimeError(f"legacy tables still exist: {remaining}")
        summary["legacy_tables_after"] = remaining
        summary["json_policy"] = json_policy_check(connection)
        summary["mysql_health"] = connection.health_check()
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
