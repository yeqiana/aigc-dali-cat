from datetime import datetime

from platform.core.contracts.artifact_contract import ArtifactContract
from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType
from platform.repository.artifact.mysql_artifact_repository import MySqlArtifactRepository


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.queried = []
        self.one = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        self.queried.append((sql, params))
        return self.one

    def query_all(self, sql, params=None):
        return []


def _artifact():
    return ArtifactContract(
        artifact_id="artifact_001",
        artifact_type=ArtifactType.IMAGE,
        path="episodes/ep002/frame01.png",
        sha256="a" * 64,
        owner_type=EntityType.EPISODE,
        owner_id="ep002",
        created_by="runtime",
        created_at=datetime.utcnow(),
        metadata={"w": 1088, "h": 1360},
    )


def test_mysql_artifact_repository_save():
    connection = FakeConnection()
    repository = MySqlArtifactRepository(connection)

    repository.save(_artifact())

    assert len(connection.executed) == 1
    sql, params = connection.executed[0]
    assert "INSERT INTO artifact_index" in sql
    assert params[0] == "artifact_001"
    assert params[1] == "IMAGE"
    assert params[3] == "a" * 64


def test_mysql_artifact_repository_get():
    connection = FakeConnection()
    connection.one = {"artifact_id": "artifact_001"}
    repository = MySqlArtifactRepository(connection)

    row = repository.get("artifact_001")

    assert row is not None
    assert row["artifact_id"] == "artifact_001"
    assert connection.queried[-1][1] == ("artifact_001",)
