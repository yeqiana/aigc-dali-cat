from dataclasses import asdict
from typing import Protocol

from platform.core.contracts.event_contract import EventContract


class EventRepository(Protocol):
    """Event repository interface.

    上层只依赖契约，不关心 JSONL/MySQL 实现。
    """

    def save(self, event: EventContract) -> None:
        ...


class MySqlEventRepository:
    """MySQL Event Repository 占位实现。

    Phase 1-P1.2.1 先建立持久化边界。
    实际数据库连接由后续 Spring Boot/Data Layer 接入。
    """

    def __init__(self, connection=None):
        self.connection = connection

    def save(self, event: EventContract) -> None:
        if self.connection is None:
            raise RuntimeError(
                "MySqlEventRepository requires database connection"
            )

        # 后续实现 INSERT INTO event_log
        # 当前不执行真实SQL，避免引入数据库依赖。
        record = asdict(event)
        self.connection.insert_event(record)
