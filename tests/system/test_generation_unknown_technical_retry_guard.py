from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_scheduler
import next_action
import generation_attempt_authority


def _item():
    return {"frame": 6, "status": "tech_failed",
            "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT"}


def _state():
    return {"logical_asset_key": "episode/frame-06",
            "attempts_consumed": 1, "remaining_attempts": 1,
            "active_attempt_index": None}


def test_outcome_unknown_never_automatically_requeues():
    with (patch.object(image_scheduler, "_shared_generation_attempt_state",
                       return_value=_state()),
          patch.object(image_scheduler.generation_attempt_authority, "load_attempt",
                       return_value={"status": "OUTCOME_UNKNOWN"})):
        allowed, state, reason = image_scheduler._technical_retry_budget(
            Path("episode"), _item(), "IMAGE_TOOL_NO_ARTIFACT")
    assert allowed is False
    assert reason == "previous_generation_attempt_unverified"
    assert state["remaining_attempts"] == 1


def test_only_verified_failed_after_dispatch_can_retry():
    with (patch.object(image_scheduler, "_shared_generation_attempt_state",
                       return_value=_state()),
          patch.object(image_scheduler.generation_attempt_authority, "load_attempt",
                       return_value={"status": "FAILED_AFTER_DISPATCH"})):
        allowed, _, reason = image_scheduler._technical_retry_budget(
            Path("episode"), _item(), "IMAGE_TOOL_NO_ARTIFACT")
    assert allowed is True
    assert reason == "shared_generation_attempt_budget_available"


def test_succeeded_previous_attempt_requires_reconciliation():
    with (patch.object(image_scheduler, "_shared_generation_attempt_state",
                       return_value=_state()),
          patch.object(image_scheduler.generation_attempt_authority, "load_attempt",
                       return_value={"status": "SUCCEEDED"})):
        allowed, _, reason = image_scheduler._technical_retry_budget(
            Path("episode"), _item(), "IMAGE_TOOL_NO_ARTIFACT")
    assert allowed is False
    assert reason == "previous_generation_attempt_reconciliation_required"


def test_missing_attempt_receipt_fails_closed():
    with (patch.object(image_scheduler, "_shared_generation_attempt_state",
                       return_value=_state()),
          patch.object(image_scheduler.generation_attempt_authority, "load_attempt",
                       return_value=None)):
        allowed, _, reason = image_scheduler._technical_retry_budget(
            Path("episode"), _item(), "IMAGE_TOOL_NO_ARTIFACT")
    assert allowed is False
    assert reason == "previous_generation_attempt_missing"


def test_next_action_does_not_advertise_automatic_unknown_retry():
    q = {"items": [_item(), {"frame": 24, "status": "tech_failed",
                             "technical_failure_code": "ASPECT_RATIO_MISMATCH"},
                   {"frame": 5, "status": "generated"}]}
    with patch.object(image_scheduler, "_technical_retry_budget",
                      return_value=(False, _state(),
                                    "previous_generation_attempt_unverified")):
        projected = next_action._technical_generation_evidence_action(Path("episode"), q)
    assert projected is not None
    assert projected["action"] == "VERIFY_TECHNICAL_GENERATION_EVIDENCE"
    assert projected["frames"] == [6, 24]
    assert projected["executor"] == "WORK"
    semantics = next_action.apply_runtime_block_semantics(dict(projected))
    assert semantics["hard_stop"] is True
    assert semantics["auto_recoverable"] is False


def test_native_dispatch_is_preserved_when_previous_failure_is_proven():
    q = {"items": [_item()]}
    with patch.object(image_scheduler, "_technical_retry_budget",
                      return_value=(True, _state(),
                                    "shared_generation_attempt_budget_available")):
        assert next_action._technical_generation_evidence_action(Path("episode"), q) is None


def test_failure_before_first_attempt_is_not_counted_as_repeat():
    state = {**_state(), "attempts_consumed": 0, "remaining_attempts": 2}
    with (patch.object(image_scheduler, "_shared_generation_attempt_state",
                       return_value=state),
          patch.object(image_scheduler.generation_attempt_authority,
                       "load_attempt") as reader):
        allowed, _, reason = image_scheduler._technical_retry_budget(
            Path("episode"), _item(), "IMAGE_TOOL_NO_ARTIFACT")
    assert allowed is True
    reader.assert_not_called()
    assert reason == "shared_generation_attempt_budget_available"


class _PriorAttemptConnection:
    def __init__(self, status):
        self.status = status
        self.calls = []

    def query_one(self, sql, params):
        self.calls.append((sql, params))
        return {"STATUS": self.status} if self.status is not None else None


def test_mysql_attempt_authority_blocks_next_reservation_after_unknown():
    connection = _PriorAttemptConnection("OUTCOME_UNKNOWN")
    reason = generation_attempt_authority._previous_attempt_denial(
        connection, "episode", "episode/frame-06", 1)
    assert reason == "GENERATION_ATTEMPT_OUTCOME_UNKNOWN_RECONCILIATION_REQUIRED"
    assert "FOR UPDATE" in connection.calls[0][0]


def test_mysql_attempt_authority_allows_only_verified_terminal_history():
    for status in ("SUCCEEDED", "FAILED_AFTER_DISPATCH"):
        assert generation_attempt_authority._previous_attempt_denial(
            _PriorAttemptConnection(status), "episode", "episode/frame-01", 1) is None
    assert generation_attempt_authority._previous_attempt_denial(
        _PriorAttemptConnection(None), "episode", "episode/frame-01", 1
    ) == "GENERATION_ATTEMPT_PREVIOUS_HISTORY_MISSING"
    assert generation_attempt_authority._previous_attempt_denial(
        _PriorAttemptConnection("DISPATCH_COMMITTED"), "episode", "episode/frame-01", 1
    ) == "GENERATION_ATTEMPT_PREVIOUS_STATUS_UNRECONCILED"
