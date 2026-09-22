#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_status_snapshot  # noqa: E402


def _write(ep: Path, rel: str, data: dict) -> None:
    path = ep / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _episode(tmp: str) -> Path:
    ep = Path(tmp) / "episode"
    ep.mkdir(parents=True)
    return ep


def test_stale_user_decision_is_suppressed_after_weak_pass_without_writing_new_state():
    with tempfile.TemporaryDirectory() as td:
        ep = _episode(td)
        _write(ep, "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        _write(ep, "meta/runtime-runner-state.json", {"status": "HOST_WAIT", "heartbeat": "2026-09-16T16:15:46+08:00"})
        _write(ep, "meta/runtime/next-action.json", {
            "episode_state": "STORYBOARD_LOCKED",
            "action": "USER_DECISION_REQUIRED",
            "frames": [3],
            "hard_stop": True,
            "auto_recoverable": False,
            "reason": "old visual lock candidate pool exhausted",
        })
        _write(ep, "meta/production-ledger.json", {"frames": {
            "01": {"status": "PASSED", "current_candidate": {"sha256": "1" * 64}},
            "03": {"status": "WEAK_PASS", "current_candidate": {"sha256": "3" * 64}},
            "08": {"status": "PASSED", "current_candidate": {"sha256": "8" * 64}},
            "16": {"status": "LOCKED", "current_candidate": {"sha256": "6" * 64}},
        }})
        _write(ep, "meta/visual-lock-admissions.json", {"items": {
            "V-B": {"status": "PASS"}, "V-A": {"status": "WEAK_PASS"},
            "V-W": {"status": "PASS"}, "V-H": {"status": "PASS"},
        }})

        result = runtime_status_snapshot.snapshot(ep)

        assert result["production_stage"] == "STORYBOARD_LOCKED"
        assert result["current_action"] is None
        assert result["needs_user"] is False
        assert result["execution_status"] == "HOST_WAIT"
        assert result["blocking_reason"] is None
        assert result["image_progress"]["accepted_frames"] == 4
        assert result["image_progress"]["weak_pass_frames"] == 1
        assert result["review_progress"]["visual_lock_accepted"] == 4
        assert "STALE_USER_DECISION_ACTION" in result["consistency_warnings"]
        assert not (ep / "meta/runtime-status-snapshot.json").exists()


def test_real_user_decision_wins_over_runner_wait_and_exposes_reason():
    with tempfile.TemporaryDirectory() as td:
        ep = _episode(td)
        _write(ep, "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        _write(ep, "meta/runtime-runner-state.json", {"status": "HOST_WAIT", "heartbeat": "2026-09-16T16:15:46+08:00"})
        _write(ep, "meta/runtime/next-action.json", {
            "episode_state": "STORYBOARD_LOCKED",
            "action": "USER_DECISION_REQUIRED",
            "frames": [3],
            "blocking": True,
            "hard_stop": True,
            "auto_recoverable": False,
            "reason": "manual choice required",
        })
        _write(ep, "meta/production-ledger.json", {"frames": {"03": {"status": "NEEDS_USER"}}})

        result = runtime_status_snapshot.snapshot(ep)

        assert result["execution_status"] == "NEEDS_USER"
        assert result["needs_user"] is True
        assert result["current_action"] == "USER_DECISION_REQUIRED"
        assert result["blocking_reason"] == "manual choice required"
        assert result["next_step"] == "USER_DECISION_REQUIRED"


def test_auto_recoverable_machine_action_masks_transient_needs_user_ledger_state():
    with tempfile.TemporaryDirectory() as td:
        ep = _episode(td)
        _write(ep, "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        _write(ep, "meta/runtime/next-action.json", {
            "episode_state": "STORYBOARD_LOCKED",
            "action": "APPLY_VISUAL_LOCK_WEAK_PASS",
            "executor": "MACHINE",
            "frames": [3],
            "hard_stop": False,
            "auto_recoverable": True,
        })
        _write(ep, "meta/production-ledger.json", {"frames": {"03": {"status": "NEEDS_USER"}}})

        result = runtime_status_snapshot.snapshot(ep)

        assert result["execution_status"] == "READY"
        assert result["needs_user"] is False
        assert result["auto_recoverable"] is True
        assert result["current_action"] == "APPLY_VISUAL_LOCK_WEAK_PASS"


def test_live_runner_has_running_precedence_when_no_blocking_action_exists():
    with tempfile.TemporaryDirectory() as td:
        ep = _episode(td)
        heartbeat = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        _write(ep, "meta/episode-state.json", {"current_state": "VISUAL_CALIBRATED"})
        _write(ep, "meta/runtime-runner-state.json", {"status": "RUNNING", "heartbeat": heartbeat})
        _write(ep, "meta/production-ledger.json", {"frames": {"01": {"status": "PASSED"}}})

        result = runtime_status_snapshot.snapshot(ep)

        assert result["execution_status"] == "RUNNING"
        assert result["heartbeat"]["health"] == "HEALTHY"
        assert result["heartbeat"]["host_loop"] == "RUNNING"
