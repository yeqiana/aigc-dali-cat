from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType


@dataclass(frozen=True)
class EventContract:
    """平台事件事实契约。

    Event 只表达“发生了什么”，不能据此绕过 canonical episode-state
    或其他既有门禁直接推进 Story OS 状态。
    """

    event_id: str
    event_type: EventType
    aggregate_type: EntityType
    aggregate_id: str
    occurred_at: datetime
    trace_id: str | None = None
    task_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
