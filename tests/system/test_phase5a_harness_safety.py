from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_collaborative_canary as canary


def test_global_claim_allows_only_one_workspace_and_same_id_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "ROOT", tmp_path)
    first_id = "phase5a-singleton-one"
    first = canary.initialize_workspace(first_id)

    initial = canary.claim_global_canary(first, first_id)
    resumed = canary.claim_global_canary(first, first_id)

    assert initial["resumed"] is False
    assert resumed["resumed"] is True
    assert resumed["workspace"] == str(first.resolve())

    second_id = "phase5a-singleton-two"
    second = canary.initialize_workspace(second_id)
    try:
        canary.claim_global_canary(second, second_id)
    except canary.CanaryContractError as exc:
        assert str(exc) == "CANARY_GLOBAL_SINGLETON_ALREADY_CLAIMED"
    else:
        raise AssertionError("a second workspace must not obtain a real-canary slot")


def test_corrupt_global_claim_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "ROOT", tmp_path)
    canary_id = "phase5a-corrupt-claim"
    episode = canary.initialize_workspace(canary_id)
    claim_path = tmp_path / canary.GLOBAL_CLAIM_REL
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text("{truncated", encoding="utf-8")

    try:
        canary.claim_global_canary(episode, canary_id)
    except canary.CanaryContractError as exc:
        assert str(exc) == "CANARY_GLOBAL_CLAIM_INVALID_FAIL_CLOSED"
    else:
        raise AssertionError("a corrupt singleton claim must fail closed")


def test_original_queue_item_cannot_consume_attempt_two():
    item = {"kind": "original", "status": "queued"}
    state = {"attempts_consumed": 1, "remaining_attempts": 1,
             "active_attempt_index": None}

    try:
        canary.validate_queued_attempt(item, state)
    except canary.CanaryContractError as exc:
        assert str(exc) == "CANARY_ORIGINAL_ITEM_CANNOT_USE_ATTEMPT2"
    else:
        raise AssertionError("original queue item must not use Attempt 2")


def test_generated_original_item_remains_resumable_after_attempt_one():
    item = {"kind": "original", "status": "generated"}
    state = {"attempts_consumed": 1, "remaining_attempts": 1,
             "active_attempt_index": None}

    canary.validate_queued_attempt(item, state)


def test_model_execution_receipt_snapshot_detects_additions_and_changes(tmp_path):
    episode = tmp_path / "episode"
    receipts = episode / "meta/provider-receipts/model-executions"
    receipts.mkdir(parents=True)
    receipt_path = receipts / "call-1.json"
    receipt_path.write_text('{"call_id":"call-1"}\n', encoding="utf-8")

    before = canary._model_execution_receipt_snapshot(episode)
    assert before == canary._model_execution_receipt_snapshot(episode)

    receipt_path.write_text('{"call_id":"call-1","status":"SUCCESS"}\n', encoding="utf-8")
    after = canary._model_execution_receipt_snapshot(episode)
    assert set(after) == set(before)
    assert after != before
