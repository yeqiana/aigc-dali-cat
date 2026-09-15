from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import product_runtime_adapter as adapter


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _request(request_id: str, *, started_at=None, finished_at=None, status="HOST_ACTION_REQUIRED") -> dict:
    row = {
        "request_id": request_id,
        "status": status,
        "next_step": "PREIMAGE_ENVIRONMENT",
        "task": {
            "task_id": f"task-{request_id}", "task_type": "ENVIRONMENT_PREPARE",
            "snapshot_id": "s" * 24, "candidate_output": "meta/runtime/preimage-candidates/environment.json",
        },
    }
    if started_at:
        row["started_at"] = started_at
    if finished_at:
        row["finished_at"] = finished_at
    return row


def test_start_handshake_records_real_worker_and_rejects_double_owner():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        request_id = "req-1"
        _write(ep / adapter.REQUEST_HISTORY_REL / f"{request_id}.json", _request(request_id))
        started = adapter.mark_preimage_task_running(ep, request_id, worker_id="devspace-worker-a")
        assert started["status"] == "RUNNING"
        assert started["worker_id"] == "devspace-worker-a"
        assert started["started_at"]
        state = json.loads((ep / "meta/runtime/preimage-task-state.json").read_text(encoding="utf-8"))
        execution = state["tasks"]["ENVIRONMENT_PREPARE"]["execution"]
        assert execution["worker_id"] == "devspace-worker-a"
        with pytest.raises(RuntimeError, match="ALREADY_RUNNING"):
            adapter.mark_preimage_task_running(ep, request_id, worker_id="devspace-worker-b")


def test_metrics_use_only_observed_execution_intervals():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        history = ep / adapter.REQUEST_HISTORY_REL
        _write(history / "a.json", _request("a", started_at="2026-09-15T10:00:00+00:00", finished_at="2026-09-15T10:10:00+00:00", status="FINALIZED"))
        _write(history / "b.json", _request("b", started_at="2026-09-15T10:05:00+00:00", finished_at="2026-09-15T10:15:00+00:00", status="FINALIZED"))
        _write(history / "c.json", _request("c"))
        metrics = adapter.preimage_execution_metrics(ep)
        assert metrics == {
            "snapshot_id": None, "requested": 3, "started": 2, "finished": 2, "inflight_now": 0,
            "peak_observed_concurrency": 2, "unmeasured_requests": 1,
            "measurement": "host_execution_intervals_only",
        }
