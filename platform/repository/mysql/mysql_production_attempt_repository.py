from __future__ import annotations

import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import bounded_json


_UPSERT_SQL = """
INSERT INTO TB_PRODUCTION_ATTEMPT (
    ATTEMPT_ID, EPISODE_ID, FRAME_NO, ATTEMPT_NO, ATTEMPT_KIND,
    STATUS, PROVIDER, MODEL, ARTIFACT_ID, ERROR_CODE, ELAPSED_MS,
    START_TIME, END_TIME, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    STATUS=VALUES(STATUS),
    PROVIDER=VALUES(PROVIDER),
    MODEL=VALUES(MODEL),
    ARTIFACT_ID=VALUES(ARTIFACT_ID),
    ERROR_CODE=VALUES(ERROR_CODE),
    ELAPSED_MS=VALUES(ELAPSED_MS),
    START_TIME=VALUES(START_TIME),
    END_TIME=VALUES(END_TIME),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_GET_SQL = """
SELECT ATTEMPT_ID, EPISODE_ID, FRAME_NO, ATTEMPT_NO, ATTEMPT_KIND,
       STATUS, PROVIDER, MODEL, ARTIFACT_ID, ERROR_CODE, ELAPSED_MS,
       START_TIME, END_TIME, PAYLOAD, CREATE_TIME
FROM TB_PRODUCTION_ATTEMPT
WHERE ATTEMPT_ID=%s
LIMIT 1
""".strip()

_LIST_FRAME_SQL = """
SELECT ATTEMPT_ID, EPISODE_ID, FRAME_NO, ATTEMPT_NO, ATTEMPT_KIND,
       STATUS, PROVIDER, MODEL, ARTIFACT_ID, ERROR_CODE, ELAPSED_MS,
       START_TIME, END_TIME, PAYLOAD, CREATE_TIME
FROM TB_PRODUCTION_ATTEMPT
WHERE EPISODE_ID=%s AND FRAME_NO=%s
ORDER BY ATTEMPT_NO ASC
""".strip()


class MySqlProductionAttemptRepository:
    """Immutable-attempt identity with updateable execution result projection."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = (
            "attempt_id",
            "episode_id",
            "frame_no",
            "attempt_no",
            "attempt_kind",
            "status",
            "payload",
        )
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError(
                "production attempt missing required fields: " + ", ".join(missing)
            )
        frame_no = int(row["frame_no"])
        attempt_no = int(row["attempt_no"])
        if frame_no < 1 or frame_no > 999:
            raise ValueError("production attempt frame_no must be 1..999")
        if attempt_no < 1:
            raise ValueError("production attempt attempt_no must be >= 1")
        payload = bounded_json(row["payload"], entity="production attempt")
        self.connection.execute(
            _UPSERT_SQL,
            (
                str(row["attempt_id"]),
                str(row["episode_id"]),
                frame_no,
                attempt_no,
                str(row["attempt_kind"]),
                str(row["status"]),
                row.get("provider"),
                row.get("model"),
                row.get("artifact_id"),
                row.get("error_code"),
                row.get("elapsed_ms"),
                row.get("start_time"),
                row.get("end_time"),
                payload,
            ),
        )
        return {
            "attempt_id": str(row["attempt_id"]),
            "episode_id": str(row["episode_id"]),
            "frame_no": frame_no,
            "attempt_no": attempt_no,
        }

    def get(self, attempt_id: str) -> dict | None:
        return self._decode(
            self.connection.query_one(_GET_SQL, (str(attempt_id),))
        )

    def list_frame(self, episode_id: str, frame_no: int) -> list[dict]:
        rows = self.connection.query_all(
            _LIST_FRAME_SQL, (str(episode_id), int(frame_no))
        ) or []
        return [decoded for row in rows if (decoded := self._decode(row)) is not None]

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if not row:
            return None
        payload = row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            raise ValueError("production attempt payload must decode to object")
        return {
            "attempt_id": row.get("ATTEMPT_ID") or row.get("attempt_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "frame_no": row.get("FRAME_NO") or row.get("frame_no"),
            "attempt_no": row.get("ATTEMPT_NO") or row.get("attempt_no"),
            "attempt_kind": row.get("ATTEMPT_KIND") or row.get("attempt_kind"),
            "status": row.get("STATUS") or row.get("status"),
            "provider": row.get("PROVIDER") or row.get("provider"),
            "model": row.get("MODEL") or row.get("model"),
            "artifact_id": (
                row.get("ARTIFACT_ID")
                if "ARTIFACT_ID" in row
                else row.get("artifact_id")
            ),
            "error_code": (
                row.get("ERROR_CODE")
                if "ERROR_CODE" in row
                else row.get("error_code")
            ),
            "elapsed_ms": (
                row.get("ELAPSED_MS")
                if "ELAPSED_MS" in row
                else row.get("elapsed_ms")
            ),
            "start_time": row.get("START_TIME") or row.get("start_time"),
            "end_time": row.get("END_TIME") or row.get("end_time"),
            "payload": payload,
        }
