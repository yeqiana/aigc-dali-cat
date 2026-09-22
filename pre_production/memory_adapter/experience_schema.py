#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stable contracts for the Pre Production Experience Store.

This module defines the shape and invariants of the three experience entities
described in docs/Story_OS_PreProduction_Intelligence_Experience_Store_Integration_V1.0.md:
Episode Experience, Risk Pattern and Creator Decision Experience.

Frozen invariants (Experience Store integration design phase):
- storage only: the store keeps history, it never judges a story and never
  edits a rule, a lexicon or a similarity weight;
- every record is derived, never authority: authority is derived_non_authority;
- advisory only: advisory_only is always True and blocks_production is always False;
- no scoring: keys implying a score/percentage/threshold are rejected.
"""
from __future__ import annotations

from typing import Any

from ..story_dna.schema import iter_keys, load_contract

EXPERIENCE_CONTRACT = "experience_record.schema.json"
RISK_PATTERN_CONTRACT = "risk_pattern.schema.json"
DECISION_EXPERIENCE_CONTRACT = "creator_decision_experience.schema.json"

AUTHORITY = "derived_non_authority"
RECORD_KIND_EPISODE_EXPERIENCE = str(load_contract(EXPERIENCE_CONTRACT)["record_kind"])

RISK_TYPES: tuple = tuple(load_contract(RISK_PATTERN_CONTRACT)["risk_types"])
RISK_LEVELS: tuple = tuple(load_contract(RISK_PATTERN_CONTRACT)["risk_levels"])
ADVISOR_DECISIONS: tuple = tuple(load_contract(DECISION_EXPERIENCE_CONTRACT)["advisor_decisions"])
CREATOR_ACTIONS: tuple = tuple(load_contract(DECISION_EXPERIENCE_CONTRACT)["creator_actions"])
RECOMMENDATION_RESULTS: tuple = tuple(
    load_contract(DECISION_EXPERIENCE_CONTRACT)["recommendation_results"])


def forbidden_key_issues(obj: Any, contract: dict, where: str) -> list[str]:
    """Keys that would imply a score/rating/percentage/threshold anywhere."""
    patterns = tuple(contract.get("forbidden_key_patterns") or ())
    issues: list[str] = []
    for key in iter_keys(obj):
        low = key.lower()
        if any(pattern in low for pattern in patterns):
            issues.append(where + ": forbidden key '" + key + "' (no scoring is allowed)")
    return issues


def _enum_issue(where: str, field: str, value: Any, allowed: tuple) -> list[str]:
    if value is None:
        return []
    if value not in allowed:
        return [where + ": '" + field + "' value '" + str(value) + "' not in " + str(list(allowed))]
    return []


def _empty_issue(where: str, field: str, value: Any) -> list[str]:
    if value is None or (hasattr(value, "__len__") and len(value) == 0):
        return [where + ": '" + field + "' must not be empty"]
    return []


def _validate_common(record: dict, contract: dict, where: str,
                     enums: dict | None = None) -> list[str]:
    issues: list[str] = []
    if not isinstance(record, dict):
        return [where + ": root must be a mapping"]

    for key in contract["required"]:
        if key not in record:
            issues.append(where + ": missing required key '" + key + "'")

    for key in contract.get("non_empty_required") or ():
        if key in record:
            issues.extend(_empty_issue(where, key, record.get(key)))

    for field, allowed in (enums or {}).items():
        issues.extend(_enum_issue(where, field, record.get(field), allowed))

    authority_values = tuple(contract.get("authority_values") or ())
    issues.extend(_enum_issue(where, "authority", record.get("authority"), authority_values))

    for flag in contract.get("must_be_true") or ():
        if record.get(flag) is not True:
            issues.append(where + ": '" + flag + "' must stay true (advisory only)")
    for flag in contract.get("must_be_false") or ():
        if record.get(flag) is not False:
            issues.append(where + ": '" + flag + "' must stay false (never block production)")

    issues.extend(forbidden_key_issues(record, contract, where))
    return issues


def validate_experience_record(record: dict) -> list[str]:
    """Validate one Episode Experience record against its contract."""
    contract = load_contract(EXPERIENCE_CONTRACT)
    return _validate_common(record, contract, "experience_record")


def validate_risk_pattern(record: dict) -> list[str]:
    """Validate one Risk Pattern record against its contract."""
    contract = load_contract(RISK_PATTERN_CONTRACT)
    return _validate_common(record, contract, "risk_pattern",
                            enums={"risk_type": RISK_TYPES, "risk_level": RISK_LEVELS})


def validate_creator_decision_experience(record: dict) -> list[str]:
    """Validate one Creator Decision Experience record against its contract."""
    contract = load_contract(DECISION_EXPERIENCE_CONTRACT)
    return _validate_common(record, contract, "creator_decision_experience",
                            enums={"advisor_decision": ADVISOR_DECISIONS,
                                   "creator_action": CREATOR_ACTIONS,
                                   "recommendation_result": RECOMMENDATION_RESULTS})


def is_valid(issues: list[str]) -> bool:
    return not issues


def require_valid(issues: list[str], where: str) -> None:
    if issues:
        raise ValueError(where + " contract violation: " + "; ".join(issues))


__all__ = [
    "ADVISOR_DECISIONS",
    "AUTHORITY",
    "CREATOR_ACTIONS",
    "DECISION_EXPERIENCE_CONTRACT",
    "EXPERIENCE_CONTRACT",
    "RECOMMENDATION_RESULTS",
    "RECORD_KIND_EPISODE_EXPERIENCE",
    "RISK_LEVELS",
    "RISK_PATTERN_CONTRACT",
    "RISK_TYPES",
    "forbidden_key_issues",
    "is_valid",
    "require_valid",
    "validate_creator_decision_experience",
    "validate_experience_record",
    "validate_risk_pattern",
]
