from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import generation_attempt_authority
import image_scheduler
import phase5a_collaborative_canary as canary


def test_phase5a_technical_retry_may_use_only_attempt_two():
    item = {
        "kind": "original",
        "scope": "batch",
        "status": "queued",
        "generation_attempt_reason": "TECHNICAL_RETRY",
        "technical_retry_source_code": "ASPECT_RATIO_MISMATCH",
    }
    canary.validate_queued_attempt(
        item,
        {"attempts_consumed": 1, "remaining_attempts": 1, "active_attempt_index": None},
    )


def test_phase5a_original_without_technical_retry_marker_cannot_use_attempt_two():
    item = {"kind": "original", "scope": "batch", "status": "queued"}
    with pytest.raises(canary.CanaryContractError, match="CANARY_ORIGINAL_ITEM_CANNOT_USE_ATTEMPT2"):
        canary.validate_queued_attempt(
            item,
            {"attempts_consumed": 1, "remaining_attempts": 1, "active_attempt_index": None},
        )


def test_phase5a_no_path_can_use_attempt_three():
    item = {
        "kind": "original",
        "scope": "batch",
        "status": "queued",
        "generation_attempt_reason": "TECHNICAL_RETRY",
        "technical_retry_source_code": "ASPECT_RATIO_MISMATCH",
    }
    with pytest.raises(canary.CanaryContractError, match="CANARY_GENERATION_ATTEMPT_BUDGET_EXHAUSTED"):
        canary.validate_queued_attempt(
            item,
            {"attempts_consumed": 2, "remaining_attempts": 0, "active_attempt_index": None},
        )


def test_technical_retry_budget_reads_shared_generation_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(
        generation_attempt_authority,
        "load_asset_state",
        lambda *_a, **_k: {
            "attempts_consumed": 1,
            "remaining_attempts": 1,
            "active_attempt_index": None,
        },
    )
    ok, state, reason = image_scheduler._technical_retry_budget(
        tmp_path, {"frame": 1}, "ASPECT_RATIO_MISMATCH"
    )
    assert ok is True
    assert state["attempts_consumed"] == 1
    assert state["remaining_attempts"] == 1
    assert reason == "shared_generation_attempt_budget_available"


def test_technical_retry_budget_denies_after_attempt_two(monkeypatch, tmp_path):
    monkeypatch.setattr(
        generation_attempt_authority,
        "load_asset_state",
        lambda *_a, **_k: {
            "attempts_consumed": 2,
            "remaining_attempts": 0,
            "active_attempt_index": None,
        },
    )
    ok, state, reason = image_scheduler._technical_retry_budget(
        tmp_path, {"frame": 1}, "ASPECT_RATIO_MISMATCH"
    )
    assert ok is False
    assert state["attempts_consumed"] == 2
    assert reason == "shared_generation_attempt_budget_exhausted"


def test_retry_tech_marks_attempt_reason_and_never_grants_extra_pool(monkeypatch, tmp_path):
    queue = {
        "items": [{
            "id": "q1",
            "frame": 1,
            "kind": "original",
            "scope": "batch",
            "status": "blocked",
            "attempts": 1,
            "technical_failure_code": "ASPECT_RATIO_MISMATCH",
            "last_error": "ASPECT_RATIO_MISMATCH",
        }]
    }

    @contextlib.contextmanager
    def tx(_ep):
        yield

    monkeypatch.setattr(image_scheduler, "queue_transaction", tx)
    monkeypatch.setattr(image_scheduler, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(image_scheduler, "save_queue", lambda _ep, _q: None)
    monkeypatch.setattr(
        image_scheduler,
        "_shared_generation_attempt_state",
        lambda _ep, _item: {
            "logical_asset_key": "episode/frame-01",
            "attempts_consumed": 1,
            "remaining_attempts": 1,
            "active_attempt_index": None,
        },
    )

    result = image_scheduler.retry_tech(tmp_path, frame=1, sleep_fn=lambda _s: None)

    item = queue["items"][0]
    assert result["requeued"] == 1
    assert result["budget_authority"] == "generation_attempt_authority"
    assert result["max_real_generation_attempts"] == 2
    assert item["status"] == "queued"
    assert item["generation_attempt_reason"] == "TECHNICAL_RETRY"
    assert item["technical_retry_source_code"] == "ASPECT_RATIO_MISMATCH"
    assert item["technical_retry_shared_budget"]["remaining_before_retry"] == 1


def test_retry_tech_blocks_when_shared_attempt_two_already_used(monkeypatch, tmp_path):
    queue = {
        "items": [{
            "id": "q1",
            "frame": 1,
            "kind": "original",
            "scope": "batch",
            "status": "tech_failed",
            "attempts": 2,
            "technical_failure_code": "ASPECT_RATIO_MISMATCH",
            "last_error": "ASPECT_RATIO_MISMATCH",
        }]
    }

    @contextlib.contextmanager
    def tx(_ep):
        yield

    monkeypatch.setattr(image_scheduler, "queue_transaction", tx)
    monkeypatch.setattr(image_scheduler, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(image_scheduler, "save_queue", lambda _ep, _q: None)
    monkeypatch.setattr(
        image_scheduler,
        "_shared_generation_attempt_state",
        lambda _ep, _item: {
            "logical_asset_key": "episode/frame-01",
            "attempts_consumed": 2,
            "remaining_attempts": 0,
            "active_attempt_index": None,
        },
    )

    result = image_scheduler.retry_tech(tmp_path, frame=1, sleep_fn=lambda _s: None)

    item = queue["items"][0]
    assert result["requeued"] == 0
    assert item["status"] == "external_blocked"
    assert item["external_block"]["reason"] == "shared_generation_attempt_budget_exhausted"
