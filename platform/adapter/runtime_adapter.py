from typing import Any

from platform.adapter.contracts import SubmitTaskRequest, TaskQueryResult
from platform.observer.event_observer import EventObserver
from platform.observer.trace_observer import TraceObserver
from platform.observer.artifact_observer import ArtifactObserver


class RuntimeAdapter:
    """连接未来 Control Plane 与现有 Runtime 的隔离层。

    当前版本只提供接口，不替换现有 Runtime。
    P9.27：可注入 RuntimeRepositories 显式接线写入链路；
    不注入时 observer 仍是空的，行为与之前完全一致。
    """

    def __init__(
        self,
        event_observer: EventObserver | None = None,
        trace_observer: TraceObserver | None = None,
        artifact_observer: ArtifactObserver | None = None,
        repositories: Any = None,
    ):
        self.repositories = repositories
        self.provider = None
        if repositories is not None:
            observers = repositories.observers()
            event_observer = event_observer or observers.event
            trace_observer = trace_observer or observers.trace
            artifact_observer = artifact_observer or observers.artifact
        self.event_observer = event_observer
        self.trace_observer = trace_observer
        self.artifact_observer = artifact_observer

    @classmethod
    def from_env(cls, **kwargs) -> "RuntimeAdapter":
        """按 STORYOS_RUNTIME_STORE_MODE 从环境装配（默认 jsonl）。"""
        from platform.repository.runtime_repository_provider import (
            build_runtime_repository_provider,
        )

        provider = build_runtime_repository_provider(**kwargs)
        adapter = cls(repositories=provider.repositories())
        adapter.provider = provider
        return adapter

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
        """持久化已经构造好的 EventContract（P9.27 修正原先的错误调用）。"""
        if self.event_observer:
            self.event_observer.save(event)

    def record_trace(self, trace: Any) -> None:
        """持久化已经构造好的 TraceContract。"""
        if self.trace_observer:
            self.trace_observer.save(trace)

    def register_artifact(self, artifact: Any) -> None:
        """持久化已经构造好的 ArtifactContract。"""
        if self.artifact_observer:
            self.artifact_observer.save(artifact)

    def close(self) -> None:
        """释放 from_env() 自建的连接；注入的观察器/仓库不受影响。"""
        if self.provider is not None:
            self.provider.close()
            self.provider = None
