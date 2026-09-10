"""MySQL Trace Repository（P9.26.4 真实持久化实现）。"""

from __future__ import annotations

import json
from typing import Protocol

from platform.core.contracts.trace_contract import TraceContract
from platform.repository.mysql.mysql_connection import MySqlConnection


class TraceRepository(Protocol):
    def save(self, trace: TraceContract) -> None: ...


_TRACE_UPSERT_SQL = (
    "INSERT INTO trace_span "
    "(trace_id, span_id, operation, status, started_at, request_id, episode_id, "
    " task_id, parent_span_id, ended_at, duration_ms, inputs, outputs, error, attributes) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "AS new "
    "ON DUPLICATE KEY UPDATE "
    "operation=new.operation, status=new.status, started_at=new.started_at, "
    "request_id=new.request_id, episode_id=new.episode_id, task_id=new.task_id, "
    "parent_span_id=new.parent_span_id, ended_at=new.ended_at, "
    "duration_ms=new.duration_ms, inputs=new.inputs, outputs=new.outputs, "
    "error=new.error, attributes=new.attributes"
)

_TRACE_SELECT_SQL = "SELECT * FROM trace_span WHERE trace_id = %s AND span_id = %s"
_TRACE_LIST_SQL = "SELECT * FROM trace_span ORDER BY started_at"
_TRACE_PAGE_SQL = (
    "SELECT * FROM trace_span WHERE (trace_id, span_id) > (%s, %s) "
    "ORDER BY trace_id, span_id LIMIT %s"
)


class MySqlTraceRepository:
    """Trace/Span 事实的 MySQL 持久化。

    以 (trace_id, span_id) 为主键幂等写入。
    """

    def __init__(self, connection: MySqlConnection | None = None):
        self.connection = connection

    def _conn(self) -> MySqlConnection:
        if self.connection is None:
            raise RuntimeError("MySqlTraceRepository requires a MySqlConnection")
        return self.connection

    def save(self, trace: TraceContract) -> None:
        self._conn().execute(_TRACE_UPSERT_SQL, (
            trace.trace_id,
            trace.span_id,
            trace.operation,
            trace.status.value,
            trace.started_at,
            trace.request_id,
            trace.episode_id,
            trace.task_id,
            trace.parent_span_id,
            trace.ended_at,
            trace.duration_ms,
            json.dumps(trace.inputs, ensure_ascii=False),
            json.dumps(trace.outputs, ensure_ascii=False),
            trace.error,
            json.dumps(trace.attributes, ensure_ascii=False),
        ))

    def get(self, trace_id: str, span_id: str) -> dict | None:
        return self._conn().query_one(_TRACE_SELECT_SQL, (trace_id, span_id))

    def list_all(self) -> list[dict]:
        return self._conn().query_all(_TRACE_LIST_SQL)

    def iter_all(self, batch_size: int = 500):
        """按复合主键 keyset 分页流式读取（P9.27）。"""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last_trace = ""
        last_span = ""
        while True:
            rows = self._conn().query_all(
                _TRACE_PAGE_SQL, (last_trace, last_span, batch_size)
            )
            if not rows:
                return
            for row in rows:
                yield row
            last_trace = rows[-1]["trace_id"]
            last_span = rows[-1]["span_id"]
            if len(rows) < batch_size:
                return
