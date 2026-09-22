#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Observation Feedback -> Experience Store ingestion (Experience Store Runtime MVP).

Write path::

    Episode Observation Ledger -> Advisor Feedback -> Experience Store

The converter keeps references (``observation_reference``,
``feedback_reference``, ``advisor_report_reference``) and never copies the full
advisor report or Story DNA into the store.

Boundaries:
- human triggered: nothing here runs from the Runtime;
- storage only: it does not judge, rank, score or learn;
- explicit failures: invalid input raises before anything is written, so a
  rejected ingest leaves the store untouched.
"""
from __future__ import annotations

from ..observation.schema import require_valid as require_feedback_valid
from ..observation.schema import validate_feedback
from .experience_store import (
    build_creator_decision_experience,
    build_experience_record,
    build_risk_pattern,
)


def decision_experience_from_feedback(feedback: dict) -> dict:
    """Build one Creator Decision Experience from a stored Advisor Feedback record.

    ``creator_action`` mirrors the feedback ``creator_decision`` and
    ``final_assessment`` keeps the creator's free-text final effect.
    """
    return build_creator_decision_experience(
        episode_id=str(feedback.get("episode_id") or ""),
        advisor_decision=str(feedback.get("advisor_decision") or ""),
        creator_action=str(feedback.get("creator_decision") or ""),
        recommendation_result=str(feedback.get("recommendation_result") or ""),
        final_assessment=str(feedback.get("final_effect") or feedback.get("notes") or ""),
        feedback_reference=str(feedback.get("feedback_id") or ""),
    )


def experience_from_feedback(feedback: dict, *, observation: dict | None = None,
                             story_dna_reference: str = "", production_outcome=None,
                             audience_feedback=None) -> dict:
    """Build one Episode Experience from a feedback record, keeping references only."""
    observation = observation or {}
    reference = (story_dna_reference or str(observation.get("story_dna_reference") or ""))
    return build_experience_record(
        episode_id=str(feedback.get("episode_id") or ""),
        story_dna_reference=reference,
        advisor_report_reference="advisor_report:" + str(feedback.get("advisor_report_id") or ""),
        observation_reference=str(observation.get("observation_id") or "") or None,
        feedback_reference=str(feedback.get("feedback_id") or "") or None,
        production_outcome=production_outcome,
        audience_feedback=audience_feedback,
    )


def pattern_from_evidence(evidence: dict, *, tokens=None, related_episode=None) -> dict:
    """Build one Risk Pattern from a Similarity Evidence record.

    Only the evidence id and its matched feature tokens are carried over; the
    explanation text stays in the similarity report, not in the store.
    """
    features = evidence.get("matched_features") if tokens is None else tokens
    episodes = ([str(evidence.get("related_episode_id") or "")]
                if related_episode is None else [str(item) for item in related_episode])
    return build_risk_pattern(
        risk_type=str(evidence.get("risk_type") or ""),
        pattern_description=" + ".join(str(item) for item in (features or [])),
        related_episode=episodes,
        evidence=[str(evidence.get("evidence_id") or "")],
        risk_level=evidence.get("risk_level"),
    )


def ingest_feedback(feedback: dict, *, store, observation: dict | None = None,
                    story_dna_reference: str = "", production_outcome=None,
                    audience_feedback=None, dry_run: bool = False) -> dict:
    """Persist one feedback record as a Creator Decision Experience + Episode Experience.

    Both records are validated before the first write, so an invalid feedback
    never leaves a partial record behind. Failures raise; nothing is swallowed.
    Re-running the same feedback is idempotent through duplicate protection.
    """
    require_feedback_valid(validate_feedback(feedback), "advisor_feedback")
    decision = decision_experience_from_feedback(feedback)
    experience = experience_from_feedback(feedback, observation=observation,
                                          story_dna_reference=story_dna_reference,
                                          production_outcome=production_outcome,
                                          audience_feedback=audience_feedback)

    if dry_run:
        decision_status = experience_status = "DRY_RUN"
    else:
        decision_status = store.save_creator_decision(decision)["status"]
        experience_status = store.save_experience(experience)["status"]

    return {
        "ok": True,
        "episode_id": experience["episode_id"],
        "experience_id": experience["experience_id"],
        "decision_experience_id": decision["decision_experience_id"],
        "experience_status": experience_status,
        "decision_status": decision_status,
        "observation_reference": experience["observation_reference"],
        "feedback_reference": experience["feedback_reference"],
        "advisor_report_reference": experience["advisor_report_reference"],
        "store_dir": str(store.store_dir),
        "dry_run": bool(dry_run),
        "advisory_only": True,
        "blocks_production": False,
    }


__all__ = [
    "decision_experience_from_feedback",
    "experience_from_feedback",
    "ingest_feedback",
    "pattern_from_evidence",
]
