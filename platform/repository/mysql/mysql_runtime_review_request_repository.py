from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    bounded_json,
    runtime_review_projection,
)


_UPSERT_SQL = """
INSERT INTO TB_RUNTIME_REVIEW_REQUEST (
    RUNTIME_REVIEW_RECORD_ID, EPISODE_ID, REVIEW_KIND, RECORD_KEY, ATTEMPT_NO,
    REQUEST_ID, REQUEST_FINGERPRINT, STATUS, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    ATTEMPT_NO=VALUES(ATTEMPT_NO),
    REQUEST_ID=VALUES(REQUEST_ID),
    REQUEST_FINGERPRINT=VALUES(REQUEST_FINGERPRINT),
    STATUS=VALUES(STATUS),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_GET_SQL = """
SELECT RUNTIME_REVIEW_RECORD_ID, EPISODE_ID, REVIEW_KIND, RECORD_KEY, ATTEMPT_NO,
       REQUEST_ID, REQUEST_FINGERPRINT, STATUS, PAYLOAD, CREATE_TIME, UPDATE_TIME
FROM TB_RUNTIME_REVIEW_REQUEST
WHERE EPISODE_ID=%s AND REVIEW_KIND=%s AND RECORD_KEY=%s
LIMIT 1
""".strip()

_BY_ID_SQL = """
SELECT RUNTIME_REVIEW_RECORD_ID, EPISODE_ID, REVIEW_KIND, RECORD_KEY, ATTEMPT_NO,
       REQUEST_ID, REQUEST_FINGERPRINT, STATUS, PAYLOAD, CREATE_TIME, UPDATE_TIME
FROM TB_RUNTIME_REVIEW_REQUEST
WHERE RUNTIME_REVIEW_RECORD_ID=%s
LIMIT 1
""".strip()

_CURRENT_SQL = """
SELECT RUNTIME_REVIEW_RECORD_ID, EPISODE_ID, REVIEW_KIND, RECORD_KEY, ATTEMPT_NO,
       REQUEST_ID, REQUEST_FINGERPRINT, STATUS, PAYLOAD, CREATE_TIME, UPDATE_TIME
FROM TB_RUNTIME_REVIEW_REQUEST
WHERE EPISODE_ID=%s AND RECORD_KEY='CURRENT'
ORDER BY REVIEW_KIND
""".strip()

_ATTEMPTS_SQL = """
SELECT RUNTIME_REVIEW_RECORD_ID, EPISODE_ID, REVIEW_KIND, RECORD_KEY, ATTEMPT_NO,
       REQUEST_ID, REQUEST_FINGERPRINT, STATUS, PAYLOAD, CREATE_TIME, UPDATE_TIME
FROM TB_RUNTIME_REVIEW_REQUEST
WHERE EPISODE_ID=%s AND REVIEW_KIND=%s AND RECORD_KEY LIKE 'ATTEMPT:%%'
ORDER BY ATTEMPT_NO, RUNTIME_REVIEW_RECORD_ID
""".strip()


def runtime_review_record_id(episode_id: str, review_kind: str, record_key: str) -> str:
    raw = f"{episode_id}|{review_kind}|{record_key}".encode("utf-8")
    return "RR_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlRuntimeReviewRequestRepository:
    """Durable CURRENT head plus immutable ATTEMPT snapshots for product review requests."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = (
            "episode_id", "review_kind", "record_key", "attempt_no",
            "request_id", "status", "payload",
        )
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("runtime review request missing required fields: " + ", ".join(missing))
        episode_id = str(row["episode_id"])
        review_kind = str(row["review_kind"])
        record_key = str(row["record_key"])
        attempt_no = int(row["attempt_no"])
        if attempt_no < 1:
            raise ValueError("runtime review attempt_no must be >= 1")
        record_id = str(row.get("runtime_review_record_id") or runtime_review_record_id(
            episode_id, review_kind, record_key
        ))
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = runtime_review_projection(payload_value, row["payload_ref"])
        payload = bounded_json(payload_value, entity="runtime review request")
        self.connection.execute(
            _UPSERT_SQL,
            (
                record_id, episode_id, review_kind, record_key, attempt_no,
                str(row["request_id"]), row.get("request_fingerprint"),
                str(row["status"]), payload,
            ),
        )
        return {
            "runtime_review_record_id": record_id,
            "episode_id": episode_id,
            "review_kind": review_kind,
            "record_key": record_key,
            "attempt_no": attempt_no,
        }

    def get(self, episode_id: str, review_kind: str, record_key: str) -> dict | None:
        return self._decode(self.connection.query_one(
            _GET_SQL, (str(episode_id), str(review_kind), str(record_key))
        ))

    def get_by_id(self, runtime_review_record_id_value: str) -> dict | None:
        return self._decode(self.connection.query_one(
            _BY_ID_SQL, (str(runtime_review_record_id_value),)
        ))

    def list_current(self, episode_id: str) -> list[dict]:
        return [
            decoded for row in self.connection.query_all(_CURRENT_SQL, (str(episode_id),))
            if (decoded := self._decode(row)) is not None
        ]

    def list_attempts(self, episode_id: str, review_kind: str) -> list[dict]:
        return [
            decoded for row in self.connection.query_all(
                _ATTEMPTS_SQL, (str(episode_id), str(review_kind))
            ) if (decoded := self._decode(row)) is not None
        ]

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
            "runtime_review_record_id": row.get("RUNTIME_REVIEW_RECORD_ID") or row.get("runtime_review_record_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "review_kind": row.get("REVIEW_KIND") or row.get("review_kind"),
            "record_key": row.get("RECORD_KEY") or row.get("record_key"),
            "attempt_no": row.get("ATTEMPT_NO") or row.get("attempt_no"),
            "request_id": row.get("REQUEST_ID") or row.get("request_id"),
            "request_fingerprint": row.get("REQUEST_FINGERPRINT") or row.get("request_fingerprint"),
            "status": row.get("STATUS") or row.get("status"),
            "payload": payload,
        }
