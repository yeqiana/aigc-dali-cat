"""MySQL Event Repository（P9.26.4 真实持久化实现）。"""

from __future__ import annotations

import json
from platform.repository.mysql.payload_policy import bounded_json
from typing import Protocol

from platform.core.contracts.event_contract import EventContract
from platform.repository.mysql.mysql_connection import MySqlConnection


class EventRepository(Protocol):
    def save(self, event: EventContract) -> None: ...


_EVENT_UPSERT_SQL = (
    "INSERT INTO TB_EVENT_LOG "
    "(EVENT_ID, EVENT_TYPE, AGGREGATE_TYPE, AGGREGATE_ID, EPISODE_ID, OCCURRED_TIME, "
    " TRACE_ID, TASK_ID, PAYLOAD, METADATA) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "AS new "
    "ON DUPLICATE KEY UPDATE "
    "EVENT_TYPE=new.EVENT_TYPE, AGGREGATE_TYPE=new.AGGREGATE_TYPE, "
    "AGGREGATE_ID=new.AGGREGATE_ID, EPISODE_ID=new.EPISODE_ID, "
    "OCCURRED_TIME=new.OCCURRED_TIME, TRACE_ID=new.TRACE_ID, TASK_ID=new.TASK_ID, "
    "PAYLOAD=new.PAYLOAD, METADATA=new.METADATA"
)

_EVENT_SELECT_SQL = "SELECT * FROM TB_EVENT_LOG WHERE EVENT_ID = %s"
_EVENT_LIST_SQL = "SELECT * FROM TB_EVENT_LOG ORDER BY OCCURRED_TIME"
_EVENT_PAGE_SQL = "SELECT * FROM TB_EVENT_LOG WHERE EVENT_ID > %s ORDER BY EVENT_ID LIMIT %s"
_EVENT_RECENT_SQL = (
    "SELECT * FROM TB_EVENT_LOG "
    "ORDER BY OCCURRED_TIME DESC, EVENT_ID DESC LIMIT %s OFFSET %s"
)
_EVENT_AGGREGATE_SQL = (
    "SELECT * FROM TB_EVENT_LOG "
    "WHERE EVENT_TYPE=%s AND AGGREGATE_TYPE=%s AND AGGREGATE_ID=%s "
    "ORDER BY OCCURRED_TIME, EVENT_ID"
)


def _normalize_row(row: dict | None) -> dict | None:
    """将 MySQL 驱动返回的列名统一为仓库约定的小写。"""
    if row is None:
        return None
    return {str(key).lower(): value for key, value in row.items()}


def _normalize_rows(rows: list[dict]) -> list[dict]:
    return [_normalize_row(row) or {} for row in rows]


class MySqlEventRepository:
    """Event 事实的 MySQL 持久化。

    以 event_id 为主键幂等写入（ON DUPLICATE KEY UPDATE）。
    """

    def __init__(self, connection: MySqlConnection | None = None):
        self.connection = connection

    def _conn(self) -> MySqlConnection:
        if self.connection is None:
            raise RuntimeError("MySqlEventRepository requires a MySqlConnection")
        return self.connection

    def save(self, event: EventContract) -> None:
        episode_id = (
            event.aggregate_id
            if event.aggregate_type.value == "EPISODE"
            else None
        )
        self._conn().execute(_EVENT_UPSERT_SQL, (
            event.event_id,
            event.event_type.value,
            event.aggregate_type.value,
            event.aggregate_id,
            episode_id,
            event.occurred_at,
            event.trace_id,
            event.task_id,
            bounded_json(event.payload, entity="event payload"),
            bounded_json(event.metadata, entity="event metadata"),
        ))

    def get(self, event_id: str) -> dict | None:
        return _normalize_row(self._conn().query_one(_EVENT_SELECT_SQL, (event_id,)))

    def list_all(self) -> list[dict]:
        return _normalize_rows(self._conn().query_all(_EVENT_LIST_SQL))

    def list_recent(self, *, limit: int = 50, offset: int = 0) -> list[dict]:
        return _normalize_rows(
            self._conn().query_all(_EVENT_RECENT_SQL, (int(limit), int(offset)))
        )

    def list_by_aggregate(
        self, event_type: str, aggregate_type: str, aggregate_id: str
    ) -> list[dict]:
        return _normalize_rows(self._conn().query_all(
            _EVENT_AGGREGATE_SQL,
            (str(event_type), str(aggregate_type), str(aggregate_id)),
        ))

    def iter_all(self, batch_size: int = 500):
        """按主键 keyset 分页流式读取（P9.27），避免一次性载入全表。"""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last = ""
        while True:
            rows = _normalize_rows(self._conn().query_all(_EVENT_PAGE_SQL, (last, batch_size)))
            if not rows:
                return
            for row in rows:
                yield row
            last = rows[-1].get("event_id") or ""
            if len(rows) < batch_size:
                return
