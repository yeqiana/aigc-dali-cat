from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_performance as perf


def _ts(seconds: int) -> str:
    base = dt.datetime(2026, 9, 15, 10, 0, tzinfo=dt.timezone.utc)
    return (base + dt.timedelta(seconds=seconds)).isoformat()


def test_stage_wall_uses_interval_union_and_keeps_resource_time_separate():
    data = {
        "started_at": _ts(0),
        "finalized_at": _ts(15),
        "stages": {
            "VISUAL_LOCK": {
                "runs": [
                    {"started_at": _ts(0), "ended_at": _ts(10), "duration_seconds": 10.0, "status": "PASS"},
                    {"started_at": _ts(5), "ended_at": _ts(15), "duration_seconds": 10.0, "status": "PASS"},
                ]
            }
        },
        "named_spans": {},
        "image_attempts": [],
        "summary": {},
    }
    perf._refresh_summary(data)
    row = data["summary"]["stage_wall"]["VISUAL_LOCK"]
    assert row["wall_seconds"] == 15.0
    assert row["resource_seconds"] == 20.0
    assert row["unclosed_runs"] == 0


def test_finalize_closes_open_telemetry_without_claiming_pass():
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perf-finalize-", dir=tests_root) as raw:
        ep = Path(raw)
        run_id = perf.begin_stage(ep, "VISUAL_LOCK", source="test")
        assert run_id
        result = perf.finalize(ep, "PUBLISH_READY")
        row = result["stages"]["VISUAL_LOCK"]["runs"][-1]
        assert row["status"] == "CLOSED_AT_FINALIZE"
        assert row["metadata"]["auto_closed_at_finalize"] is True
        assert row["ended_at"]
        assert isinstance(row["duration_seconds"], float)
        assert result["summary"]["stage_wall"]["VISUAL_LOCK"]["unclosed_runs"] == 0
        assert result["final_status"] == "PUBLISH_READY"


def test_queue_attempt_is_idempotent_by_item_and_attempt():
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perf-image-", dir=tests_root) as raw:
        ep = Path(raw)
        item = {
            "id": "queue-01",
            "frame": 1,
            "scope": "batch",
            "kind": "original",
            "model": "gpt-image-2",
            "attempts": 2,
            "started_at": _ts(0),
            "completed_at": _ts(10),
        }
        perf.record_queue_image_attempt(ep, item, status="tech_failed", error_code="TIMEOUT")
        perf.record_queue_image_attempt(ep, item, status="generated")
        rows = perf.load(ep, False)["image_attempts"]
        assert len(rows) == 1
        assert rows[0]["queue_item_id"] == "queue-01"
        assert rows[0]["attempt"] == 2
        assert rows[0]["status"] == "generated"
        assert rows[0]["error_code"] is None
        assert rows[0]["elapsed_seconds"] == 10.0


def test_execution_sessions_split_active_host_user_and_idle_wall():
    data = {
        "started_at": _ts(0), "updated_at": _ts(40), "finalized_at": None,
        "stages": {}, "named_spans": {}, "image_attempts": [], "summary": {},
        "execution_sessions": [{
            "session_id": "run-1", "source": "test", "started_at": _ts(0), "ended_at": _ts(40), "status": "COMPLETE",
            "states": [
                {"state": "ACTIVE", "started_at": _ts(0), "ended_at": _ts(10)},
                {"state": "HOST_WAIT", "started_at": _ts(10), "ended_at": _ts(25)},
                {"state": "ACTIVE", "started_at": _ts(25), "ended_at": _ts(30)},
                {"state": "USER_WAIT", "started_at": _ts(30), "ended_at": _ts(35)},
                {"state": "IDLE", "started_at": _ts(35), "ended_at": _ts(40)},
            ],
        }],
    }
    perf._refresh_summary(data)
    latest = data["summary"]["execution_wall"]["latest"]
    assert latest["active_seconds"] == 15.0
    assert latest["host_wait_seconds"] == 15.0
    assert latest["user_wait_seconds"] == 5.0
    assert latest["idle_seconds"] == 5.0
    assert latest["wall_seconds"] == 40.0
    assert data["summary"]["performance_slo"]["active_wall_seconds"] == 15.0


def test_new_execution_session_closes_previous_wait_and_latest_slo_ignores_history():
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perf-session-", dir=tests_root) as raw:
        ep = Path(raw)
        perf.begin_execution_session(ep, source="test", session_id="old", at=_ts(0))
        perf.transition_execution_state(ep, "ACTIVE", session_id="old", at=_ts(0))
        perf.transition_execution_state(ep, "HOST_WAIT", session_id="old", at=_ts(10))
        perf.begin_execution_session(ep, source="test", session_id="new", at=_ts(100))
        perf.transition_execution_state(ep, "ACTIVE", session_id="new", at=_ts(100))
        perf.transition_execution_state(ep, "IDLE", session_id="new", at=_ts(120))
        perf.finish_execution_session(ep, session_id="new", status="COMPLETE", at=_ts(120))
        data = perf.load(ep, False)
        perf._refresh_summary(data)
        assert data["execution_sessions"][0]["status"] == "HANDOFF_TO_NEXT_SESSION"
        assert data["execution_sessions"][0]["states"][-1]["state"] == "HOST_WAIT"
        assert data["execution_sessions"][0]["states"][-1]["duration_seconds"] == 90.0
        latest = data["summary"]["execution_wall"]["latest"]
        assert latest["active_seconds"] == 20.0
        assert data["summary"]["performance_slo"]["active_wall_seconds"] == 20.0


def test_execution_result_classification_keeps_waits_out_of_active_time():
    assert perf.execution_state_for_result(20, {"action": "PRODUCT_REVIEW"}) == "HOST_WAIT"
    assert perf.execution_state_for_result(22, {}) == "USER_WAIT"
    assert perf.execution_state_for_result(0, {"action": "USER_DECISION_REQUIRED"}) == "USER_WAIT"
    assert perf.execution_state_for_result(0, {"action": "COMPLETE"}) == "IDLE"
