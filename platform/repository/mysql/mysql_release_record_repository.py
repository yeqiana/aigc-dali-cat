from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    bounded_json,
    release_projection,
)


_UPSERT_SQL = """
INSERT INTO TB_RELEASE_RECORD (
    RELEASE_ID, EPISODE_ID, RELEASE_TYPE, STATUS, SNAPSHOT_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    STATUS=VALUES(STATUS),
    SNAPSHOT_SHA256=VALUES(SNAPSHOT_SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_ID_SQL = """
SELECT RELEASE_ID, EPISODE_ID, RELEASE_TYPE, STATUS, SNAPSHOT_SHA256, PAYLOAD, CREATE_TIME
FROM TB_RELEASE_RECORD
WHERE RELEASE_ID=%s
LIMIT 1
""".strip()

_LIST_SQL = """
SELECT RELEASE_ID, EPISODE_ID, RELEASE_TYPE, STATUS, SNAPSHOT_SHA256, PAYLOAD, CREATE_TIME
FROM TB_RELEASE_RECORD
WHERE EPISODE_ID=%s
ORDER BY RELEASE_TYPE, CREATE_TIME
""".strip()


def release_record_id(episode_id: str, release_type: str) -> str:
    raw = f"{episode_id}|{release_type}".encode("utf-8")
    return "RR_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlReleaseRecordRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "release_type", "status", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("release record missing required fields: " + ", ".join(missing))
        episode_id = str(row["episode_id"])
        release_type = str(row["release_type"])
        rid = str(row.get("release_id") or release_record_id(episode_id, release_type))
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = release_projection(payload_value, row["payload_ref"])
        payload = bounded_json(payload_value, entity="release record")
        self.connection.execute(
            _UPSERT_SQL,
            (rid, episode_id, release_type, str(row["status"]), row.get("snapshot_sha256"), payload),
        )
        return {"release_id": rid, "episode_id": episode_id, "release_type": release_type}

    def get_current(self, episode_id: str, release_type: str) -> dict | None:
        return self.get_by_id(release_record_id(str(episode_id), str(release_type)))

    def get_by_id(self, release_id: str) -> dict | None:
        return self._decode(self.connection.query_one(_BY_ID_SQL, (str(release_id),)))

    def list_episode(self, episode_id: str) -> list[dict]:
        rows = self.connection.query_all(_LIST_SQL, (str(episode_id),)) or []
        return [decoded for row in rows if (decoded := self._decode(row)) is not None]

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if not row:
            return None
        payload = row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            return None
        return {
            "release_id": row.get("RELEASE_ID") or row.get("release_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "release_type": row.get("RELEASE_TYPE") or row.get("release_type"),
            "status": row.get("STATUS") or row.get("status"),
            "snapshot_sha256": row.get("SNAPSHOT_SHA256") or row.get("snapshot_sha256"),
            "payload": payload,
        }
