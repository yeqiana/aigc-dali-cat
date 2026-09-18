from __future__ import annotations

import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    bounded_json,
    runtime_request_projection,
)


_UPSERT_SQL = """
INSERT INTO TB_RUNTIME_REQUEST (
    RUNTIME_REQUEST_ID, EPISODE_ID, REQUEST_TYPE, STATUS, FINGERPRINT, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    REQUEST_TYPE=VALUES(REQUEST_TYPE),
    STATUS=VALUES(STATUS),
    FINGERPRINT=VALUES(FINGERPRINT),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_ID_SQL = """
SELECT RUNTIME_REQUEST_ID, EPISODE_ID, REQUEST_TYPE, STATUS, FINGERPRINT, PAYLOAD, CREATE_TIME
FROM TB_RUNTIME_REQUEST
WHERE RUNTIME_REQUEST_ID=%s
LIMIT 1
""".strip()

_LATEST_SQL = """
SELECT RUNTIME_REQUEST_ID, EPISODE_ID, REQUEST_TYPE, STATUS, FINGERPRINT, PAYLOAD, CREATE_TIME
FROM TB_RUNTIME_REQUEST
WHERE EPISODE_ID=%s
ORDER BY CREATE_TIME DESC, RUNTIME_REQUEST_ID DESC
LIMIT 1
""".strip()


class MySqlRuntimeRequestRepository:
    """Typed durable store for immutable Episode Runtime Requests."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = (
            "runtime_request_id", "episode_id", "request_type", "status", "payload",
        )
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError(
                "runtime request missing required fields: " + ", ".join(missing)
            )
        request_id = str(row["runtime_request_id"])
        episode_id = str(row["episode_id"])
        request_type = str(row["request_type"])
        status = str(row["status"])
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = runtime_request_projection(
                payload_value, row["payload_ref"]
            )
        payload = bounded_json(payload_value, entity="runtime request")
        self.connection.execute(
            _UPSERT_SQL,
            (
                request_id,
                episode_id,
                request_type,
                status,
                row.get("fingerprint"),
                payload,
            ),
        )
        return {
            "runtime_request_id": request_id,
            "episode_id": episode_id,
            "request_type": request_type,
            "status": status,
        }

    def get_by_id(self, runtime_request_id: str) -> dict | None:
        return self._decode(
            self.connection.query_one(_BY_ID_SQL, (str(runtime_request_id),))
        )

    def get_latest(self, episode_id: str) -> dict | None:
        return self._decode(
            self.connection.query_one(_LATEST_SQL, (str(episode_id),))
        )

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
            "runtime_request_id": row.get("RUNTIME_REQUEST_ID") or row.get("runtime_request_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "request_type": row.get("REQUEST_TYPE") or row.get("request_type"),
            "status": row.get("STATUS") or row.get("status"),
            "fingerprint": row.get("FINGERPRINT") or row.get("fingerprint"),
            "payload": payload,
        }
