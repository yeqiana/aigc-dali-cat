from __future__ import annotations

import datetime as dt
import json
from copy import deepcopy
from platform.repository.mysql.payload_policy import bounded_json


_UPSERT_SQL = """
INSERT INTO TB_HOST_REQUEST (
    HOST_REQUEST_ID, EPISODE_ID, REQUEST_TYPE, STATUS, WORKER_ID,
    FINGERPRINT, START_TIME, END_TIME, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    REQUEST_TYPE=VALUES(REQUEST_TYPE),
    STATUS=VALUES(STATUS),
    WORKER_ID=VALUES(WORKER_ID),
    FINGERPRINT=VALUES(FINGERPRINT),
    START_TIME=VALUES(START_TIME),
    END_TIME=VALUES(END_TIME),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_ID_SQL = """
SELECT HOST_REQUEST_ID, EPISODE_ID, REQUEST_TYPE, STATUS, WORKER_ID,
       FINGERPRINT, START_TIME, END_TIME, PAYLOAD, CREATE_TIME
FROM TB_HOST_REQUEST
WHERE HOST_REQUEST_ID=%s
LIMIT 1
""".strip()

_BY_EPISODE_SQL = """
SELECT HOST_REQUEST_ID, EPISODE_ID, REQUEST_TYPE, STATUS, WORKER_ID,
       FINGERPRINT, START_TIME, END_TIME, PAYLOAD, CREATE_TIME
FROM TB_HOST_REQUEST
WHERE EPISODE_ID=%s
ORDER BY CREATE_TIME, HOST_REQUEST_ID
""".strip()


def _parse_time(value):
    if value in (None, "") or isinstance(value, dt.datetime):
        return value or None
    try:
        return dt.datetime.fromisoformat(str(value))
    except ValueError:
        return None


class MySqlHostRequestRepository:
    """Durable lifecycle history for Host/PREIMAGE requests."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("host_request_id", "episode_id", "request_type", "status", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("host request missing required fields: " + ", ".join(missing))
        payload = bounded_json(row["payload"], entity="host request")
        self.connection.execute(
            _UPSERT_SQL,
            (
                str(row["host_request_id"]),
                str(row["episode_id"]),
                str(row["request_type"]),
                str(row["status"]),
                row.get("worker_id"),
                row.get("fingerprint"),
                _parse_time(row.get("start_time")),
                _parse_time(row.get("end_time")),
                payload,
            ),
        )
        return {
            "host_request_id": str(row["host_request_id"]),
            "episode_id": str(row["episode_id"]),
            "status": str(row["status"]),
        }

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
            "host_request_id": row.get("HOST_REQUEST_ID") or row.get("host_request_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "request_type": row.get("REQUEST_TYPE") or row.get("request_type"),
            "status": row.get("STATUS") or row.get("status"),
            "worker_id": row.get("WORKER_ID") or row.get("worker_id"),
            "fingerprint": row.get("FINGERPRINT") or row.get("fingerprint"),
            "payload": payload,
        }

    def get_by_id(self, host_request_id: str) -> dict | None:
        return self._decode(self.connection.query_one(_BY_ID_SQL, (str(host_request_id),)))

    def list_by_episode(self, episode_id: str) -> list[dict]:
        return [
            decoded
            for row in self.connection.query_all(_BY_EPISODE_SQL, (str(episode_id),))
            if (decoded := self._decode(row)) is not None
        ]
