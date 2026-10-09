"""Retirement of a non-promotable initial Canary without falsifying its image Attempt."""
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


def _root_claim(tmp_path, canary_id="original") -> Path:
    ep = tmp_path / ".codex_tmp" / "phase5a" / canary_id
    ep.mkdir(parents=True)
    f = tmp_path / canary.GLOBAL_CLAIM_REL
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({
        "canary_type": canary.CANARY_TYPE,
        "canary_id": canary_id, "workspace": str(ep.resolve()),
    }), encoding="utf-8")
    return ep.resolve()


def _blocked(**overrides):
    return {
        "review_key": "legacy-final-1", "review_kind": "FINAL_SEMANTIC",
        "status": "blocked",
        "technical_failure_code": "FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL",
        "recovery_action": "VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY",
        "runner_request_id": None,
        "receipt": None,
        **overrides,
    }


def test_original_root_can_be_retirement_source_only_with_exact_global_claim(tmp_path):
    ep = _root_claim(tmp_path)
    with (
        patch.object(canary, "ROOT", tmp_path),
        patch.object(canary, "_validation_epoch_claims", return_value=[]),
    ):
        record = canary._retirement_source_claim(ep, "original")
        assert record["validation_epoch"] == 1
        assert record["_epoch_index"] == 1
        assert record["workspace"] == str(ep)
        with pytest.raises(canary.CanaryContractError, match="EPOCH_CLAIM_REQUIRED"):
            canary._retirement_source_claim(ep, "wrong-id")


def test_original_root_cannot_retire_around_replacement_claim(tmp_path):
    ep = _root_claim(tmp_path)
    replacement = tmp_path / canary.REPLACEMENT_CLAIM_REL
    replacement.write_text("{}", encoding="utf-8")
    with (
        patch.object(canary, "ROOT", tmp_path),
        patch.object(canary, "_validation_epoch_claims", return_value=[]),
    ):
        with pytest.raises(canary.CanaryContractError, match="NOT_LATEST_EPOCH"):
            canary._retirement_source_claim(ep, "original")


def test_older_source_cannot_retire_around_newer_epoch(tmp_path):
    ep = _root_claim(tmp_path)
    with (
        patch.object(canary, "ROOT", tmp_path),
        patch.object(canary, "_validation_epoch_claims", return_value=[
            {"canary_id": "e2", "workspace": str(tmp_path / "e2"), "_epoch_index": 2}
        ]),
    ):
        with pytest.raises(canary.CanaryContractError, match="NOT_LATEST_EPOCH"):
            canary._retirement_source_claim(ep, "original")


def test_unverified_blocked_review_qualifies_for_further_evidence_check():
    rows = canary._assert_review_queue_not_recoverable(
        {"items": [{"frame": 1, "status": "generated"}],
         "review_work_items": [_blocked()]})
    assert len(rows) == 1
    assert rows[0]["status"] == "blocked"
    assert rows[0]["runner_request_bound"] is False
    assert rows[0]["result_receipt_present"] is False


@pytest.mark.parametrize("mutation", [
    {"runner_request_id": "f" * 32},
    {"receipt": {"status": "SUCCESS"}},
    {"technical_failure_code": "OTHER_ERROR"},
    {"recovery_action": "RETRY_NOW"},
    {"review_kind": "FAST_SCOUT"},
    {"status": "queued"},
])
def test_blocked_review_with_recoverable_or_ambiguous_evidence_is_denied(mutation):
    with pytest.raises(canary.CanaryContractError):
        canary._assert_review_queue_not_recoverable({
            "items": [{"frame": 1, "status": "generated"}],
            "review_work_items": [_blocked(**mutation)]})


def test_root_retirement_needs_explicit_successor_authorization(tmp_path):
    old = _root_claim(tmp_path)
    new = tmp_path / ".codex_tmp" / "phase5a" / "successor"
    new.mkdir(parents=True)
    with (
        patch.object(canary, "ROOT", tmp_path),
        patch.object(canary, "_validation_epoch_claims", return_value=[]),
        patch.object(canary, "_read_retirement", return_value={
            "validation_epoch": 1, "successor_epoch_id": "successor",
        }),
        patch.object(canary, "_claim_validation_epoch",
                     return_value={"canary_id": "successor", "validation_epoch": 2}) as claim,
        patch.object(canary, "validate_workspace",
                     side_effect=lambda ep, cid: (Path(ep).resolve(), {})),
        patch.object(canary, "_replacement_source_evidence") as prohibited,
    ):
        with pytest.raises(canary.CanaryContractError, match="EXPLICIT_AUTHORIZATION_REQUIRED"):
            canary.claim_global_canary(new, "successor")
        result = canary.claim_global_canary(
            new, "successor", allow_validation_epoch=True)
    assert result["validation_epoch"] == 2
    claim.assert_called_once()
    assert claim.call_args.kwargs["previous_claim"]["_epoch_index"] == 1
    prohibited.assert_not_called()
