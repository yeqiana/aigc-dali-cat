"""Read-only adapter to the existing MySQL Generation Attempt Authority.

A model envelope is not allowed to reserve or commit Attempt. A returned MySQL
row is evidence about the *existing* authority, never a second authority.
"""
from __future__ import annotations
from pathlib import Path

def inspect_attempt(ep: str | Path, logical_asset_key: str, attempt_index: int, *,
                    expected_generation_key: str, load_attempt=None) -> dict:
    if not logical_asset_key or type(attempt_index) is not int or attempt_index <= 0 or not expected_generation_key:
        raise ValueError("GENERATION_ATTEMPT_IDENTITY_INVALID")
    if load_attempt is None:
        from generation_attempt_authority import load_attempt as authoritative_load
        load_attempt=authoritative_load
    row=load_attempt(Path(ep),logical_asset_key,attempt_index)
    if row is None:
        return {"status":"MISSING","may_retry":False,"review_authority_granted":False}
    if (not isinstance(row,dict) or
        str(row.get("logical_asset_key") or "")!=logical_asset_key or
        row.get("attempt_index")!=attempt_index or
        str(row.get("generation_key") or "")!=expected_generation_key):
        return {"status":"MISMATCH","may_retry":False,"review_authority_granted":False}
    state=str(row.get("status") or "")
    if state=="RESERVED":
        reason="PRE_DISPATCH_RESERVED"
    elif state=="DISPATCH_COMMITTED":
        reason="LIVE_OR_UNKNOWN_UPSTREAM_EXECUTION"
    elif state=="OUTCOME_UNKNOWN":
        reason="MODEL_EXECUTION_NEEDS_RECONCILIATION"
    elif state=="SUCCEEDED":
        reason="ATTEMPT_SUCCEEDED_REVIEW_NOT_ATTESTED"
    elif state=="FAILED_AFTER_DISPATCH":
        reason="ATTEMPT_FAILURE_REQUIRES_NEW_AUTHORIZATION"
    else:
        reason="UNKNOWN_ATTEMPT_STATE"
    return {"status":state or "UNRECOGNIZED","reason":reason,
            "may_retry":False,"review_authority_granted":False,
            "attempt_consumed":state in {"DISPATCH_COMMITTED","OUTCOME_UNKNOWN","SUCCEEDED","FAILED_AFTER_DISPATCH"}}
