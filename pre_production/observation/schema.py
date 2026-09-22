#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stable data contracts for the Shadow Observation module.

This module is the single source of truth for the shape of an Episode
Observation Record and an Advisor Feedback record. It defines structure and
invariants only: it never judges quality and never scores anything.

Frozen invariants (Shadow Observation phase):
- Advisor stays advisory only: ``advisory_only`` is always True and
  ``blocks_production`` is always False;
- every record is derived, never authority: ``authority`` is
  ``derived_non_authority``;
- no scoring: keys implying a score/percentage/rating are rejected;
- human feedback is human: ``judgement_source`` is always ``human``.
"""
from __future__ import annotations

from typing import Any, Iterable

from ..story_dna.schema import load_contract

OBSERVATION_CONTRACT = "episode_observation.schema.json"
FEEDBACK_CONTRACT = "advisor_feedback_model.schema.json"

AUTHORITY = "derived_non_authority"
JUDGEMENT_SOURCE_HUMAN = "human"

OBSERVATION_STATUS_OBSERVED = "OBSERVED"
OBSERVATION_STATUS_FEEDBACK_PENDING = "FEEDBACK_PENDING"
OBSERVATION_STATUS_COMPLETED = "COMPLETED"
OBSERVATION_STATUSES: tuple = tuple(load_contract(OBSERVATION_CONTRACT)["observation_statuses"])

CREATOR_DECISION_ACCEPT = "ACCEPT"
CREATOR_DECISION_REVISE = "REVISE"
CREATOR_DECISION_IGNORE = "IGNORE"
CREATOR_DECISIONS: tuple = tuple(load_contract(FEEDBACK_CONTRACT)["creator_decisions"])

RECOMMENDATION_RESULT_USEFUL = "USEFUL"
RECOMMENDATION_RESULT_PARTIAL = "PARTIAL"
RECOMMENDATION_RESULT_NOT_USEFUL = "NOT_USEFUL"
RECOMMENDATION_RESULTS: tuple = tuple(load_contract(FEEDBACK_CONTRACT)["recommendation_results"])

ADVISOR_DECISIONS: tuple = tuple(load_contract(FEEDBACK_CONTRACT)["advisor_decisions"])
JUDGEMENT_SOURCES: tuple = tuple(load_contract(FEEDBACK_CONTRACT)["judgement_sources"])


def iter_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key)
            yield from iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_keys(item)


def forbidden_key_issues(obj: Any, contract: dict, where: str) -> list[str]:
    """Keys that would imply a score/rating/percentage anywhere in the record."""
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


def validate_observation_record(record: dict) -> list[str]:
    """Validate one Episode Observation Record against its contract."""
    contract = load_contract(OBSERVATION_CONTRACT)
    where = "episode_observation"
    issues: list[str] = []
    if not isinstance(record, dict):
        return [where + ": root must be a mapping"]

    for key in contract["required"]:
        if key not in record:
            issues.append(where + ": missing required key '" + key + "'")

    issues.extend(_enum_issue(where, "observation_status", record.get("observation_status"),
                              OBSERVATION_STATUSES))
    issues.extend(_enum_issue(where, "authority", record.get("authority"),
                              tuple(contract["authority_values"])))

    for flag in contract.get("must_be_true") or ():
        if record.get(flag) is not True:
            issues.append(where + ": '" + flag + "' must stay true (advisor is advisory only)")
    for flag in contract.get("must_be_false") or ():
        if record.get(flag) is not False:
            issues.append(where + ": '" + flag + "' must stay false (never block production)")

    issues.extend(forbidden_key_issues(record, contract, where))
    return issues


def validate_feedback(record: dict) -> list[str]:
    """Validate one Advisor Feedback record against its contract."""
    contract = load_contract(FEEDBACK_CONTRACT)
    where = "advisor_feedback"
    issues: list[str] = []
    if not isinstance(record, dict):
        return [where + ": root must be a mapping"]

    for key in contract["required"]:
        if key not in record:
            issues.append(where + ": missing required key '" + key + "'")

    issues.extend(_enum_issue(where, "advisor_decision", record.get("advisor_decision"),
                              ADVISOR_DECISIONS))
    issues.extend(_enum_issue(where, "creator_decision", record.get("creator_decision"),
                              CREATOR_DECISIONS))
    issues.extend(_enum_issue(where, "recommendation_result", record.get("recommendation_result"),
                              RECOMMENDATION_RESULTS))
    issues.extend(_enum_issue(where, "judgement_source", record.get("judgement_source"),
                              JUDGEMENT_SOURCES))

    for field in contract.get("bool_fields") or ():
        if field in record and not isinstance(record[field], bool):
            issues.append(where + ": '" + field + "' must be a boolean")

    for flag in contract.get("must_be_true") or ():
        if record.get(flag) is not True:
            issues.append(where + ": '" + flag + "' must stay true (advisor is advisory only)")
    for flag in contract.get("must_be_false") or ():
        if record.get(flag) is not False:
            issues.append(where + ": '" + flag + "' must stay false (never block production)")

    issues.extend(forbidden_key_issues(record, contract, where))
    return issues


def is_valid(issues: list[str]) -> bool:
    return not issues


def require_valid(issues: list[str], where: str) -> None:
    if issues:
        raise ValueError(where + " contract violation: " + "; ".join(issues))


__all__ = [
    "ADVISOR_DECISIONS",
    "AUTHORITY",
    "CREATOR_DECISION_ACCEPT",
    "CREATOR_DECISION_IGNORE",
    "CREATOR_DECISION_REVISE",
    "CREATOR_DECISIONS",
    "FEEDBACK_CONTRACT",
    "JUDGEMENT_SOURCE_HUMAN",
    "JUDGEMENT_SOURCES",
    "OBSERVATION_CONTRACT",
    "OBSERVATION_STATUSES",
    "OBSERVATION_STATUS_COMPLETED",
    "OBSERVATION_STATUS_FEEDBACK_PENDING",
    "OBSERVATION_STATUS_OBSERVED",
    "RECOMMENDATION_RESULTS",
    "RECOMMENDATION_RESULT_NOT_USEFUL",
    "RECOMMENDATION_RESULT_PARTIAL",
    "RECOMMENDATION_RESULT_USEFUL",
    "forbidden_key_issues",
    "is_valid",
    "iter_keys",
    "require_valid",
    "validate_feedback",
    "validate_observation_record",
]

