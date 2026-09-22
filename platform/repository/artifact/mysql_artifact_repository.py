"""MySQL Artifact Index Repository（P9.26.4 真实持久化实现）。"""

from __future__ import annotations

import hashlib
import json
from typing import Protocol

from platform.core.contracts.artifact_contract import ArtifactContract
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.payload_policy import canonical_json_bytes


class ArtifactRepository(Protocol):
    def save(self, artifact: ArtifactContract) -> None: ...


_ARTIFACT_UPSERT_SQL = (
    "INSERT INTO TB_ARTIFACT_INDEX "
    "(ARTIFACT_ID, EPISODE_ID, ARTIFACT_TYPE, URI, SHA256, MIME_TYPE, BYTE_SIZE, "
    " WIDTH_PX, HEIGHT_PX, OWNER_TYPE, OWNER_ID, CREATED_BY, TRACE_ID, TASK_ID, "
    " METADATA_BLOB, METADATA_SHA256, STATUS, CREATE_TIME) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "AS new "
    "ON DUPLICATE KEY UPDATE "
    "EPISODE_ID=new.EPISODE_ID, ARTIFACT_TYPE=new.ARTIFACT_TYPE, URI=new.URI, "
    "SHA256=new.SHA256, MIME_TYPE=new.MIME_TYPE, BYTE_SIZE=new.BYTE_SIZE, "
    "WIDTH_PX=new.WIDTH_PX, HEIGHT_PX=new.HEIGHT_PX, OWNER_TYPE=new.OWNER_TYPE, "
    "OWNER_ID=new.OWNER_ID, CREATED_BY=new.CREATED_BY, TRACE_ID=new.TRACE_ID, "
    "TASK_ID=new.TASK_ID, METADATA_BLOB=new.METADATA_BLOB, "
    "METADATA_SHA256=new.METADATA_SHA256, STATUS=new.STATUS, CREATE_TIME=new.CREATE_TIME"
)

_ARTIFACT_SELECT_SQL = "SELECT * FROM TB_ARTIFACT_INDEX WHERE ARTIFACT_ID = %s"
_ARTIFACT_LIST_SQL = "SELECT * FROM TB_ARTIFACT_INDEX ORDER BY CREATE_TIME"
_ARTIFACT_PAGE_SQL = (
    "SELECT * FROM TB_ARTIFACT_INDEX WHERE ARTIFACT_ID > %s ORDER BY ARTIFACT_ID LIMIT %s"
)


def _normalize_row(row: dict | None) -> dict | None:
    """将 MySQL 驱动返回的列名统一为仓库约定的小写。"""
    if row is None:
        return None
    return {str(key).lower(): value for key, value in row.items()}


def _normalize_rows(rows: list[dict]) -> list[dict]:
    return [_normalize_row(row) or {} for row in rows]


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
        metadata = dict(artifact.metadata or {})
        metadata_bytes = canonical_json_bytes(metadata)
        metadata_sha = hashlib.sha256(metadata_bytes).hexdigest()
        episode_id = artifact.owner_id if artifact.owner_type.value == "EPISODE" else metadata.get("episode_id")
        mime_type = metadata.get("mime_type")
        byte_size = metadata.get("byte_size") or metadata.get("bytes")
        width = metadata.get("width_px") or metadata.get("width") or metadata.get("w")
        height = metadata.get("height_px") or metadata.get("height") or metadata.get("h")
        self._conn().execute(_ARTIFACT_UPSERT_SQL, (
            artifact.artifact_id,
            episode_id,
            artifact.artifact_type.value,
            artifact.path,
            artifact.sha256,
            mime_type,
            byte_size,
            width,
            height,
            artifact.owner_type.value,
            artifact.owner_id,
            artifact.created_by,
            artifact.trace_id,
            artifact.task_id,
            metadata_bytes,
            metadata_sha,
            "ACTIVE",
            artifact.created_at,
        ))

    def get(self, artifact_id: str) -> dict | None:
        return _normalize_row(self._conn().query_one(_ARTIFACT_SELECT_SQL, (artifact_id,)))

    def list_all(self) -> list[dict]:
        return _normalize_rows(self._conn().query_all(_ARTIFACT_LIST_SQL))

    def iter_all(self, batch_size: int = 500):
        """按主键 keyset 分页流式读取（P9.27）。"""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        last = ""
        while True:
            rows = _normalize_rows(self._conn().query_all(_ARTIFACT_PAGE_SQL, (last, batch_size)))
            if not rows:
                return
            for row in rows:
                yield row
            last = rows[-1].get("artifact_id") or ""
            if len(rows) < batch_size:
                return
