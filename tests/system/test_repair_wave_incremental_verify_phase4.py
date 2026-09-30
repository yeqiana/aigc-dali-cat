from __future__ import annotations

import sys
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import repair_aggregator


def _wave(tmp_path: Path) -> dict:
    plan = {
        "schema_version": 1,
        "episode_id": "synthetic",
        "repair_wave_id": "synthetic/production/repair-wave-1",
        "status": "STARTED",
        "frames": [
            {"frame_id": frame, "repairable": True, "repair_status": "ENQUEUED"}
            for frame in ("03", "07", "11")
        ],
        "summary": {"repaired_pass": 0, "still_failed": 0, "needs_user": 0},
    }
    repair_aggregator._write_plan(tmp_path, plan)
    return plan


def test_wave_completion_materializes_incremental_plan_once_and_keeps_context_separate(tmp_path):
    _wave(tmp_path)
    incremental = {
        "action": "PRODUCTION_INCREMENTAL_REQUIRED",
        "dirty_frames": ["03", "07", "11"],
        "context_frames": ["02", "03", "04", "06", "07", "08", "10", "11", "12"],
        "reused_frames": [f"{number:02d}" for number in range(1, 21) if number not in {3, 7, 11}],
    }
    with patch.object(repair_aggregator.incremental_closure, "plan", return_value=incremental) as plan_call:
        result = repair_aggregator.finalize_wave(
            tmp_path, repair_reviews={"03": "PASS", "07": "PASS", "11": "PASS"})
        resumed = repair_aggregator.finalize_wave(tmp_path)

    assert result["status"] == "COMPLETED"
    assert result["plan"]["incremental_verify_plan"] == incremental
    assert resumed["status"] == "ALREADY_COMPLETED"
    assert plan_call.call_count == 1
    trace = tmp_path / "meta/runtime/trace-events.jsonl"
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line]
    names = [row.get("event_type") for row in events]
    assert names.count("INCREMENTAL_VERIFY_STARTED") == 1
    assert names.count("INCREMENTAL_VERIFY_FINISHED") == 1


def test_wave_completion_fails_closed_when_planner_omits_repaired_candidate(tmp_path):
    _wave(tmp_path)
    with patch.object(repair_aggregator.incremental_closure, "plan", return_value={
        "action": "NOOP", "dirty_frames": [], "context_frames": [], "reused_frames": []
    }):
        result = repair_aggregator.finalize_wave(
            tmp_path, repair_reviews={"03": "PASS", "07": "PASS", "11": "PASS"})

    trace = tmp_path / "meta/runtime/trace-events.jsonl"
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line]
    assert any(row.get("event_type") == "INCREMENTAL_VERIFY_FINISHED"
               and row.get("status") == "INVALIDATION_MISMATCH" for row in events)
    assert result["plan"]["status"] == "COMPLETED"
    assert result["plan"]["incremental_verify_plan"]["action"] == "NOOP"
