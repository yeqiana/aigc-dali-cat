from __future__ import annotations

from contextlib import nullcontext
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_checkpoint_persistence as persistence  # noqa: E402
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, payload_bytes  # noqa: E402


class FakeConnection:
    def transaction(self):
        return nullcontext(self)

    def close(self):
        pass


class FakeRuns:
    def __init__(self):
        self.row = None
        self.saved = []

    def upsert(self, record):
        self.saved.append(dict(record))
        self.row = dict(record)

    def get(self, _run_id):
        return self.row


class FakeTasks:
    def __init__(self):
        self.rows = []

    def delete_run_projection(self, _run_id):
        self.rows = []
        return 0

    def upsert(self, record):
        self.rows.append(dict(record))

    def list_run(self, _run_id):
        return list(self.rows)


def _wire(monkeypatch, mode="mysql"):
    runs = FakeRuns()
    tasks = FakeTasks()
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": mode},
    )
    monkeypatch.setattr(
        persistence.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        persistence,
        "_repositories",
        lambda: (FakeConnection(), runs, tasks),
    )
    return runs, tasks


def _checkpoint():
    return {
        "schema_version": 2,
        "story_os_version": "2.0",
        "runtime": "WORK",
        "last_completed": "CREATIVE_STORY",
        "next_action": "PREIMAGE_COMPILE",
        "locked_frames": ["01"],
        "failed_frames": [],
        "updated_at": "2026-09-18T00:10:00+00:00",
        "step_runs": [{
            "step": "CREATIVE_STORY",
            "status": "PASS",
            "attempt": 1,
            "started_at": "2026-09-18T00:00:00+00:00",
            "finished_at": "2026-09-18T00:10:00+00:00",
            "input_hash": "a",
            "output_hash": "b",
            "note": "ok",
        }],
    }


def test_mysql_projection_round_trips_checkpoint_without_file(monkeypatch, tmp_path):
    runs, tasks = _wire(monkeypatch, "mysql")
    data = _checkpoint()

    result = persistence.persist(tmp_path, data)
    loaded = persistence.load(tmp_path)

    assert result["step_count"] == 1
    assert loaded == data
    assert runs.saved[0]["run_reason"] == "RECOVERY_PROJECTION"
    assert {row["task_type"] for row in tasks.rows} == {
        persistence.META_TASK_TYPE,
        persistence.STEP_TASK_TYPE,
    }


def test_runner_events_are_externalized_and_round_trip_with_sha(monkeypatch, tmp_path):
    _runs, tasks = _wire(monkeypatch, "mysql")
    monkeypatch.setenv("STORY_OS_RUNTIME_WORKSPACE", str(tmp_path / "runtime"))
    data = _checkpoint()
    data["runner_events"] = [
        {"at": "2026-09-18T00:00:00+00:00", "event": "tick", "detail": "x" * 500}
        for _ in range(100)
    ]

    persistence.persist(tmp_path, data)
    meta = next(row for row in tasks.rows if row["task_type"] == persistence.META_TASK_TYPE)
    payload = meta["payload"]

    assert "runner_events" not in payload
    assert payload["runner_events_ref"]["projection_type"] == persistence.RUNNER_EVENTS_PROJECTION
    assert payload_bytes(payload) <= MAX_INLINE_PAYLOAD_BYTES
    assert persistence.load(tmp_path)["runner_events"] == data["runner_events"]


def test_runner_events_sha_mismatch_fails_closed(monkeypatch, tmp_path):
    _runs, tasks = _wire(monkeypatch, "mysql")
    monkeypatch.setenv("STORY_OS_RUNTIME_WORKSPACE", str(tmp_path / "runtime"))
    data = _checkpoint()
    data["runner_events"] = [{"event": "tick"}]
    persistence.persist(tmp_path, data)
    meta = next(row for row in tasks.rows if row["task_type"] == persistence.META_TASK_TYPE)
    rel = meta["payload"]["runner_events_ref"]["document"]["rel"]
    path = persistence.runtime_workspace.workspace_path(tmp_path, rel)
    path.write_text('[{"event":"tampered"}]', encoding="utf-8")

    with pytest.raises(ValueError, match="sha256 mismatch"):
        persistence.load(tmp_path)


def test_mysql_missing_is_authoritative_absence(monkeypatch, tmp_path):
    _runs, _tasks = _wire(monkeypatch, "mysql")
    assert persistence.load(tmp_path) is None


def test_mysql_failure_propagates_instead_of_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        persistence,
        "_repositories",
        lambda: (_ for _ in ()).throw(RuntimeError("mysql down")),
    )
    with pytest.raises(RuntimeError, match="mysql down"):
        persistence.load(tmp_path)
