from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubmitTaskRequest:
    """Control Plane -> Runtime 的任务提交请求。

    Phase 0 只定义边界，不真正调度任务。
    """

    task_type: str
    episode_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class TaskQueryResult:
    """任务查询结果。

    未来可由 Runtime Adapter 映射到 Control Plane DTO。
    """

    task_id: str
    status: str
    metadata: dict[str, Any]
