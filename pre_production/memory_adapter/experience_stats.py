#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only accumulation statistics for the Experience Store.

Experience Accumulation phase: the goal is to collect real episode data and
check whether the advisor was useful, not to extend the model. This module only
tallies what is already stored and reports which documented references are
missing. It writes nothing, ranks nothing, scores nothing and decides nothing.

Boundaries:
- read only: no file in the store, the feedback directory or the observation
  ledger is opened for writing, and a missing store is reported as zeros;
- no scoring: counts and label distributions only, never a rate or a grade;
- no verdict: the documented Pattern Learning precondition is printed as the
  human's comparison, not as an automatic pass/fail;
- nothing here touches the Runtime, episode-state.json or story-gates.json.
"""
from __future__ import annotations

from pathlib import Path

from ..observation.feedback import DEFAULT_FEEDBACK_DIR, list_feedback, load_feedback
from ..observation.ledger import DEFAULT_LEDGER_PATH, read_records as read_observations
from .experience_store_jsonl import KIND_DECISION, KIND_EXPERIENCE, KIND_PATTERN

# Documented Good Experience standard (Experience Accumulation Plan 五): a
# record is complete when all four facts/references are present.
REQUIRED_EXPERIENCE_FIELDS = ("story_dna_reference", "advisor_report_reference",
                              "feedback_reference", "production_outcome")
QUALITY_STANDARD = "story_dna + advisor_report + human_feedback + production_outcome"

# Documented precondition for entering Pattern Learning (Plan 六). Recorded as a
# string so the tooling never turns it into an automatic threshold decision.
PATTERN_LEARNING_PRECONDITION = "30-50 complete Episode Experience, all with human feedback"


def _present(value) -> bool:
    """True when a reference or fact actually carries content."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if hasattr(value, "__len__"):
        return len(value) > 0
    return True


def experience_quality(record: dict) -> dict:
    """Completeness of one experience record against the documented standard."""
    missing = [field for field in REQUIRED_EXPERIENCE_FIELDS
               if not _present(record.get(field))]
    return {"complete": not missing, "missing": missing}


def _labels(values) -> dict:
    """Plain label counts; an empty label is reported as unknown."""
    counts: dict = {}
    for value in values:
        key = str(value) if value not in (None, "") else "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _episode_ids(records) -> list:
    return sorted({str(record.get("episode_id") or "") for record in records} - {""})


def feedback_stats(feedback_dir=None) -> dict:
    """Count the stored Advisor Feedback files; read-only and tolerant."""
    base = Path(feedback_dir) if feedback_dir is not None else DEFAULT_FEEDBACK_DIR
    paths = list_feedback(base)
    readable = [load_feedback(path) for path in paths]
    loaded = [item for item in readable if isinstance(item, dict)]
    return {
        "dir": str(base),
        "files": len(paths),
        "readable": len(loaded),
        "feedback_ids": sorted({str(item.get("feedback_id") or "") for item in loaded} - {""}),
        "creator_decisions": _labels(item.get("creator_decision") for item in loaded),
    }


def observation_stats(ledger_path=None) -> dict:
    """Count the Observation Ledger rows; the ledger is only read."""
    path = Path(ledger_path) if ledger_path is not None else DEFAULT_LEDGER_PATH
    records = read_observations(path)
    return {
        "ledger": str(path),
        "records": len(records),
        "with_feedback": len([row for row in records if row.get("creator_feedback_reference")]),
        "by_status": _labels(row.get("observation_status") for row in records),
    }


