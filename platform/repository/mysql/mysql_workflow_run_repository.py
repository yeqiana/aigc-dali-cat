from __future__ import annotations


_UPSERT_SQL = """
INSERT INTO TB_WORKFLOW_RUN (
    WORKFLOW_RUN_ID, EPISODE_ID, RUNTIME_TYPE, RUN_REASON,
    STATUS, START_TIME, END_TIME
) VALUES (%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    RUNTIME_TYPE=VALUES(RUNTIME_TYPE),
    RUN_REASON=VALUES(RUN_REASON),
    STATUS=VALUES(STATUS),
    START_TIME=VALUES(START_TIME),
    END_TIME=VALUES(END_TIME)
""".strip()

_GET_SQL = """
SELECT WORKFLOW_RUN_ID, EPISODE_ID, RUNTIME_TYPE, RUN_REASON,
       STATUS, START_TIME, END_TIME, CREATE_TIME
FROM TB_WORKFLOW_RUN
WHERE WORKFLOW_RUN_ID=%s
LIMIT 1
""".strip()


class MySqlWorkflowRunRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        required = ("workflow_run_id", "episode_id", "runtime_type", "run_reason", "status")
        missing = [key for key in required if record.get(key) in (None, "")]
        if missing:
            raise ValueError("workflow run missing required fields: " + ", ".join(missing))
        run_id = str(record["workflow_run_id"])
        self.connection.execute(
            _UPSERT_SQL,
            (
                run_id,
                str(record["episode_id"]),
                str(record["runtime_type"]),
                str(record["run_reason"]),
                str(record["status"]),
                record.get("start_time"),
                record.get("end_time"),
            ),
        )
        return {"workflow_run_id": run_id, "episode_id": str(record["episode_id"])}

    def get(self, workflow_run_id: str) -> dict | None:
        row = self.connection.query_one(_GET_SQL, (str(workflow_run_id),))
        if not row:
            return None
        return {
            "workflow_run_id": row.get("WORKFLOW_RUN_ID") or row.get("workflow_run_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "runtime_type": row.get("RUNTIME_TYPE") or row.get("runtime_type"),
            "run_reason": row.get("RUN_REASON") or row.get("run_reason"),
            "status": row.get("STATUS") or row.get("status"),
            "start_time": row.get("START_TIME") or row.get("start_time"),
            "end_time": row.get("END_TIME") or row.get("end_time"),
            "create_time": row.get("CREATE_TIME") or row.get("create_time"),
        }
