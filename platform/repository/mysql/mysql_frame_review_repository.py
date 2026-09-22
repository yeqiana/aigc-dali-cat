from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from platform.repository.mysql.payload_policy import bounded_json


_UPSERT_SQL = """
INSERT INTO TB_FRAME_REVIEW (
    FRAME_REVIEW_ID, EPISODE_ID, FRAME_NO, REVIEW_TYPE, ATTEMPT_NO,
    DECISION, ASSET_SHA256, CONTRACT_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    DECISION=VALUES(DECISION),
    ASSET_SHA256=VALUES(ASSET_SHA256),
    CONTRACT_SHA256=VALUES(CONTRACT_SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_ID_SQL = """
SELECT FRAME_REVIEW_ID, EPISODE_ID, FRAME_NO, REVIEW_TYPE, ATTEMPT_NO,
       DECISION, ASSET_SHA256, CONTRACT_SHA256, PAYLOAD, CREATE_TIME
FROM TB_FRAME_REVIEW
WHERE FRAME_REVIEW_ID=%s
LIMIT 1
""".strip()

_LIST_SQL = """
SELECT FRAME_REVIEW_ID, EPISODE_ID, FRAME_NO, REVIEW_TYPE, ATTEMPT_NO,
       DECISION, ASSET_SHA256, CONTRACT_SHA256, PAYLOAD, CREATE_TIME
FROM TB_FRAME_REVIEW
WHERE EPISODE_ID=%s
ORDER BY FRAME_NO, REVIEW_TYPE
""".strip()


def frame_review_id(episode_id: str, frame_no: int, review_type: str = "FINAL", attempt_no: int = 1) -> str:
    raw = f"{episode_id}|{int(frame_no)}|{review_type}|{int(attempt_no)}".encode("utf-8")
    return "FR_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlFrameReviewRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "frame_no", "review_type", "decision", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("frame review missing required fields: " + ", ".join(missing))
        episode_id = str(row["episode_id"])
        frame_no = int(row["frame_no"])
        review_type = str(row.get("review_type") or "FINAL")
        attempt_no = int(row.get("attempt_no") or 1)
        rid = str(row.get("frame_review_id") or frame_review_id(episode_id, frame_no, review_type, attempt_no))
        payload = bounded_json(row["payload"], entity="frame review")
        self.connection.execute(
            _UPSERT_SQL,
            (
                rid, episode_id, frame_no, review_type, attempt_no,
                str(row["decision"]), row.get("asset_sha256"), row.get("contract_sha256"), payload,
            ),
        )
        return {"frame_review_id": rid, "episode_id": episode_id, "frame_no": frame_no,
                "review_type": review_type, "attempt_no": attempt_no}

    def get_current(self, episode_id: str, frame_no: int, review_type: str = "FINAL", attempt_no: int = 1) -> dict | None:
        rid = frame_review_id(str(episode_id), int(frame_no), str(review_type), int(attempt_no))
        return self.get_by_id(rid)

    def get_by_id(self, review_id: str) -> dict | None:
        return self._decode(self.connection.query_one(_BY_ID_SQL, (str(review_id),)))

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
            "frame_review_id": row.get("FRAME_REVIEW_ID") or row.get("frame_review_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "frame_no": row.get("FRAME_NO") or row.get("frame_no"),
            "review_type": row.get("REVIEW_TYPE") or row.get("review_type"),
            "attempt_no": row.get("ATTEMPT_NO") or row.get("attempt_no"),
            "decision": row.get("DECISION") or row.get("decision"),
            "asset_sha256": row.get("ASSET_SHA256") or row.get("asset_sha256"),
            "contract_sha256": row.get("CONTRACT_SHA256") or row.get("contract_sha256"),
            "payload": payload,
        }
