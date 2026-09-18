from __future__ import annotations

from copy import deepcopy


_UPSERT_SQL = """
INSERT INTO TB_PRODUCTION_FRAME (
    EPISODE_ID, FRAME_NO, STATUS, APPROVED_ARTIFACT_ID,
    CURRENT_ATTEMPT_ID, CONTRACT_SHA256
) VALUES (%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    STATUS=VALUES(STATUS),
    APPROVED_ARTIFACT_ID=VALUES(APPROVED_ARTIFACT_ID),
    CURRENT_ATTEMPT_ID=VALUES(CURRENT_ATTEMPT_ID),
    CONTRACT_SHA256=VALUES(CONTRACT_SHA256)
""".strip()

_GET_SQL = """
SELECT EPISODE_ID, FRAME_NO, STATUS, APPROVED_ARTIFACT_ID,
       CURRENT_ATTEMPT_ID, CONTRACT_SHA256, UPDATE_TIME
FROM TB_PRODUCTION_FRAME
WHERE EPISODE_ID=%s AND FRAME_NO=%s
LIMIT 1
""".strip()

_LIST_SQL = """
SELECT EPISODE_ID, FRAME_NO, STATUS, APPROVED_ARTIFACT_ID,
       CURRENT_ATTEMPT_ID, CONTRACT_SHA256, UPDATE_TIME
FROM TB_PRODUCTION_FRAME
WHERE EPISODE_ID=%s
ORDER BY FRAME_NO ASC
""".strip()


class MySqlProductionFrameRepository:
    """Current durable production state for each Episode frame."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "frame_no", "status")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError(
                "production frame missing required fields: " + ", ".join(missing)
            )
        episode_id = str(row["episode_id"])
        frame_no = int(row["frame_no"])
        if frame_no < 1 or frame_no > 999:
            raise ValueError("production frame frame_no must be 1..999")
        status = str(row["status"])
        self.connection.execute(
            _UPSERT_SQL,
            (
                episode_id,
                frame_no,
                status,
                row.get("approved_artifact_id"),
                row.get("current_attempt_id"),
                row.get("contract_sha256"),
            ),
        )
        return {
            "episode_id": episode_id,
            "frame_no": frame_no,
            "status": status,
        }

    def get(self, episode_id: str, frame_no: int) -> dict | None:
        return self._decode(
            self.connection.query_one(_GET_SQL, (str(episode_id), int(frame_no)))
        )

    def list_episode(self, episode_id: str) -> list[dict]:
        rows = self.connection.query_all(_LIST_SQL, (str(episode_id),)) or []
        return [decoded for row in rows if (decoded := self._decode(row)) is not None]

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if not row:
            return None
        return {
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "frame_no": row.get("FRAME_NO") or row.get("frame_no"),
            "status": row.get("STATUS") or row.get("status"),
            "approved_artifact_id": (
                row.get("APPROVED_ARTIFACT_ID")
                if "APPROVED_ARTIFACT_ID" in row
                else row.get("approved_artifact_id")
            ),
            "current_attempt_id": (
                row.get("CURRENT_ATTEMPT_ID")
                if "CURRENT_ATTEMPT_ID" in row
                else row.get("current_attempt_id")
            ),
            "contract_sha256": (
                row.get("CONTRACT_SHA256")
                if "CONTRACT_SHA256" in row
                else row.get("contract_sha256")
            ),
            "update_time": row.get("UPDATE_TIME") or row.get("update_time"),
        }
