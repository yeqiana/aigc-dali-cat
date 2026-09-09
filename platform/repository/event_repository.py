from typing import Protocol

from platform.core.contracts.event_contract import EventContract
from platform.event.jsonl_event_store import JsonlEventStore


class EventRepository(Protocol):
    """Event持久化抽象。

    Phase 1 使用Repository隔离存储实现。
    后续可替换为MySQL实现。
    """

    def save(self, event: EventContract) -> None:
        ...


class DualWriteEventRepository:
    """Phase 1 Event双写Repository。

    当前：
    Event -> JSONL

    未来：
    Event -> MySQL + JSONL backup

    不负责状态计算。
    """

    def __init__(self, jsonl_store: JsonlEventStore | None = None):
        self.jsonl_store = jsonl_store or JsonlEventStore()

    def save(self, event: EventContract) -> None:
        self.jsonl_store.append(event)
