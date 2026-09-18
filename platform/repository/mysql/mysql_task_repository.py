from __future__ import annotations

import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import bounded_json


_UPSERT_SQL = """
INSERT INTO TB_TASK (
    TASK_ID, EPISODE_ID, WORKFLOW_RUN_ID, TASK_TYPE, FRAME_NO,
    STATUS, ATTEMPT_NO, OWNER_ID, START_TIME, END_TIME, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    TASK_TYPE=VALUES(TASK_TYPE),
    FRAME_NO=VALUES(FRAME_NO),
    STATUS=VALUES(STATUS),
    ATTEMPT_NO=VALUES(ATTEMPT_NO),
    OWNER_ID=VALUES(OWNER_ID),
    START_TIME=VALUES(START_TIME),
    END_TIME=VALUES(END_TIME),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_LIST_RUN_SQL = """
SELECT TASK_ID, EPISODE_ID, WORKFLOW_RUN_ID, TASK_TYPE, FRAME_NO,
       STATUS, ATTEMPT_NO, OWNER_ID, START_TIME, END_TIME, PAYLOAD,
       CREATE_TIME, UPDATE_TIME
FROM TB_TASK
WHERE WORKFLOW_RUN_ID=%s
ORDER BY CREATE_TIME ASC, TASK_ID ASC
""".strip()

_DELETE_RUN_SQL = """
DELETE FROM TB_TASK
WHERE WORKFLOW_RUN_ID=%s
""".strip()


class MySqlTaskRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = (
            "task_id", "episode_id", "workflow_run_id",
            "task_type", "status", "attempt_no", "payload",
        )
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("task row missing required fields: " + ", ".join(missing))
        attempt_no = int(row["attempt_no"])
        if attempt_no < 1:
            raise ValueError("task attempt_no must be >= 1")
        payload = bounded_json(row["payload"], entity="task")
        self.connection.execute(
            _UPSERT_SQL,
            (
                str(row["task_id"]),
                str(row["episode_id"]),
                str(row["workflow_run_id"]),
                str(row["task_type"]),
                row.get("frame_no"),
                str(row["status"]),
                attempt_no,
                row.get("owner_id"),
                row.get("start_time"),
                row.get("end_time"),
                payload,
            ),
        )
        return {
            "task_id": str(row["task_id"]),
            "workflow_run_id": str(row["workflow_run_id"]),
        }

    def list_run(self, workflow_run_id: str) -> list[dict]:
        rows = self.connection.query_all(_LIST_RUN_SQL, (str(workflow_run_id),)) or []
        return [decoded for row in rows if (decoded := self._decode(row)) is not None]

    def delete_run_projection(self, workflow_run_id: str) -> int:
        return int(
            self.connection.execute(_DELETE_RUN_SQL, (str(workflow_run_id),)) or 0
        )

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
            raise ValueError("task payload must decode to object")
        return {
            "task_id": row.get("TASK_ID") or row.get("task_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "workflow_run_id": row.get("WORKFLOW_RUN_ID") or row.get("workflow_run_id"),
            "task_type": row.get("TASK_TYPE") or row.get("task_type"),
            "frame_no": row.get("FRAME_NO") if "FRAME_NO" in row else row.get("frame_no"),
            "status": row.get("STATUS") or row.get("status"),
            "attempt_no": row.get("ATTEMPT_NO") or row.get("attempt_no"),
            "owner_id": row.get("OWNER_ID") if "OWNER_ID" in row else row.get("owner_id"),
            "start_time": row.get("START_TIME") or row.get("start_time"),
            "end_time": row.get("END_TIME") or row.get("end_time"),
            "payload": payload,
        }
