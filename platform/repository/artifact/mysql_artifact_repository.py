from typing import Protocol

from platform.core.contracts.artifact_contract import ArtifactContract


class ArtifactRepository(Protocol):
    """Artifact持久化抽象。

    只负责资产索引保存，不负责文件移动、复制和删除。
    """

    def save(self, artifact: ArtifactContract) -> None:
        ...


class MySqlArtifactRepository:
    """MySQL Artifact Index Repository。

    Phase 1阶段只定义数据库边界，暂不绑定具体ORM。
    后续对应 artifact_index 表。
    """

    def __init__(self, connection=None):
        self.connection = connection

    def save(self, artifact: ArtifactContract) -> None:
        if self.connection is None:
            raise RuntimeError("mysql connection is required")

        self.connection.insert_artifact(artifact)
