#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract validators for Pre Production Intelligence artifacts.

Validators return a list of human-readable issues; an empty list means valid.
They never raise on malformed input and never mutate the document.
"""
from __future__ import annotations

from typing import Any

from .schema import (
    DIMENSIONS,
    FORBIDDEN_KEY_PATTERNS,
    REQUIRED_TOP_LEVEL,
    STORY_DNA_SCHEMA,
    iter_keys,
    load_contract,
    missing_subfields,
    token_set,
)


def _forbidden_key_issues(obj: Any, patterns: tuple[str, ...], where: str) -> list[str]:
    issues: list[str] = []
    for key in iter_keys(obj):
        low = key.lower()
        if any(p in low for p in patterns):
            issues.append(f"{where}: forbidden key '{key}' (no scoring is allowed)")
    return issues


def validate_dna(dna: dict) -> list[str]:
    """Validate story_fingerprint.yaml against story_dna.schema.json."""
    issues: list[str] = []
    if not isinstance(dna, dict):
        return ["story_dna: root must be a mapping"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in dna:
            issues.append(f"story_dna: missing required key '{key}'")

    for dim in DIMENSIONS:
        values = dna.get(dim)
        if values is None:
            continue
        if not isinstance(values, dict):
            issues.append(f"story_dna: '{dim}' must be a mapping")
            continue
        for sub, value in values.items():
            if isinstance(value, (list, tuple)):
                for item in value:
                    if not isinstance(item, str):
                        issues.append(f"story_dna: '{dim}.{sub}' list items must be strings")
                        break
            elif not isinstance(value, str):
                issues.append(f"story_dna: '{dim}.{sub}' must be a string or list of strings")

    for miss in missing_subfields(dna):
        issues.append(f"story_dna: subfield '{miss}' missing")

    issues.extend(_forbidden_key_issues(dna, FORBIDDEN_KEY_PATTERNS, "story_dna"))
    return issues


def validate_similarity_evidence(evidence: dict) -> list[str]:
    """Validate one Similarity Evidence record."""
    contract = load_contract("similarity_evidence.schema.json")
    issues: list[str] = []
    if not isinstance(evidence, dict):
        return ["similarity_evidence: record must be a mapping"]

    for key in contract["required"]:
        if key not in evidence:
            issues.append(f"similarity_evidence: missing required key '{key}'")

    level = evidence.get("risk_level")
    if level is not None and level not in contract["risk_levels"]:
        issues.append(f"similarity_evidence: risk_level '{level}' not in {contract['risk_levels']}")

    rtype = evidence.get("risk_type")
    if rtype is not None and rtype not in contract["risk_types"]:
        issues.append(f"similarity_evidence: risk_type '{rtype}' not in {contract['risk_types']}")

    if level == "HIGH":
        for key in contract["high_requires_non_empty"]:
            value = evidence.get(key)
            if not value:
                issues.append(f"similarity_evidence: HIGH risk requires non-empty '{key}'")

    issues.extend(_forbidden_key_issues(evidence, tuple(contract["forbidden_key_patterns"]), "similarity_evidence"))
    return issues


def validate_similarity_report(report: dict) -> list[str]:
    """Validate the similarity_report.yaml wrapper."""
    issues: list[str] = []
    if not isinstance(report, dict):
        return ["similarity_report: root must be a mapping"]
    if "current_story_id" not in report:
        issues.append("similarity_report: missing 'current_story_id'")
    evidence = report.get("evidence")
    if not isinstance(evidence, list):
        issues.append("similarity_report: 'evidence' must be a list")
        return issues
    for item in evidence:
        issues.extend(validate_similarity_evidence(item))
    return issues


def validate_advisor_report(report: dict) -> list[str]:
    """Validate advisor_report.yaml against advisor_report.schema.json."""
    contract = load_contract("advisor_report.schema.json")
    issues: list[str] = []
    if not isinstance(report, dict):
        return ["advisor_report: root must be a mapping"]

    for key in contract["required"]:
        if key not in report:
            issues.append(f"advisor_report: missing required key '{key}'")

    decision = report.get("decision")
    if decision is not None and decision not in contract["decisions"]:
        issues.append(f"advisor_report: decision '{decision}' not in {contract['decisions']}")

    confidence = report.get("confidence")
    if confidence is not None and confidence not in contract["confidence_levels"]:
        issues.append(f"advisor_report: confidence '{confidence}' not in {contract['confidence_levels']}")

    risks = report.get("risks")
    if isinstance(risks, list):
        for idx, risk in enumerate(risks):
            if not isinstance(risk, dict):
                issues.append(f"advisor_report: risks[{idx}] must be a mapping")
                continue
            for key in contract["risk_required"]:
                if key not in risk:
                    issues.append(f"advisor_report: risks[{idx}] missing '{key}'")
            if not risk.get("evidence"):
                issues.append(f"advisor_report: risks[{idx}] must carry evidence")
    elif risks is not None:
        issues.append("advisor_report: 'risks' must be a list")

    recommendations = report.get("recommendations")
    if recommendations is not None and not isinstance(recommendations, list):
        issues.append("advisor_report: 'recommendations' must be a list")

    issues.extend(_forbidden_key_issues(report, tuple(contract["forbidden_key_patterns"]), "advisor_report"))
    return issues


def validate_review_reference(ref: dict) -> list[str]:
    """Validate one Review Reference (Memory Adapter output)."""
    contract = load_contract("review_reference.schema.json")
    issues: list[str] = []
    if not isinstance(ref, dict):
        return ["review_reference: root must be a mapping"]
    for key in contract["required"]:
        if key not in ref:
            issues.append(f"review_reference: missing required key '{key}'")
    decision = ref.get("creator_decision")
    if decision is not None and decision not in contract["creator_decisions"]:
        issues.append(f"review_reference: creator_decision '{decision}' not in {contract['creator_decisions']}")
    return issues


def is_valid(issues: list[str]) -> bool:
    return not issues


def require_valid(issues: list[str], where: str) -> None:
    if issues:
        raise ValueError(f"{where} contract violation: " + "; ".join(issues))


__all__ = [
    "validate_dna",
    "validate_similarity_evidence",
    "validate_similarity_report",
    "validate_advisor_report",
    "validate_review_reference",
    "is_valid",
    "require_valid",
]

