from typing import Any
from uuid import uuid4

from platform.core.clock import utc_now
from platform.core.contracts.artifact_contract import ArtifactContract
from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType
from platform.repository.artifact_repository import ArtifactRepository


class ArtifactObserver:
    """Artifact索引观察器。

    只登记资产事实，不复制、移动或删除文件。
    P9.27 起 register() 会把登记结果交给注入的 repository。
    """

    def __init__(self, repository: ArtifactRepository | None = None):
        self.repository = repository

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
        artifact = ArtifactContract(
            artifact_id=f"artifact_{uuid4().hex}",
            artifact_type=artifact_type,
            path=path,
            sha256=sha256,
            owner_type=owner_type,
            owner_id=owner_id,
            created_by=created_by,
            created_at=utc_now(),
            trace_id=trace_id,
            task_id=task_id,
            metadata=metadata or {},
        )
        self.save(artifact)
        return artifact

    def save(self, artifact: ArtifactContract) -> None:
        """持久化已经构造好的资产契约；没有 repository 时只观察。"""
        if self.repository:
            self.repository.save(artifact)