def collect_stats(store, *, feedback_dir=None, ledger_path=None) -> dict:
    """Accumulation statistics over one Experience Store; never writes anything."""
    experiences = store.read(KIND_EXPERIENCE)
    decisions = store.read(KIND_DECISION)
    patterns = store.read(KIND_PATTERN)

    qualities = [experience_quality(record) for record in experiences]
    complete = [record for record, quality in zip(experiences, qualities) if quality["complete"]]
    missing_counts: dict = {}
    for quality in qualities:
        for field in quality["missing"]:
            missing_counts[field] = missing_counts.get(field, 0) + 1

    feedback = feedback_stats(feedback_dir)
    observations = observation_stats(ledger_path)
    stored_feedback_ids = {str(record.get("feedback_reference") or "") for record in experiences}

    return {
        "store_dir": str(store.store_dir),
        "counts": {
            KIND_EXPERIENCE: len(experiences),
            KIND_PATTERN: len(patterns),
            KIND_DECISION: len(decisions),
        },
        "episodes": {
            "with_experience": _episode_ids(experiences),
            "with_decision": _episode_ids(decisions),
            "pattern_related_episode": _episode_ids(
                {"episode_id": item} for record in patterns
                for item in record.get("related_episode") or []),
        },
        "quality": {
            "standard": QUALITY_STANDARD,
            "complete": len(complete),
            "incomplete": len(experiences) - len(complete),
            "missing_by_field": missing_counts,
            "complete_episodes": _episode_ids(complete),
        },
        "feedback": dict(feedback,
                         referenced_by_experience=len([item for item in stored_feedback_ids
                                                       if item and item in set(feedback["feedback_ids"])])),
        "observations": observations,
        "distribution": {
            "advisor_decision": _labels(record.get("advisor_decision") for record in decisions),
            "creator_action": _labels(record.get("creator_action") for record in decisions),
            "recommendation_result": _labels(record.get("recommendation_result")
                                             for record in decisions),
            "risk_level": _labels(record.get("risk_level") for record in patterns),
            "risk_type": _labels(record.get("risk_type") for record in patterns),
        },
        "malformed": {kind: len(items) for kind, items in store.malformed().items()},
        "pattern_learning_precondition": {
            "documented": PATTERN_LEARNING_PRECONDITION,
            "complete_experiences": len(complete),
            "experiences_with_feedback_reference": len(
                [record for record in experiences if _present(record.get("feedback_reference"))]),
        },
        "authority": "derived_non_authority",
        "advisory_only": True,
        "blocks_production": False,
    }


def format_stats(payload: dict) -> list:
    """Plain read-only lines for the CLI; no rate, no grade, no verdict."""
    counts = payload["counts"]
    quality = payload["quality"]
    feedback = payload["feedback"]
    observations = payload["observations"]
    episodes = payload["episodes"]
    precondition = payload["pattern_learning_precondition"]
    malformed = sum(payload["malformed"].values())

    lines = [
        "store       : " + str(payload["store_dir"]),
        "records     : experience=" + str(counts[KIND_EXPERIENCE]) +
        " pattern=" + str(counts[KIND_PATTERN]) +
        " decision=" + str(counts[KIND_DECISION]) + " malformed_lines=" + str(malformed),
        "feedback    : files=" + str(feedback["files"]) +
        " readable=" + str(feedback["readable"]) + " dir=" + str(feedback["dir"]),
        "observation : records=" + str(observations["records"]) +
        " with_feedback=" + str(observations["with_feedback"]) +
        " ledger=" + str(observations["ledger"]),
        "episodes    : with_experience=" + str(len(episodes["with_experience"])) +
        " " + ",".join(episodes["with_experience"]),
        "quality     : standard=" + str(quality["standard"]),
        "              complete=" + str(quality["complete"]) +
        " incomplete=" + str(quality["incomplete"]) +
        " missing=" + str(quality["missing_by_field"]),
        "distribution: advisor_decision=" + str(payload["distribution"]["advisor_decision"]),
        "              creator_action=" + str(payload["distribution"]["creator_action"]),
        "              recommendation_result=" + str(payload["distribution"]["recommendation_result"]),
        "pattern goal: documented=" + str(precondition["documented"]),
        "              complete_experiences=" + str(precondition["complete_experiences"]) +
        " with_feedback_reference=" + str(precondition["experiences_with_feedback_reference"]),
        "note        : read-only statistics; counts and labels only; advisory only; "
        "blocks_production=False",
    ]
    return lines


__all__ = [
    "PATTERN_LEARNING_PRECONDITION",
    "QUALITY_STANDARD",
    "REQUIRED_EXPERIENCE_FIELDS",
    "collect_stats",
    "experience_quality",
    "feedback_stats",
    "format_stats",
    "observation_stats",
]
