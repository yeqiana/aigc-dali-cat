from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType


@dataclass(frozen=True)
class ArtifactContract:
    """生产资产索引事实契约。

    Artifact Contract 只建立索引和归属关系，不移动、复制或删除真实文件。
    """

    artifact_id: str
    artifact_type: ArtifactType
    path: str
    sha256: str
    owner_type: EntityType
    owner_id: str
    created_by: str
    created_at: datetime
    trace_id: str | None = None
    task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
