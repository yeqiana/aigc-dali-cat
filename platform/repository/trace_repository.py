"""Trace 持久化抽象（与 event_repository.py 对称）。"""

from typing import Protocol

from platform.core.contracts.trace_contract import TraceContract

__all__ = ["TraceRepository"]


class TraceRepository(Protocol):
    """Trace/Span 事实持久化抽象。

    只要求 save(trace)，可由 JSONL / MySQL / DualWrite 任意实现承担。
    """

    def save(self, trace: TraceContract) -> None:
        ...

