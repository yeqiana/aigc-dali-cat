#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Observation module (advisory only, production zero-touch).

Sub-modules:
- ``schema``      stable contracts for the observation record and feedback;
- ``ledger``      Episode Observation Ledger (per-episode lifecycle);
- ``feedback``    Advisor Feedback Model (human judgement of one advisor run);
- ``observation`` Shadow Observation Runner (record an advisor run, never raise).
"""
from __future__ import annotations

from .schema import (
    ADVISOR_DECISIONS,
    AUTHORITY,
    CREATOR_DECISIONS,
    JUDGEMENT_SOURCE_HUMAN,
    OBSERVATION_STATUSES,
    RECOMMENDATION_RESULTS,
    is_valid,
    require_valid,
    validate_feedback,
    validate_observation_record,
)

__all__ = [
    "ADVISOR_DECISIONS",
    "AUTHORITY",
    "CREATOR_DECISIONS",
    "JUDGEMENT_SOURCE_HUMAN",
    "OBSERVATION_STATUSES",
    "RECOMMENDATION_RESULTS",
    "is_valid",
    "require_valid",
    "validate_feedback",
    "validate_observation_record",
]

