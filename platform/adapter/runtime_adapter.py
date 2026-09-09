from typing import Any

from platform.adapter.contracts import SubmitTaskRequest, TaskQueryResult
from platform.observer.event_observer import EventObserver
from platform.observer.trace_observer import TraceObserver
from platform.observer.artifact_observer import ArtifactObserver


class RuntimeAdapter:
    """连接未来 Control Plane 与现有 Runtime 的隔离层。

    当前版本只提供接口，不替换现有 Runtime。
    """

    def __init__(
        self,
        event_observer: EventObserver | None = None,
        trace_observer: TraceObserver | None = None,
        artifact_observer: ArtifactObserver | None = None,
    ):
        self.event_observer = event_observer
        self.trace_observer = trace_observer
        self.artifact_observer = artifact_observer

    def submit_task(self, request: SubmitTaskRequest) -> str:
        """提交任务入口。

        Phase 0 不执行任务，只保留未来 Control Plane 调用边界。
        """
        return "ADAPTER_ONLY"

    def query_task(self, task_id: str) -> TaskQueryResult:
        return TaskQueryResult(
            task_id=task_id,
            status="UNKNOWN",
            metadata={"source": "runtime_adapter"},
        )

    def record_event(self, event: Any) -> None:
        if self.event_observer:
            self.event_observer.record(event)

    def record_trace(self, trace: Any) -> None:
        if self.trace_observer:
            self.trace_observer.record(trace)

    def register_artifact(self, artifact: Any) -> None:
        if self.artifact_observer:
            self.artifact_observer.register(artifact)
