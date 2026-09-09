from datetime import datetime

from platform.core.contracts.artifact_contract import ArtifactContract
from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType
from platform.repository.artifact.mysql_artifact_repository import MySqlArtifactRepository


class FakeConnection:
    def __init__(self):
        self.saved = []

    def insert_artifact(self, artifact):
        self.saved.append(artifact)


def test_mysql_artifact_repository_save():
    connection = FakeConnection()
    repository = MySqlArtifactRepository(connection)

    artifact = ArtifactContract(
        artifact_id="artifact_001",
        artifact_type=ArtifactType.IMAGE,
        path="episodes/ep002/frame01.png",
        sha256="sha256",
        owner_type=EntityType.EPISODE,
        owner_id="ep002",
        created_by="runtime",
        created_at=datetime.utcnow(),
    )

    repository.save(artifact)

    assert connection.saved[0].artifact_id == "artifact_001"
