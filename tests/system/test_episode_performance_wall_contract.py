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
