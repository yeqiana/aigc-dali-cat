"""MySQL Artifact Index Repository（P9.26.4 真实持久化实现）。"""

from __future__ import annotations

import json
from typing import Protocol

from platform.core.contracts.artifact_contract import ArtifactContract
from platform.repository.mysql.mysql_connection import MySqlConnection


class ArtifactRepository(Protocol):
    def save(self, artifact: ArtifactContract) -> None: ...


_ARTIFACT_UPSERT_SQL = (
    "INSERT INTO artifact_index "
    "(artifact_id, artifact_type, path, sha256, owner_type, owner_id, "
    " created_by, created_at, trace_id, task_id, metadata) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "AS new "
    "ON DUPLICATE KEY UPDATE "
    "artifact_type=new.artifact_type, path=new.path, sha256=new.sha256, "
    "owner_type=new.owner_type, owner_id=new.owner_id, "
    "created_by=new.created_by, created_at=new.created_at, "
    "trace_id=new.trace_id, task_id=new.task_id, metadata=new.metadata"
)

_ARTIFACT_SELECT_SQL = "SELECT * FROM artifact_index WHERE artifact_id = %s"
_ARTIFACT_LIST_SQL = "SELECT * FROM artifact_index ORDER BY created_at"
_ARTIFACT_PAGE_SQL = (
    "SELECT * FROM artifact_index WHERE artifact_id > %s ORDER BY artifact_id LIMIT %s"
)


class MySqlArtifactRepository:
    """Artifact 索引的 MySQL 持久化。

    以 artifact_id 为主键幂等写入。
    """

    def __init__(self, connection: MySqlConnection | None = None):
        self.connection = connection

    def _conn(self) -> MySqlConnection:
        if self.connection is None:
            raise RuntimeError("MySqlArtifactRepository requires a MySqlConnection")
        return self.connection

    def save(self, artifact: ArtifactContract) -> None:
        self._conn().execute(_ARTIFACT_UPSERT_SQL, (
            artifact.artifact_id,
            artifact.artifact_type.value,
            artifact.path,
            artifact.sha256,
            artifact.owner_type.value,
            artifact.owner_id,
            artifact.created_by,
            artifact.created_at,
            artifact.trace_id,
            artifact.task_id,
            json.dumps(artifact.metadata, ensure_ascii=False),
        ))

    def get(self, artifact_id: str) -> dict | None:
        return self._conn().query_one(_ARTIFACT_SELECT_SQL, (artifact_id,))

    def list_all(self) -> list[dict]:
        return self._conn().query_all(_ARTIFACT_LIST_SQL)

    def iter_all(self, batch_size: int = 500):
        """按主键 keyset 分页流式读取（P9.27）。"""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last = ""
        while True:
            rows = self._conn().query_all(_ARTIFACT_PAGE_SQL, (last, batch_size))
            if not rows:
                return
            for row in rows:
                yield row
            last = rows[-1]["artifact_id"]
            if len(rows) < batch_size:
                return
