"""Read-only Provider Receipt reconciliation against existing MySQL authority.

Never creates a second store, never commits Review PASS, never reserves Attempt.
"""
from __future__ import annotations

from pathlib import Path
import re

_SHA=re.compile(r"^[0-9a-f]{64}$")

def inspect_existing(ep: str | Path, legacy_receipt_path: str | Path, *,
                     expected_artifact_sha256: str,
                     expected_attempt_id: str,
                     load_receipt=None) -> dict:
    if not _SHA.fullmatch(str(expected_artifact_sha256 or "").lower()) or not expected_attempt_id:
        raise ValueError("RECEIPT_EXPECTED_IDENTITY_INVALID")
    if load_receipt is None:
        from provider_receipt_persistence import load_by_path
        load_receipt=load_by_path
    observed=load_receipt(Path(ep), legacy_receipt_path)
    if not observed:
        return {"status":"NOT_FOUND","can_finalize":False,"review_authority_granted":False}
    source=observed.get("source")
    row=observed.get("payload")
    if source != "mysql":
        return {"status":"PROVISIONAL_ONLY","reason":"NO_MYSQL_RECEIPT_AUTHORITY",
                "can_finalize":False,"review_authority_granted":False}
    if not isinstance(row, dict):
        return {"status":"INVALID","reason":"RECEIPT_PAYLOAD_INVALID",
                "can_finalize":False,"review_authority_granted":False}
    if not isinstance(observed.get("receipt_id"), str) or not observed["receipt_id"].strip():
        return {"status":"INVALID","reason":"MYSQL_RECEIPT_ID_MISSING",
                "can_finalize":False,"review_authority_granted":False}
    actual_sha=str(row.get("raw_sha256") or row.get("artifact_sha256") or "").lower()
    if (actual_sha != expected_artifact_sha256.lower()
        or str(row.get("attempt_id") or "") != str(expected_attempt_id)):
        return {"status":"MISMATCH","reason":"RECEIPT_ATTEMPT_OR_ARTIFACT_MISMATCH",
                "can_finalize":False,"review_authority_granted":False}
    return {"status":"RECEIPT_PRESENT","source":"mysql",
            "receipt_id":observed.get("receipt_id"),
            "can_finalize":False,"review_authority_granted":False,
            "next_action":"VERIFY_EXISTING_ATTEMPT_AND_REVIEW_COMMIT"}
