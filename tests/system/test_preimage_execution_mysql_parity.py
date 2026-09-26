from __future__ import annotations

import contextlib
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import preimage_execution_persistence as execution  # noqa: E402


class FakeConnection:
    @contextlib.contextmanager
    def transaction(self):
        yield self

    def close(self):
        pass


class FakeRuns:
    def __init__(self):
        self.rows = {}

    def upsert(self, record):
        self.rows[record["workflow_run_id"]] = deepcopy(record)
        return record


class FakeTasks:
    def __init__(self):
        self.rows = {}

    def upsert(self, record):
        self.rows[record["task_id"]] = deepcopy(record)
        return record

    def list_run(self, workflow_run_id):
        return [
            deepcopy(row)
            for row in self.rows.values()
            if row.get("workflow_run_id") == workflow_run_id
        ]


def _exercise(ep):
    execution.begin_execution(
        ep,
        snapshot_id="snap",
        task_id="task",
        execution_id="exec",
        attempt=1,
        idempotency_key="idem",
    )
    execution.mark_candidate_ready(ep, snapshot_id="snap", task_id="task", execution_id="exec")
    execution.prepare_commit(
        ep,
        snapshot_id="snap",
        task_id="task",
        execution_id="exec",
        attempt=1,
        idempotency_key="idem",
        input_sha="a" * 64,
        output_sha="b" * 64,
    )
    execution.mark_committed(
        ep,
        snapshot_id="snap",
        task_id="task",
        execution_id="exec",
        commit_id="commit-1",
    )
    replay = execution.replay_state(
        ep,
        snapshot_id="snap",
        idempotency_key="idem",
        actual_authority_sha="b" * 64,
    )
    record = execution.find_execution(ep, "snap", "task", "exec")
    return record, replay


def test_mysql_and_json_modes_have_same_commit_receipt_semantics(monkeypatch, tmp_path):
    json_ep = tmp_path / "json"
    json_ep.mkdir()
    monkeypatch.setattr(execution, "mode", lambda: "json")
    json_record, json_replay = _exercise(json_ep)

    mysql_ep = tmp_path / "mysql"
    mysql_ep.mkdir()
    conn = FakeConnection()
    runs = FakeRuns()
    tasks = FakeTasks()
    monkeypatch.setattr(execution, "mode", lambda: "mysql")
    monkeypatch.setattr(execution.episode_identity, "storage_episode_id", lambda _ep: "EP_TEST")
    monkeypatch.setattr(execution, "_mysql_repositories", lambda: (conn, runs, tasks))
    mysql_record, mysql_replay = _exercise(mysql_ep)

    assert mysql_record["status"] == json_record["status"] == "COMMITTED"
    assert mysql_record["commit_receipt"]["status"] == json_record["commit_receipt"]["status"] == "COMMITTED"
    assert mysql_record["commit_receipt"]["input_sha"] == json_record["commit_receipt"]["input_sha"]
    assert mysql_record["commit_receipt"]["output_sha"] == json_record["commit_receipt"]["output_sha"]
    assert mysql_replay["status"] == json_replay["status"] == "REPLAYED"
