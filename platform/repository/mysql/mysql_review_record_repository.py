from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from platform.repository.mysql.payload_policy import bounded_json, projection_envelope


_UPSERT_SQL = """
INSERT INTO TB_REVIEW_RECORD (
    REVIEW_ID, EPISODE_ID, REVIEW_TYPE, ATTEMPT_NO, DECISION,
    SOURCE_SHA256, REVIEWER_TYPE, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    DECISION=VALUES(DECISION),
    SOURCE_SHA256=VALUES(SOURCE_SHA256),
    REVIEWER_TYPE=VALUES(REVIEWER_TYPE),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_ID_SQL = """
SELECT REVIEW_ID, EPISODE_ID, REVIEW_TYPE, ATTEMPT_NO, DECISION,
       SOURCE_SHA256, REVIEWER_TYPE, PAYLOAD, CREATE_TIME
FROM TB_REVIEW_RECORD
WHERE REVIEW_ID=%s
LIMIT 1
""".strip()

_LATEST_SQL = """
SELECT REVIEW_ID, EPISODE_ID, REVIEW_TYPE, ATTEMPT_NO, DECISION,
       SOURCE_SHA256, REVIEWER_TYPE, PAYLOAD, CREATE_TIME
FROM TB_REVIEW_RECORD
WHERE EPISODE_ID=%s AND REVIEW_TYPE=%s
ORDER BY ATTEMPT_NO DESC
LIMIT 1
""".strip()

_LIST_TYPE_SQL = """
SELECT REVIEW_ID, EPISODE_ID, REVIEW_TYPE, ATTEMPT_NO, DECISION,
       SOURCE_SHA256, REVIEWER_TYPE, PAYLOAD, CREATE_TIME
FROM TB_REVIEW_RECORD
WHERE EPISODE_ID=%s AND REVIEW_TYPE=%s
ORDER BY ATTEMPT_NO ASC
""".strip()


def review_id(episode_id: str, review_type: str, attempt_no: int = 1) -> str:
    raw = f"{episode_id}|{review_type}|{int(attempt_no)}".encode("utf-8")
    return "RV_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlReviewRecordRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "review_type", "decision", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("review record missing required fields: " + ", ".join(missing))
        episode_id = str(row["episode_id"])
        review_type = str(row["review_type"])
        attempt_no = int(row.get("attempt_no", 1))
        if attempt_no < 1:
            raise ValueError("review record attempt_no must be >= 1")
        rid = str(row.get("review_id") or review_id(episode_id, review_type, attempt_no))
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = projection_envelope(
                payload_value,
                row["payload_ref"],
                "EPISODE_REVIEW_REF",
                {
                    "review_type": review_type,
                    "decision": str(row["decision"]),
                    "attempt_no": attempt_no,
                },
            )
        payload = bounded_json(payload_value, entity="review record")
        self.connection.execute(
            _UPSERT_SQL,
            (
                rid, episode_id, review_type, attempt_no, str(row["decision"]),
                row.get("source_sha256"), row.get("reviewer_type"), payload,
            ),
        )
        return {
            "review_id": rid,
            "episode_id": episode_id,
            "review_type": review_type,
            "attempt_no": attempt_no,
        }

    def get_by_id(self, review_id_value: str) -> dict | None:
        return self._decode(self.connection.query_one(_BY_ID_SQL, (str(review_id_value),)))

    def get_latest(self, episode_id: str, review_type: str) -> dict | None:
        return self._decode(
            self.connection.query_one(
                _LATEST_SQL, (str(episode_id), str(review_type))
            )
        )

    def list_attempts(self, episode_id: str, review_type: str) -> list[dict]:
        rows = self.connection.query_all(
            _LIST_TYPE_SQL, (str(episode_id), str(review_type))
        ) or []
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
            "review_id": row.get("REVIEW_ID") or row.get("review_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "review_type": row.get("REVIEW_TYPE") or row.get("review_type"),
            "attempt_no": row.get("ATTEMPT_NO") or row.get("attempt_no"),
            "decision": row.get("DECISION") or row.get("decision"),
            "source_sha256": row.get("SOURCE_SHA256") or row.get("source_sha256"),
            "reviewer_type": row.get("REVIEWER_TYPE") or row.get("reviewer_type"),
            "payload": payload,
        }
