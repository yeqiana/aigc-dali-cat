"""Scheduler never exits 0 while an image Review still needs authority."""
from __future__ import annotations

from pathlib import Path
import sys

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import image_scheduler
import review_queue


def _queue(status: str, kind=review_queue.FINAL_SEMANTIC) -> dict:
    return {
        "items": [{"frame": 1, "status": "generated"}],
        review_queue.QUEUE_KEY: [{
            "review_kind": kind, "frame": 1, "status": status,
            "review_key": "review-1", "receipt": None,
        }],
    }


def test_final_semantic_quarantine_trumps_generated_image():
    assert image_scheduler._scheduler_terminal_rc(
        _queue("blocked"), has_block=False, has_failure=False) == 22


def test_live_foreign_review_cannot_be_reported_as_success():
    assert image_scheduler._scheduler_terminal_rc(
        _queue("running"), has_block=False, has_failure=False) == 24


def test_queued_review_is_pending_not_success():
    assert image_scheduler._scheduler_terminal_rc(
        _queue("queued"), has_block=False, has_failure=False) == 20


def test_success_only_after_review_terminal():
    assert image_scheduler._scheduler_terminal_rc(
        _queue("finalized"), has_block=False, has_failure=False) == 0


def test_running_fast_scout_also_prevents_false_success():
    assert image_scheduler._scheduler_terminal_rc(
        _queue("running", kind=review_queue.FAST_SCOUT),
        has_block=False, has_failure=False) == 24
