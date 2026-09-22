#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Observation module (advisory only, production zero-touch).

Sub-modules:
- schema      stable contracts for the observation record and feedback;
- ledger      Episode Observation Ledger (per-episode lifecycle);
- feedback    Advisor Feedback Model (human judgement of one advisor run);
- observation Shadow Observation Runner (record an advisor run, never raise).
"""
from __future__ import annotations

from .feedback import (
    DEFAULT_FEEDBACK_DIR,
    build_feedback,
    feedback_id_for,
    feedback_reference,
    list_feedback,
    load_feedback,
    report_sha256,
    save_feedback,
)
from .ledger import (
    DEFAULT_LEDGER_PATH,
    append_record,
    build_observation,
    collapse_latest,
    complete_observation,
    find_record,
    index_by_episode,
    mark_feedback_pending,
    observation_id,
    read_records,
    scan_ledger,
    summarize,
    transition,
)
from .observation import (
    apply_feedback,
    observation_id_for,
    report_reference,
    run_observation,
    story_dna_reference,
)
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
    "DEFAULT_FEEDBACK_DIR",
    "DEFAULT_LEDGER_PATH",
    "JUDGEMENT_SOURCE_HUMAN",
    "OBSERVATION_STATUSES",
    "RECOMMENDATION_RESULTS",
    "append_record",
    "apply_feedback",
    "build_feedback",
    "build_observation",
    "collapse_latest",
    "complete_observation",
    "feedback_id_for",
    "feedback_reference",
    "find_record",
    "index_by_episode",
    "is_valid",
    "list_feedback",
    "load_feedback",
    "mark_feedback_pending",
    "observation_id",
    "observation_id_for",
    "read_records",
    "report_reference",
    "report_sha256",
    "require_valid",
    "run_observation",
    "save_feedback",
    "scan_ledger",
    "story_dna_reference",
    "summarize",
    "transition",
    "validate_feedback",
    "validate_observation_record",
]

