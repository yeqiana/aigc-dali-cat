from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskContract:
    """任务执行事实契约。

    Phase 0 只用于描述任务，不负责调度。
    """

    task_id: str
    episode_id: str
    task_type: str
    status: str
    created_at: datetime
