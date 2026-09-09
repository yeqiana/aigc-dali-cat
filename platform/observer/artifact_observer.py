from datetime import datetime
from uuid import uuid4
from typing import Any

from platform.core.contracts.artifact_contract import ArtifactContract
from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType


class ArtifactObserver:
    """Artifact索引观察器。

    只登记资产事实，不复制、移动或删除文件。
    """

    def register(
        self,
        artifact_type: ArtifactType,
        path: str,
        sha256: str,
        owner_type: EntityType,
        owner_id: str,
        created_by: str,
        trace_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactContract:
        return ArtifactContract(
            artifact_id=f"artifact_{uuid4().hex}",
            artifact_type=artifact_type,
            path=path,
            sha256=sha256,
            owner_type=owner_type,
            owner_id=owner_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            trace_id=trace_id,
            task_id=task_id,
            metadata=metadata or {},
        )
