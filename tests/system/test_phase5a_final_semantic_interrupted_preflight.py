"""A generated Phase5A image does not prove an interrupted semantic call ended."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_collaborative_canary as canary


def _queue(*, kind="FINAL_SEMANTIC", status="blocked",
           key="generation-a", receipt=None, code="FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL"):
    return {"review_work_items": [{
        "review_kind": kind,
        "status": status,
        "generation_key": key,
        "technical_failure_code": code,
        "receipt": receipt,
    }]}


def test_interrupted_unreceipted_final_semantic_fails_closed():
    with pytest.raises(canary.CanaryContractError, match="CANARY_FINAL_SEMANTIC_EXECUTION_UNVERIFIED"):
        canary._assert_final_semantic_recovery_safe(
            _queue(), {"generation_key": "generation-a"})


def test_other_blocked_semantic_is_not_advertised_ready():
    with pytest.raises(canary.CanaryContractError, match="CANARY_FINAL_SEMANTIC_BLOCKED_REQUIRES_RECOVERY"):
        canary._assert_final_semantic_recovery_safe(
            _queue(code="REVIEW_POLICY_NOT_READY"),
            {"generation_key": "generation-a"})


def test_finalized_with_receipt_passes_specific_interruption_gate():
    canary._assert_final_semantic_recovery_safe(
        _queue(status="finalized", receipt={"review_outcome": "PASS"}, code=None),
        {"generation_key": "generation-a"})


def test_unrelated_generation_key_does_not_block_our_canary():
    canary._assert_final_semantic_recovery_safe(
        _queue(key="other-generation"), {"generation_key": "generation-a"})


def test_unrelated_fast_scout_does_not_block_final_semantic():
    canary._assert_final_semantic_recovery_safe(
        _queue(kind="FAST_SCOUT"), {"generation_key": "generation-a"})


def test_reconciled_queued_review_is_left_to_scheduler_authority():
    canary._assert_final_semantic_recovery_safe(
        _queue(status="queued", code=None), {"generation_key": "generation-a"})
