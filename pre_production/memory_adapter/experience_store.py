#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre Production Experience Store interface (design phase).

This module ships the interface and the record builders of the Experience Store.
It deliberately contains no database, no retrieval algorithm and no learning.

Flow it prepares:
    Observation Ledger -> Advisor Feedback -> Experience Store   (write path)
    Story DNA -> Experience Retrieval -> Advisor Context         (read path)

Frozen boundaries:
- interface only: nothing here opens a store; a future implementation lives
  behind ExperienceStoreRepository;
- no intelligence: the read methods return candidate records, never a ranking,
  a similarity score or a decision;
- no control flow: nothing here can change the advisor, its rules, the lexicon,
  a similarity weight, episode-state.json, story-gates.json or the Runtime.

Memory provides experience; the Advisor consumes experience; neither rewrites
the other.
"""
from __future__ import annotations

import abc
import hashlib
from datetime import datetime, timezone

from .experience_schema import (
    ADVISOR_DECISIONS,
    AUTHORITY,
    CREATOR_ACTIONS,
    RECOMMENDATION_RESULTS,
    RECORD_KIND_EPISODE_EXPERIENCE,
    RISK_TYPES,
    require_valid,
    validate_creator_decision_experience,
    validate_experience_record,
    validate_risk_pattern,
)


def _stamp(stamp: str | None = None) -> str:
    return stamp or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _digest(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def experience_id(episode_id: str, anchor: str) -> str:
    """Stable id for one episode experience, anchored to the artifact it records."""
    return "EXP-" + (str(episode_id) or "unknown") + "-" + _digest(anchor)[:8]


def pattern_id(risk_type: str, signature: str) -> str:
    """Stable id for one risk pattern, anchored to its description and episodes."""
    return "PAT-" + (str(risk_type) or "unknown") + "-" + _digest(signature)[:8]


def decision_experience_id(episode_id: str, anchor: str) -> str:
    """Stable id for one creator decision experience record."""
    return "CDE-" + (str(episode_id) or "unknown") + "-" + _digest(anchor)[:8]


def build_experience_record(*, episode_id: str, story_dna_reference: str = "",
                            advisor_report_reference: str = "", observation_reference=None,
                            feedback_reference=None, production_outcome=None,
                            audience_feedback=None, created_at=None) -> dict:
    """Build one Episode Experience record (references and facts only)."""
    anchor = (feedback_reference or observation_reference or advisor_report_reference
              or story_dna_reference or episode_id)
    record = {
        "schema": "experience_record",
        "schema_version": 1,
        "experience_id": experience_id(episode_id, anchor),
        "record_kind": RECORD_KIND_EPISODE_EXPERIENCE,
        "episode_id": str(episode_id or ""),
        "story_dna_reference": str(story_dna_reference or ""),
        "advisor_report_reference": str(advisor_report_reference or ""),
        "observation_reference": observation_reference,
        "feedback_reference": feedback_reference,
        "production_outcome": production_outcome,
        "audience_feedback": audience_feedback,
        "created_time": _stamp(created_at),
        "advisory_only": True,
        "blocks_production": False,
        "authority": AUTHORITY,
    }
    require_valid(validate_experience_record(record), "experience_record")
    return record


def build_risk_pattern(*, risk_type: str, pattern_description: str, related_episode=(),
                       evidence=(), risk_level=None, created_at=None) -> dict:
    """Build one Risk Pattern record (a description of what was observed, not a rule)."""
    episodes = [str(item) for item in related_episode]
    signature = "|".join([str(pattern_description)] + sorted(episodes))
    record = {
        "schema": "risk_pattern",
        "schema_version": 1,
        "pattern_id": pattern_id(risk_type, signature),
        "risk_type": str(risk_type or ""),
        "pattern_description": str(pattern_description or ""),
        "related_episode": episodes,
        "evidence": [str(item) for item in evidence],
        "risk_level": risk_level,
        "created_time": _stamp(created_at),
        "advisory_only": True,
        "blocks_production": False,
        "authority": AUTHORITY,
    }
    require_valid(validate_risk_pattern(record), "risk_pattern")
    return record


def build_creator_decision_experience(*, episode_id: str, advisor_decision: str,
                                      creator_action: str, recommendation_result: str,
                                      final_assessment: str = "", feedback_reference=None,
                                      created_at=None) -> dict:
    """Build one Creator Decision Experience record from a human feedback outcome."""
    anchor = (feedback_reference or "|".join([str(episode_id), str(advisor_decision),
                                               str(creator_action), str(recommendation_result)]))
    record = {
        "schema": "creator_decision_experience",
        "schema_version": 1,
        "decision_experience_id": decision_experience_id(episode_id, anchor),
        "episode_id": str(episode_id or ""),
        "feedback_reference": feedback_reference,
        "advisor_decision": str(advisor_decision or ""),
        "creator_action": str(creator_action or ""),
        "recommendation_result": str(recommendation_result or ""),
        "final_assessment": str(final_assessment or ""),
        "created_time": _stamp(created_at),
        "advisory_only": True,
        "blocks_production": False,
        "authority": AUTHORITY,
    }
    require_valid(validate_creator_decision_experience(record), "creator_decision_experience")
    return record


class ExperienceStoreRepository(abc.ABC):
    """Read/write interface of the Pre Production Experience Store.

    Interface only: the design phase ships contracts, not a database. A future
    implementation (JSONL, SQLite, a service) must satisfy this interface so the
    Advisor read path never depends on the storage choice.

    Implementations must keep the boundaries: store experience, never judge a
    story, never edit a rule or a weight, never block production.
    """

    @abc.abstractmethod
    def save_experience(self, record: dict) -> dict:
        """Append one experience_record; return a save result carrying its location."""

    @abc.abstractmethod
    def get_related_experience(self, *, story_dna: dict | None = None,
                               episode_id: str | None = None,
                               limit: int | None = None) -> list:
        """Return candidate experience records related to the query.

        No ranking, no similarity score, no decision: candidates only.
        """

    @abc.abstractmethod
    def query_pattern(self, *, risk_type: str | None = None, tokens=(),
                      limit: int | None = None) -> list:
        """Return candidate risk patterns; matching semantics stay a future detail."""


__all__ = [
    "ADVISOR_DECISIONS",
    "CREATOR_ACTIONS",
    "ExperienceStoreRepository",
    "RECOMMENDATION_RESULTS",
    "RISK_TYPES",
    "build_creator_decision_experience",
    "build_experience_record",
    "build_risk_pattern",
    "decision_experience_id",
    "experience_id",
    "pattern_id",
]
