"""锁住 MySQL UPSERT 的 row-alias 写法（P9.27）。

MySQL 8.0.20 起 `ON DUPLICATE KEY UPDATE col = VALUES(col)` 被标记为弃用，真实实例
（8.0.46）执行旧写法会返回告警 1287。这里把三个仓储的 UPSERT 语句锁在 row-alias
写法上，避免以后改回弃用语法。
"""

from __future__ import annotations

from platform.repository.artifact.mysql_artifact_repository import (
    _ARTIFACT_UPSERT_SQL,
)
from platform.repository.mysql.mysql_event_repository import _EVENT_UPSERT_SQL
from platform.repository.trace.mysql_trace_repository import _TRACE_UPSERT_SQL

UPSERTS = {
    "event_log": _EVENT_UPSERT_SQL,
    "trace_span": _TRACE_UPSERT_SQL,
    "artifact_index": _ARTIFACT_UPSERT_SQL,
}


def test_upserts_use_row_alias_not_deprecated_values_function():
    for table, sql in UPSERTS.items():
        assert "AS new" in sql, table
        assert "VALUES(" not in sql, table
        assert "=new." in sql.replace(" ", ""), table


def test_upserts_still_target_the_right_table_and_key():
    assert "INSERT INTO event_log" in _EVENT_UPSERT_SQL
    assert "INSERT INTO trace_span" in _TRACE_UPSERT_SQL
    assert "INSERT INTO artifact_index" in _ARTIFACT_UPSERT_SQL
    for table, sql in UPSERTS.items():
        assert "ON DUPLICATE KEY UPDATE" in sql, table
