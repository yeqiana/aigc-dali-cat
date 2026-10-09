"""Read-only correlation of the *existing* Attempt and Provider Receipt authorities.

Even if both match, only existing Review Authority may approve the frame.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .attempt_reconciliation import inspect_attempt
from .receipt_reconciliation import inspect_existing

def correlate_image_evidence(ep, *, logical_asset_key: str, attempt_index: int,
                             generation_key: str, attempt_id: str,
                             artifact_sha256: str, legacy_receipt_path,
                             expected_transport_route: str | None = None,
                             artifact_path=None, load_attempt=None, load_receipt=None) -> dict:
    attempt = inspect_attempt(
        ep, logical_asset_key, attempt_index,
        expected_generation_key=generation_key, load_attempt=load_attempt
    )
    if attempt["status"] != "SUCCEEDED":
        return {"status": "ATTEMPT_NOT_VERIFIED", "attempt_state": attempt["status"],
                "may_retry": False, "may_publish": False, "review_authority_granted": False}
    receipt = inspect_existing(
        ep, legacy_receipt_path, expected_artifact_sha256=artifact_sha256,
        expected_attempt_id=attempt_id, expected_transport_route=expected_transport_route,
        load_receipt=load_receipt
    )
    if receipt["status"] != "RECEIPT_PRESENT":
        return {"status": "RECEIPT_NOT_VERIFIED", "receipt_state": receipt["status"],
                "may_retry": False, "may_publish": False, "review_authority_granted": False}
    observed_sha=None
    if artifact_path is not None:
        try:
            episode_root=Path(ep).resolve(strict=True)
            candidate=Path(artifact_path)
            actual_path=(candidate if candidate.is_absolute() else episode_root/candidate).resolve(strict=True)
            if not actual_path.is_relative_to(episode_root) or not actual_path.is_file():
                raise ValueError("ARTIFACT_PATH_OUTSIDE_EPISODE")
            digest=hashlib.sha256()
            with actual_path.open("rb") as file:
                for chunk in iter(lambda:file.read(1024*1024),b""):
                    digest.update(chunk)
            observed_sha=digest.hexdigest()
            if observed_sha!=artifact_sha256.lower():
                raise ValueError("ARTIFACT_SHA_MISMATCH")
        except (OSError,ValueError):
            return {"status":"ARTIFACT_NOT_VERIFIED","may_retry":False,
                    "may_publish":False,"review_authority_granted":False}
    return {"status": "ATTEMPT_AND_RECEIPT_RECONCILED",
            "receipt_id": receipt["receipt_id"],
            "artifact_observed_sha256":observed_sha,
            "may_retry": False, "may_publish": False, "review_authority_granted": False,
            "next_action": "VERIFY_EXISTING_FINAL_SEMANTIC_REVIEW_AUTHORITY"}
