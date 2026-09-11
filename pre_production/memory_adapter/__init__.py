#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memory Adapter: read historical experience, persist Review References.

It also carries the Experience Store interface (design phase): contracts and
signatures, plus the JSONL-backed runtime store behind it.
"""
from __future__ import annotations

from .adapter import DEFAULT_STORE_DIR, MemoryAdapter
from .experience_ingest import (
    decision_experience_from_feedback,
    experience_from_feedback,
    ingest_feedback,
    pattern_from_evidence,
)
from .experience_schema import (
    ADVISOR_DECISIONS,
    AUTHORITY,
    CREATOR_ACTIONS,
    RECOMMENDATION_RESULTS,
    RISK_LEVELS,
    RISK_TYPES,
    validate_creator_decision_experience,
    validate_experience_record,
    validate_risk_pattern,
)
from .experience_store import (
    ExperienceStoreRepository,
    build_creator_decision_experience,
    build_experience_record,
    build_risk_pattern,
)
from .experience_store_jsonl import (
    DECISION_FILE,
    EXPERIENCE_FILE,
    JsonlExperienceStore,
    KIND_DECISION,
    KIND_EXPERIENCE,
    KIND_PATTERN,
    KINDS,
    PATTERN_FILE,
)

__all__ = [
    "ADVISOR_DECISIONS",
    "AUTHORITY",
    "CREATOR_ACTIONS",
    "DEFAULT_STORE_DIR",
    "DECISION_FILE",
    "ExperienceStoreRepository",
    "EXPERIENCE_FILE",
    "JsonlExperienceStore",
    "KIND_DECISION",
    "KIND_EXPERIENCE",
    "KIND_PATTERN",
    "KINDS",
    "MemoryAdapter",
    "PATTERN_FILE",
    "RECOMMENDATION_RESULTS",
    "RISK_LEVELS",
    "RISK_TYPES",
    "build_creator_decision_experience",
    "build_experience_record",
    "build_risk_pattern",
    "decision_experience_from_feedback",
    "experience_from_feedback",
    "ingest_feedback",
    "pattern_from_evidence",
    "validate_creator_decision_experience",
    "validate_experience_record",
    "validate_risk_pattern",
]
