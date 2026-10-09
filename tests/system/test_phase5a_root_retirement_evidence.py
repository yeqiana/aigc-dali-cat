"""Strict TEST_ONLY initial-epoch retirement and actual no-authority-writes semantics."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_collaborative_canary as canary


def _fixture(tmp_path, monkeypatch, *, model_receipts=(), critic=""):
    monkeypatch.setattr(canary, "ROOT", tmp_path)
    ep = tmp_path / ".codex_tmp" / "phase5a" / "original"
    (ep / "meta").mkdir(parents=True)
    (tmp_path / canary.GLOBAL_CLAIM_REL).write_text(json.dumps({
        "canary_type": canary.CANARY_TYPE,
        "canary_id": "original", "workspace": str(ep.resolve()),
    }), encoding="utf-8")
    marker = canary.workspace_marker("original")
    monkeypatch.setattr(canary, "validate_workspace", lambda *_a: (ep.resolve(), marker))
    monkeypatch.setattr(canary, "_validation_epoch_claims", lambda: [])
    monkeypatch.setattr(canary, "_model_execution_receipts", lambda _ep: list(model_receipts))
    q = {"items": [{"frame": 1, "status": "generated"}],
         "review_work_items": [{
             "review_kind": "FINAL_SEMANTIC", "review_key": "r1",
             "status": "blocked", "receipt": None,
             "technical_failure_code": "FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL",
             "recovery_action": "VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY",
         }]}
    report = ep / "meta" / "review-projection-reconciliation.json"
    report.write_text(json.dumps({
        "authority": "DIAGNOSTIC_ONLY",
        "model_dispatch_count": 0, "provider_dispatch_count": 0,
        "status": "UNVERIFIED_REVIEW_PROJECTION",
        "projections": [{"frame": "01", "errors": [
            "Final Semantic Model Execution Receipt missing"]}],
    }), encoding="utf-8")
    if critic:
        (ep / "meta" / "frame-semantic-critic-attempt-1.jsonl").write_text(
            critic, encoding="utf-8")
    return ep.resolve(), q, report


def _stub_authority(ep, queue):
    import generation_attempt_authority as attempt
    import logical_asset_identity as identity
    import scheduler_core
    import frame_semantic_review

    return (
        patch.object(identity, "frame_asset_key", return_value="asset-01"),
        patch.object(attempt, "load_asset_state",
                     return_value={"attempts_consumed": 1,
                                   "remaining_attempts": 1,
                                   "active_attempt_index": None}),
        patch.object(attempt, "load_attempt",
                     return_value={"status": "SUCCEEDED",
                                   "result_ref": "raw/01.png", "generation_key": "g1"}),
        patch.object(frame_semantic_review, "review_receipt_for_frame", return_value=None),
        patch.object(scheduler_core, "load_queue", return_value=queue),
    )


def test_initial_epoch_retirement_evidence_uses_actual_blocked_row(tmp_path, monkeypatch):
    ep, q, report = _fixture(tmp_path, monkeypatch)
    with _stub_authority(ep, q)[0], _stub_authority(ep, q)[1], \
         _stub_authority(ep, q)[2], _stub_authority(ep, q)[3], \
         _stub_authority(ep, q)[4]:
        result = canary._retirement_evidence(
            ep, "original", "REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE", report)
    assert result["attempts_consumed"] == 1
    assert result["remaining_attempts"] == 1
    assert result["review_receipt_present"] is False
    assert result["stale_review_claims"][0]["status"] == "blocked"


def test_final_semantic_model_receipt_prevents_retirement(tmp_path, monkeypatch):
    ep, q, report = _fixture(
        tmp_path, monkeypatch,
        model_receipts=[{"model_role": "vision.final", "status": "SUCCESS"}],
    )
    a, b, c, d, e = _stub_authority(ep, q)
    with a, b, c, d, e:
        with pytest.raises(canary.CanaryContractError, match="MODEL_RECEIPT_PRESENT"):
            canary._retirement_evidence(ep, "original", "UNVERIFIED_REVIEW_PROJECTION", report)


def test_completed_critic_log_is_recoverable_not_retireable(tmp_path, monkeypatch):
    ep, q, report = _fixture(
        tmp_path, monkeypatch, critic='{"type":"turn.completed"}\n')
    a, b, c, d, e = _stub_authority(ep, q)
    with a, b, c, d, e:
        with pytest.raises(canary.CanaryContractError, match="RECOVERABLE_CRITIC_TURN"):
            canary._retirement_evidence(ep, "original", "UNVERIFIED_REVIEW_PROJECTION", report)


def test_root_retirement_idempotence_preserves_original_attempt(tmp_path, monkeypatch):
    ep, q, report = _fixture(tmp_path, monkeypatch)
    a, b, c, d, e = _stub_authority(ep, q)
    with a, b, c, d, e:
        one = canary.retire_validation_epoch(
            ep, "original", retirement_reason="UNVERIFIED_REVIEW_PROJECTION",
            evidence_ref=report,
        )
        two = canary.retire_validation_epoch(
            ep, "original", retirement_reason="UNVERIFIED_REVIEW_PROJECTION",
            evidence_ref=report,
        )
    assert one == two
    assert one["retired"] is True
    assert one["validation_epoch"] == 1
    assert one["generation_dispatch_eligible"] is False
    assert one["review_dispatch_eligible"] is False
    assert one["attempts_consumed"] == 1
    assert one["remaining_attempts"] == 1
    assert one["successor_epoch_id"].startswith("phase5a-validation-e2-")
    assert (tmp_path / canary.GLOBAL_CLAIM_REL).is_file()
