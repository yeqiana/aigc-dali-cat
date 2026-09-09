from datetime import datetime
from uuid import uuid4
from typing import Any

from platform.core.contracts.trace_contract import TraceContract
from platform.core.enums.trace_status import TraceStatus


class TraceObserver:
    """Runtime Trace观察器。

    记录执行事实，不参与重试、调度和流程决策。
    """

    def start(
        self,
        operation: str,
        request_id: str | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> TraceContract:
        now = datetime.utcnow()
        return TraceContract(
            trace_id=f"trace_{uuid4().hex}",
            span_id=f"span_{uuid4().hex}",
            operation=operation,
            status=TraceStatus.RUNNING,
            started_at=now,
            request_id=request_id,
            episode_id=episode_id,
            task_id=task_id,
            inputs=inputs or {},
        )
