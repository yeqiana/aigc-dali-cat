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
    monkeypatch.setattr(
        canary,
        "_replacement_source_evidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            canary.CanaryContractError("CANARY_REPLACEMENT_SOURCE_ATTEMPT_COUNT_INVALID")
        ),
    )
    try:
        canary.claim_global_canary(second, second_id)
    except canary.CanaryContractError as exc:
        assert str(exc) == "CANARY_REPLACEMENT_SOURCE_ATTEMPT_COUNT_INVALID"
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


def test_subscription_canary_claim_precedes_unknown_capability_preflight(monkeypatch):
    import codex_subscription_image
    import image_payload_transport
    import model_policy

    episode = Path("phase5a-test-workspace")
    order = []
    preflight = {
        "episode": episode,
        "episode_path": str(episode.resolve()),
        "canary_id": "phase5a-test-canary",
        "logical_asset_key": "_external/test/frame-01",
        "policy_sha256": "a" * 64,
        "runtime_request_id": "req-test",
    }
    monkeypatch.setattr(canary, "_preflight", lambda *_args: preflight)
    monkeypatch.setattr(
        canary, "claim_global_canary",
        lambda *_args, **_kwargs: order.append("claim") or {"canary_id": preflight["canary_id"]},
    )
    monkeypatch.setattr(image_payload_transport, "selected_route",
                        lambda *_args: {"provider": "codex_subscription"})
    monkeypatch.setattr(model_policy, "resolve",
                        lambda *_args, **_kwargs: {"model": "gpt-image-2.5-flare", "quality": "high"})

    def blocked_probe(**_kwargs):
        assert order == ["claim"]
        return {
            "status": "BLOCKED",
            "failure_class": "LOGIN_AUTH_IMAGE_TOOL_CAPABILITY_UNKNOWN",
            "image_attempt_authority_called": False,
            "image_generation_called": False,
        }

    monkeypatch.setattr(codex_subscription_image, "payload_capability_preflight", blocked_probe)
    monkeypatch.setattr(canary, "_telemetry", lambda *_args, **_kwargs: None)

    result = canary.run_production_subpath(episode, canary_id=preflight["canary_id"])

    assert result["status"] == "CANARY_PAYLOAD_PREFLIGHT_BLOCKED"
    assert order == ["claim"]
    assert result["image_attempt_reserve_called"] is False
    assert result["image_scheduler_called"] is False
