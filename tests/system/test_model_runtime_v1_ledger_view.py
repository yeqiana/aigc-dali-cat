from __future__ import annotations
import sys
from pathlib import Path
import pytest
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
from model_runtime_v1 import ledger_view as ledger
B = {"role": "story.authoring", "requested_model": "model", "transport": "CODEX_NATIVE",
     "policy_sha256": "a"*64}

def test_envelope_never_claims_actual_model_or_approval():
    row = ledger.new_execution(B, input_sha256="b"*64)
    assert row["actual_model"] is None
    assert row["review_authority_granted"] is False

def test_success_requires_matching_receipt_identity():
    row = ledger.new_execution(B, input_sha256="b"*64, execution_id="ex-1")
    with pytest.raises(ValueError, match="RECEIPT_REQUIRED"):
        ledger.with_result(row, status="SUCCEEDED")
    with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
        ledger.with_result(row, status="SUCCEEDED", receipt={"receipt_id": "r", "execution_id": "wrong"})
    result = ledger.with_result(row, status="SUCCEEDED", receipt={"receipt_id": "r", "execution_id": "ex-1"})
    assert result["actual_model"] is None
    assert result["provider_receipt_id"] == "r"
    assert result["review_authority_granted"] is False

def test_unknown_outcome_requires_full_reconciliation_for_retry():
    row = ledger.with_result(ledger.new_execution(B, input_sha256="b"*64), status="INTERRUPTED_UNKNOWN")
    assert ledger.retry_decision(row)["may_retry"] is False
    assert ledger.retry_decision(row, worker_terminated=True, provider_reconciled=True)["may_retry"] is False
    assert ledger.retry_decision(row, worker_terminated=True, provider_reconciled=True, attempt_authorized=True)["may_retry"] is False

def test_terminal_immutable_and_bad_transport_denied():
    row = ledger.with_result(ledger.new_execution(B, input_sha256="b"*64), status="BLOCKED")
    with pytest.raises(ValueError, match="TERMINAL_IMMUTABLE"):
        ledger.with_result(row, status="SUCCEEDED")
    with pytest.raises(ValueError, match="MODEL_TRANSPORT_FORBIDDEN"):
        ledger.new_execution({**B, "transport": "opencodex"}, input_sha256="b"*64)

def test_provider_self_attested_model_is_not_claimed_as_actual():
    row=ledger.new_execution(B,input_sha256="b"*64,execution_id="ex")
    result=ledger.with_result(row,status="SUCCEEDED",receipt={"receipt_id":"r","execution_id":"ex",
        "actual_model_attested":"unverifiable-model"})
    assert result["actual_model"] is None

def test_boolean_retry_proofs_never_allow_duplicate_paid_attempt():
    row=ledger.with_result(ledger.new_execution(B,input_sha256="b"*64),status="INTERRUPTED_UNKNOWN")
    result=ledger.retry_decision(row,worker_terminated=True,provider_reconciled=True,attempt_authorized=True)
    assert result=={"may_retry":False,"reason":"DURABLE_ATTEMPT_AUTHORITY_REQUIRED"}
