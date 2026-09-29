from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import next_action  # noqa: E402


def test_ordinary_patch_review_frames_excludes_user_exception_lanes(monkeypatch, tmp_path):
    monkeypatch.setattr(next_action, "_expected_frames", lambda _ep: 4)
    ledger = {
        "01": {"status": "REPAIR_READY", "current_candidate": {"attempt_id": "a1"}, "attempts": [{"attempt_id": "a1", "request": {"capture_id": "auto-repair-PRODUCTION_REVIEW-01"}}]},
        "02": {"status": "REPAIR_READY", "current_candidate": {"attempt_id": "a2"}, "attempts": [{"attempt_id": "a2", "request": {"capture_id": "user-continuation-02-1"}}]},
        "03": {"status": "REPAIR_READY", "current_candidate": {"attempt_id": "a3"}, "attempts": [{"attempt_id": "a3", "request": {"capture_id": "user-exception-03-1"}}]},
        "04": {"status": "ORIGINAL_READY", "current_candidate": {"attempt_id": "a4"}, "attempts": [{"attempt_id": "a4", "request": {"capture_id": "batch-04"}}]},
    }
    assert next_action._ordinary_patch_review_frames(tmp_path, ledger) == [1]
