"""MySQL Trace Repository（P9.26.4 真实持久化实现）。"""

from __future__ import annotations

from typing import Protocol

from platform.core.contracts.trace_contract import TraceContract
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.payload_policy import bounded_json


class TraceRepository(Protocol):
    def save(self, trace: TraceContract) -> None: ...


_TRACE_UPSERT_SQL = (
    "INSERT INTO TB_TRACE_SPAN "
    "(SPAN_ID, TRACE_ID, PARENT_SPAN_ID, EPISODE_ID, REQUEST_ID, TASK_ID, "
    " SPAN_NAME, CATEGORY, STATUS, START_TIME, END_TIME, ELAPSED_MS, ERROR_TEXT, ATTRIBUTES) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "AS new "
    "ON DUPLICATE KEY UPDATE "
    "TRACE_ID=new.TRACE_ID, PARENT_SPAN_ID=new.PARENT_SPAN_ID, "
    "EPISODE_ID=new.EPISODE_ID, REQUEST_ID=new.REQUEST_ID, TASK_ID=new.TASK_ID, "
    "SPAN_NAME=new.SPAN_NAME, CATEGORY=new.CATEGORY, STATUS=new.STATUS, "
    "START_TIME=new.START_TIME, END_TIME=new.END_TIME, ELAPSED_MS=new.ELAPSED_MS, "
    "ERROR_TEXT=new.ERROR_TEXT, ATTRIBUTES=new.ATTRIBUTES"
)

_TRACE_SELECT_SQL = "SELECT * FROM TB_TRACE_SPAN WHERE TRACE_ID = %s AND SPAN_ID = %s"
_TRACE_LIST_SQL = "SELECT * FROM TB_TRACE_SPAN ORDER BY START_TIME"
_TRACE_PAGE_SQL = (
    "SELECT * FROM TB_TRACE_SPAN WHERE (TRACE_ID, SPAN_ID) > (%s, %s) "
    "ORDER BY TRACE_ID, SPAN_ID LIMIT %s"
)


def _normalize_row(row: dict | None) -> dict | None:
    """将 MySQL 驱动返回的列名统一为仓库约定的小写。"""
    if row is None:
        return None
    normalized = {str(key).lower(): value for key, value in row.items()}
    # TB_TRACE_SPAN 的数据库命名与 TraceContract 命名不同，读出时统一为契约字段。
    aliases = {
        "span_name": "operation",
        "start_time": "started_at",
        "end_time": "ended_at",
        "elapsed_ms": "duration_ms",
        "error_text": "error",
    }
    for source, target in aliases.items():
        if source in normalized and target not in normalized:
            normalized[target] = normalized[source]
    return normalized


def _normalize_rows(rows: list[dict]) -> list[dict]:
    return [_normalize_row(row) or {} for row in rows]


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
        attrs = {
            "inputs": trace.inputs,
            "outputs": trace.outputs,
            "attributes": trace.attributes,
        }
        category = trace.attributes.get("category") if isinstance(trace.attributes, dict) else None
        self._conn().execute(_TRACE_UPSERT_SQL, (
            trace.span_id,
            trace.trace_id,
            trace.parent_span_id,
            trace.episode_id,
            trace.request_id,
            trace.task_id,
            trace.operation,
            category,
            trace.status.value,
            trace.started_at,
            trace.ended_at,
            trace.duration_ms,
            trace.error,
            bounded_json(attrs, entity="trace attributes"),
        ))

    def get(self, trace_id: str, span_id: str) -> dict | None:
        return _normalize_row(self._conn().query_one(_TRACE_SELECT_SQL, (trace_id, span_id)))

    def list_all(self) -> list[dict]:
        return _normalize_rows(self._conn().query_all(_TRACE_LIST_SQL))

    def iter_all(self, batch_size: int = 500):
        """按复合主键 keyset 分页流式读取（P9.27）。"""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last_trace = ""
        last_span = ""
        while True:
            rows = _normalize_rows(self._conn().query_all(
                _TRACE_PAGE_SQL, (last_trace, last_span, batch_size)
            ))
            if not rows:
                return
            for row in rows:
                yield row
            last_trace = rows[-1].get("trace_id") or ""
            last_span = rows[-1].get("span_id") or ""
            if len(rows) < batch_size:
                return
