import json

from platform.repository.mysql.mysql_task_repository import MySqlTaskRepository
from platform.repository.mysql.mysql_workflow_run_repository import (
    MySqlWorkflowRunRepository,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None
        self.rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.one

    def query_all(self, sql, params=None):
        return self.rows


def test_workflow_run_upsert_and_get():
    conn = FakeConnection()
    repo = MySqlWorkflowRunRepository(conn)
    repo.upsert({
        "workflow_run_id": "WR_1",
        "episode_id": "EPU_1",
        "runtime_type": "WORK",
        "run_reason": "RECOVERY_PROJECTION",
        "status": "CURRENT",
    })
    assert conn.executed[-1][1][:5] == (
        "WR_1", "EPU_1", "WORK", "RECOVERY_PROJECTION", "CURRENT"
    )
    conn.one = {
        "WORKFLOW_RUN_ID": "WR_1",
        "EPISODE_ID": "EPU_1",
        "RUNTIME_TYPE": "WORK",
        "RUN_REASON": "RECOVERY_PROJECTION",
        "STATUS": "CURRENT",
    }
    assert repo.get("WR_1")["runtime_type"] == "WORK"


def test_task_upsert_list_and_delete_projection():
    conn = FakeConnection()
    repo = MySqlTaskRepository(conn)
    repo.upsert({
        "task_id": "TASK_1",
        "episode_id": "EPU_1",
        "workflow_run_id": "WR_1",
        "task_type": "RUNTIME_CHECKPOINT_STEP",
        "status": "PASS",
        "attempt_no": 1,
        "payload": {"step": "CREATIVE_STORY"},
    })
    assert json.loads(conn.executed[-1][1][-1])["step"] == "CREATIVE_STORY"
    conn.rows = [{
        "TASK_ID": "TASK_1",
        "EPISODE_ID": "EPU_1",
        "WORKFLOW_RUN_ID": "WR_1",
        "TASK_TYPE": "RUNTIME_CHECKPOINT_STEP",
        "STATUS": "PASS",
        "ATTEMPT_NO": 1,
        "PAYLOAD": '{"step":"CREATIVE_STORY"}',
    }]
    assert repo.list_run("WR_1")[0]["payload"]["step"] == "CREATIVE_STORY"
    assert repo.delete_run_projection("WR_1") == 1
