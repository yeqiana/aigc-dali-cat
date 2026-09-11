#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memory Adapter: read historical experience, persist Review References.

It also carries the Experience Store interface (design phase): contracts and
signatures only, behind which a future store implementation will sit.
"""
from __future__ import annotations

from .adapter import DEFAULT_STORE_DIR, MemoryAdapter
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

__all__ = [
    "ADVISOR_DECISIONS",
    "AUTHORITY",
    "CREATOR_ACTIONS",
    "DEFAULT_STORE_DIR",
    "ExperienceStoreRepository",
    "MemoryAdapter",
    "RECOMMENDATION_RESULTS",
    "RISK_LEVELS",
    "RISK_TYPES",
    "build_creator_decision_experience",
    "build_experience_record",
    "build_risk_pattern",
    "validate_creator_decision_experience",
    "validate_experience_record",
    "validate_risk_pattern",
]
