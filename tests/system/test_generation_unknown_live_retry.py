from __future__ import annotations
import contextlib
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_scheduler
import runtime_executor_role


def test_direct_retry_cli_cannot_requeue_unknown_provider_attempt(monkeypatch, tmp_path):
    queue = {"items": [{
        "id": "q6", "frame": 6, "kind": "original", "scope": "batch",
        "status": "tech_failed", "attempts": 1,
        "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT",
    }]}
    @contextlib.contextmanager
    def transaction(_):
        yield
    monkeypatch.setattr(image_scheduler, "queue_transaction", transaction)
    monkeypatch.setattr(image_scheduler, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(image_scheduler, "save_queue", lambda *_a: None)
    monkeypatch.setattr(image_scheduler, "_shared_generation_attempt_state",
                        lambda *_a: {"logical_asset_key": "episode/frame-06",
                                      "attempts_consumed": 1,
                                      "remaining_attempts": 1,
                                      "active_attempt_index": None})
    monkeypatch.setattr(image_scheduler.generation_attempt_authority, "load_attempt",
                        lambda *_a: {"status": "OUTCOME_UNKNOWN"})
    result = image_scheduler.retry_tech(tmp_path, frame=6, sleep_fn=lambda _: None)
    assert result["requeued"] == 0
    assert queue["items"][0]["status"] != "queued"
    assert queue["items"][0]["external_block"]["reason"] == "previous_generation_attempt_unverified"


def test_unknown_attempt_action_has_valid_work_executor():
    import next_action
    projected = next_action.apply_runtime_block_semantics({
        "action": "VERIFY_TECHNICAL_GENERATION_EVIDENCE",
        "executor": "WORK",
        "frames": [6, 24],
        "reason": "unknown prior outcome"})
    assert runtime_executor_role.validate_action(projected) is projected
    assert projected["hard_stop"] is True
    assert projected["auto_recoverable"] is False
