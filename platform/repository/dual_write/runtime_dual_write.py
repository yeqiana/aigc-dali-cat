"""P9.26.5 Runtime Data Dual Write。

Legacy(JSONL) 与 MySQL 双写包装：
    主链路仍先写 Legacy，MySQL 作为副写（幂等 upsert）。
    可用 secondary_enabled 关闭 MySQL 写入，作为回滚开关。
    不改变既有 Legacy 写入语义。
"""

from __future__ import annotations

from typing import Any

from platform.artifact.jsonl_artifact_store import JsonlArtifactStore
from platform.event.jsonl_event_store import JsonlEventStore
from platform.trace.jsonl_trace_store import JsonlTraceStore


class _RuntimeDualWriteBase:
    def __init__(self, legacy, mysql_repository=None, secondary_enabled: bool = True):
        self.legacy = legacy
        self.mysql_repository = mysql_repository
        self.secondary_enabled = secondary_enabled

    def save(self, entity) -> dict[str, Any]:
        self.legacy.append(entity)
        if not self.secondary_enabled or self.mysql_repository is None:
            return {"legacy": "OK", "mysql": "SKIPPED"}
        self.mysql_repository.save(entity)
        return {"legacy": "OK", "mysql": "OK"}


class DualWriteEventRepository(_RuntimeDualWriteBase):
    """Event 双写：Legacy JSONL + MySQL。"""

    def __init__(self, jsonl_store=None, mysql_repository=None, secondary_enabled: bool = True):
        super().__init__(jsonl_store or JsonlEventStore(), mysql_repository, secondary_enabled)


class DualWriteTraceRepository(_RuntimeDualWriteBase):
    """Trace 双写：Legacy JSONL + MySQL。"""

    def __init__(self, jsonl_store=None, mysql_repository=None, secondary_enabled: bool = True):
        super().__init__(jsonl_store or JsonlTraceStore(), mysql_repository, secondary_enabled)


class DualWriteArtifactRepository(_RuntimeDualWriteBase):
    """Artifact 双写：Legacy JSONL + MySQL。"""

    def __init__(self, jsonl_store=None, mysql_repository=None, secondary_enabled: bool = True):
        super().__init__(jsonl_store or JsonlArtifactStore(), mysql_repository, secondary_enabled)
