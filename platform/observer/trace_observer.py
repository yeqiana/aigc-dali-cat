from typing import Any
from uuid import uuid4

from platform.core.clock import utc_now
from platform.core.contracts.trace_contract import TraceContract
from platform.core.enums.trace_status import TraceStatus
from platform.repository.trace_repository import TraceRepository


class TraceObserver:
    """Runtime Trace观察器。

    记录执行事实，不参与重试、调度和流程决策。
    P9.27：span 以 (trace_id, span_id) 为主键幂等写入，RUNNING 先落一次，
    完成态由 save()（AgentRuntime 的 trace_sink）用同一主键覆盖；
    数据库里悬停的 RUNNING 行就是“已开始但没结束”的真实信号。
    """

    def __init__(self, repository: TraceRepository | None = None):
        self.repository = repository

    def start(
        self,
        operation: str,
        request_id: str | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> TraceContract:
        trace = TraceContract(
            trace_id=f"trace_{uuid4().hex}",
            span_id=f"span_{uuid4().hex}",
            operation=operation,
            status=TraceStatus.RUNNING,
            started_at=utc_now(),
            request_id=request_id,
            episode_id=episode_id,
            task_id=task_id,
            inputs=inputs or {},
        )
        self.save(trace)
        return trace

    def save(self, trace: TraceContract) -> None:
        """持久化 trace/span 事实；没有 repository 时只观察。"""
        if self.repository:
            self.repository.save(trace)
