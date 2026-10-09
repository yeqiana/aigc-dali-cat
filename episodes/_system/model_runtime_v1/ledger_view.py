"""Non-authoritative model execution evidence envelope.

Do not replace Episode state, Generation Attempt Authority, Provider Receipt
repository or Review Authority. This structure is only a derived projection.
"""
from __future__ import annotations
import uuid

VALID_STATES = frozenset({"PLANNED", "BLOCKED", "DISPATCHED", "INTERRUPTED_UNKNOWN",
                          "SUCCEEDED", "FAILED", "RECONCILED"})
TERMINAL = frozenset({"SUCCEEDED", "FAILED", "BLOCKED"})

def new_execution(binding: dict, *, input_sha256: str, execution_id: str | None = None) -> dict:
    if (not isinstance(input_sha256, str) or len(input_sha256) != 64
        or any(c not in "0123456789abcdef" for c in input_sha256.lower())):
        raise ValueError("MODEL_EXECUTION_INPUT_SHA_INVALID")
    if binding.get("transport") not in {"CODEX_NATIVE", "API_KEY_DIRECT"}:
        raise ValueError("MODEL_TRANSPORT_FORBIDDEN")
    if not binding.get("policy_sha256") or not binding.get("requested_model") or not binding.get("role"):
        raise ValueError("MODEL_BINDING_INCOMPLETE")
    return {"schema_version": 1, "execution_id": execution_id or str(uuid.uuid4()),
            "role": binding["role"], "transport": binding["transport"],
            "requested_model": binding["requested_model"], "actual_model": None,
            "model_policy_sha256": binding["policy_sha256"], "input_sha256": input_sha256.lower(),
            "status": "PLANNED", "provider_receipt_id": None, "attempt_id": None,
            "artifact_sha256": None, "review_authority_granted": False}

def with_result(row: dict, *, status: str, receipt: dict | None = None) -> dict:
    if status not in VALID_STATES:
        raise ValueError("MODEL_EXECUTION_STATE_INVALID")
    if row.get("status") in TERMINAL and status != row["status"]:
        raise ValueError("MODEL_EXECUTION_TERMINAL_IMMUTABLE")
    if status == "SUCCEEDED":
        if not isinstance(receipt, dict) or not receipt.get("receipt_id"):
            raise ValueError("MODEL_EXECUTION_SUCCESS_RECEIPT_REQUIRED")
        if receipt.get("execution_id") != row.get("execution_id"):
            raise ValueError("MODEL_EXECUTION_RECEIPT_IDENTITY_MISMATCH")
    result = dict(row)
    result["status"] = status
    if receipt and status == "SUCCEEDED":
        result["provider_receipt_id"] = receipt["receipt_id"]
        result["actual_model"] = receipt.get("actual_model_attested") or None
        result["artifact_sha256"] = receipt.get("artifact_sha256")
    result["review_authority_granted"] = False
    return result

def retry_decision(row: dict, *, worker_terminated: bool = False,
                   provider_reconciled: bool = False,
                   attempt_authorized: bool = False) -> dict:
    if row.get("status") != "INTERRUPTED_UNKNOWN":
        return {"may_retry": False, "reason": "NOT_INTERRUPTED_UNKNOWN"}
    if not (worker_terminated and provider_reconciled and attempt_authorized):
        return {"may_retry": False, "reason": "EXECUTION_UNCERTAIN_RECONCILE_FIRST"}
    return {"may_retry": True, "reason": "EXPLICIT_ATTEMPT_AUTHORIZED"}
