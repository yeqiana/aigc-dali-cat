"""Story OS Runtime MySQL 表结构（DDL）。

P9.26.4 Runtime Data Persistence Migration 的数据结构定义。
全部 IF NOT EXISTS，幂等可重复执行。
"""

from __future__ import annotations

from platform.repository.mysql.mysql_connection import MySqlConnection

DATABASE_NAME = "story_os_runtime"

CREATE_DATABASE_SQL = (
    "CREATE DATABASE IF NOT EXISTS " + DATABASE_NAME +
    " DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
)

CREATE_EVENT_TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS " + DATABASE_NAME + ".event_log ("
    "event_id VARCHAR(64) NOT NULL,"
    "event_type VARCHAR(64) NOT NULL,"
    "aggregate_type VARCHAR(64) NOT NULL,"
    "aggregate_id VARCHAR(64) NOT NULL,"
    "occurred_at DATETIME(6) NOT NULL,"
    "trace_id VARCHAR(64) NULL,"
    "task_id VARCHAR(64) NULL,"
    "payload JSON NULL,"
    "metadata JSON NULL,"
    "created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),"
    "PRIMARY KEY (event_id),"
    "KEY idx_event_aggregate (aggregate_type, aggregate_id),"
    "KEY idx_event_occurred_at (occurred_at),"
    "KEY idx_event_trace_id (trace_id)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
)

CREATE_TRACE_TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS " + DATABASE_NAME + ".trace_span ("
    "trace_id VARCHAR(64) NOT NULL,"
    "span_id VARCHAR(64) NOT NULL,"
    "operation VARCHAR(128) NOT NULL,"
    "status VARCHAR(32) NOT NULL,"
    "started_at DATETIME(6) NOT NULL,"
    "request_id VARCHAR(64) NULL,"
    "episode_id VARCHAR(64) NULL,"
    "task_id VARCHAR(64) NULL,"
    "parent_span_id VARCHAR(64) NULL,"
    "ended_at DATETIME(6) NULL,"
    "duration_ms BIGINT NULL,"
    "inputs JSON NULL,"
    "outputs JSON NULL,"
    "error TEXT NULL,"
    "attributes JSON NULL,"
    "created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),"
    "PRIMARY KEY (trace_id, span_id),"
    "KEY idx_trace_operation (operation),"
    "KEY idx_trace_started_at (started_at),"
    "KEY idx_trace_episode_id (episode_id)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
)

CREATE_ARTIFACT_TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS " + DATABASE_NAME + ".artifact_index ("
    "artifact_id VARCHAR(64) NOT NULL,"
    "artifact_type VARCHAR(64) NOT NULL,"
    "path VARCHAR(1024) NOT NULL,"
    "sha256 CHAR(64) NOT NULL,"
    "owner_type VARCHAR(64) NOT NULL,"
    "owner_id VARCHAR(64) NOT NULL,"
    "created_by VARCHAR(128) NOT NULL,"
    "created_at DATETIME(6) NOT NULL,"
    "trace_id VARCHAR(64) NULL,"
    "task_id VARCHAR(64) NULL,"
    "metadata JSON NULL,"
    "PRIMARY KEY (artifact_id),"
    "KEY idx_artifact_owner (owner_type, owner_id),"
    "KEY idx_artifact_sha256 (sha256),"
    "KEY idx_artifact_type (artifact_type),"
    "KEY idx_artifact_created_at (created_at)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
)


def apply_schema(connection: MySqlConnection) -> list[str]:
    """幂等建库建表，返回执行顺序描述。"""
    connection.execute(CREATE_DATABASE_SQL)
    connection.execute(CREATE_EVENT_TABLE_SQL)
    connection.execute(CREATE_TRACE_TABLE_SQL)
    connection.execute(CREATE_ARTIFACT_TABLE_SQL)
    return [
        "create_database",
        "create_event_log",
        "create_trace_span",
        "create_artifact_index",
    ]
