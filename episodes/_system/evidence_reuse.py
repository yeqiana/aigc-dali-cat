"""Canonical, fail-closed fingerprints for incremental Evidence reuse.

This module is deliberately a stateless validator. Evidence files and their
existing persistence adapters remain authoritative; the fingerprint is only a
decision aid for determining whether an already verified PASS can be reused.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

FINGERPRINT_SCHEMA_VERSION = 1


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_fingerprint(
    *,
    evidence_type: str,
    source_artifact_sha: str | None,
    source_contract_sha: str | None,
    relevant_context_sha: str | None,
    bound_model_policy_sha: str | None,
    review_schema_version: str | int | None,
) -> str:
    """Hash only stable authority inputs; runtime timestamps/paths are excluded."""
    return canonical_sha256({
        "fingerprint_schema_version": FINGERPRINT_SCHEMA_VERSION,
        "evidence_type": str(evidence_type),
        "source_artifact_sha": _norm(source_artifact_sha),
        "source_contract_sha": _norm(source_contract_sha),
        "relevant_context_sha": _norm(relevant_context_sha),
        "bound_model_policy_sha": _norm(bound_model_policy_sha),
        "review_schema_version": str(review_schema_version or ""),
    })


def validate_reusable(
    evidence: Any,
    *,
    expected: dict[str, Any],
    verify_errors: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Validate a PASS payload against expected stable identity fields.

    `expected` keys use the names in compute_fingerprint, except the schema is
    named `review_schema_version`. Evidence may carry `model_policy_sha256` at
    top level or in critic provenance. Missing fields fail closed.
    """
    reasons: list[str] = []
    if not isinstance(evidence, dict):
        return {"reusable": False, "reasons": ["MISSING_EVIDENCE"], "fingerprint": None}

    schema = evidence.get("schema_version")
    want_schema = expected.get("review_schema_version")
    if str(schema or "") != str(want_schema or ""):
        reasons.append("SCHEMA_VERSION_CHANGED")

    summary = evidence.get("summary")
    if not isinstance(summary, dict) or summary.get("passed") is not True:
        reasons.append("DECISION_NOT_PASS")
    issue_codes = evidence.get("issue_codes")
    if not isinstance(issue_codes, list):
        reasons.append("ISSUE_CODES_MISSING_OR_INVALID")
    elif issue_codes:
        reasons.append("EVIDENCE_HAS_ISSUES")
    supplied_type = evidence.get("evidence_type")
    expected_type = str(expected.get("evidence_type") or "")
    if supplied_type is not None and str(supplied_type) != expected_type:
        reasons.append("EVIDENCE_TYPE_CHANGED")

    field_pairs = (
        ("source_artifact_sha", "source_artifact_sha", "SOURCE_ARTIFACT_SHA_CHANGED"),
        ("source_contract_sha", "source_contract_sha", "SOURCE_CONTRACT_SHA_CHANGED"),
        ("relevant_context_sha", "relevant_context_sha", "RELEVANT_CONTEXT_CHANGED"),
    )
    for expected_key, evidence_key, reason in field_pairs:
        wanted = _norm(expected.get(expected_key))
        got = _norm(evidence.get(evidence_key))
        if not got:
            reasons.append("EVIDENCE_IDENTITY_MISSING")
        elif got != wanted:
            reasons.append(reason)

    provenance = evidence.get("critic_provenance") or {}
    if not isinstance(provenance, dict):
        provenance = {}
        reasons.append("CRITIC_PROVENANCE_INVALID")
    top_policy = _norm(evidence.get("model_policy_sha256"))
    provenance_policy = _norm(provenance.get("model_policy_sha256"))
    if top_policy and provenance_policy and top_policy != provenance_policy:
        reasons.append("POLICY_SHA_CONFLICT")
    recorded_policy = top_policy or provenance_policy
    wanted_policy = _norm(expected.get("bound_model_policy_sha"))
    if not _norm(recorded_policy):
        reasons.append("POLICY_SHA_MISSING")
    elif _norm(recorded_policy) != wanted_policy:
        reasons.append("POLICY_SHA_CHANGED")

    if verify_errors:
        reasons.append("INVALID_EVIDENCE")

    # Keep reasons deterministic and avoid repeated explanations.
    reasons = list(dict.fromkeys(reasons))
    fingerprint = compute_fingerprint(
        evidence_type=str(expected.get("evidence_type") or ""),
        source_artifact_sha=expected.get("source_artifact_sha"),
        source_contract_sha=expected.get("source_contract_sha"),
        relevant_context_sha=expected.get("relevant_context_sha"),
        bound_model_policy_sha=expected.get("bound_model_policy_sha"),
        review_schema_version=want_schema,
    )
    return {"reusable": not reasons, "reasons": reasons, "fingerprint": fingerprint}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()
