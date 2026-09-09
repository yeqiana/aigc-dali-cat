from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from platform.core.enums.trace_status import TraceStatus


@dataclass(frozen=True)
class TraceContract:
    """一次可观察执行单元的 Trace/Span 事实契约。

    Trace 用于解释执行链路，不承担调度、重试、门禁或状态推进职责。
    """

    trace_id: str
    span_id: str
    operation: str
    status: TraceStatus
    started_at: datetime
    request_id: str | None = None
    episode_id: str | None = None
    task_id: str | None = None
    parent_span_id: str | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
