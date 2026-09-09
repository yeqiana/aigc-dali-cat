from dataclasses import asdict
from typing import Protocol

from platform.core.contracts.trace_contract import TraceContract


class TraceRepository(Protocol):
    """Trace存储抽象。

    不负责Trace生成、状态判断和重试策略。
    """

    def save(self, trace: TraceContract) -> None:
        ...


class MySqlTraceRepository:
    """MySQL Trace Repository占位实现。

    Phase 1仅建立存储边界。
    后续接入MySQL时实现真实insert。
    """

    def __init__(self, connection=None):
        self.connection = connection

    def save(self, trace: TraceContract) -> None:
        if self.connection is None:
            return

        self.connection.insert_trace(asdict(trace))
