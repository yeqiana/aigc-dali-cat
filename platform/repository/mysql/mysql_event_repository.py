"""MySQL Event Repository（P9.26.4 真实持久化实现）。"""

from __future__ import annotations

import json
from typing import Protocol

from platform.core.contracts.event_contract import EventContract
from platform.repository.mysql.mysql_connection import MySqlConnection


class EventRepository(Protocol):
    def save(self, event: EventContract) -> None: ...


_EVENT_UPSERT_SQL = (
    "INSERT INTO event_log "
    "(event_id, event_type, aggregate_type, aggregate_id, occurred_at, "
    " trace_id, task_id, payload, metadata) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "AS new "
    "ON DUPLICATE KEY UPDATE "
    "event_type=new.event_type, aggregate_type=new.aggregate_type, "
    "aggregate_id=new.aggregate_id, occurred_at=new.occurred_at, "
    "trace_id=new.trace_id, task_id=new.task_id, "
    "payload=new.payload, metadata=new.metadata"
)

_EVENT_SELECT_SQL = "SELECT * FROM event_log WHERE event_id = %s"
_EVENT_LIST_SQL = "SELECT * FROM event_log ORDER BY occurred_at"
_EVENT_PAGE_SQL = "SELECT * FROM event_log WHERE event_id > %s ORDER BY event_id LIMIT %s"


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
        self._conn().execute(_EVENT_UPSERT_SQL, (
            event.event_id,
            event.event_type.value,
            event.aggregate_type.value,
            event.aggregate_id,
            event.occurred_at,
            event.trace_id,
            event.task_id,
            json.dumps(event.payload, ensure_ascii=False),
            json.dumps(event.metadata, ensure_ascii=False),
        ))

    def get(self, event_id: str) -> dict | None:
        return self._conn().query_one(_EVENT_SELECT_SQL, (event_id,))

    def list_all(self) -> list[dict]:
        return self._conn().query_all(_EVENT_LIST_SQL)

    def iter_all(self, batch_size: int = 500):
        """按主键 keyset 分页流式读取（P9.27），避免一次性载入全表。"""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last = ""
        while True:
            rows = self._conn().query_all(_EVENT_PAGE_SQL, (last, batch_size))
            if not rows:
                return
            for row in rows:
                yield row
            last = rows[-1]["event_id"]
            if len(rows) < batch_size:
                return
