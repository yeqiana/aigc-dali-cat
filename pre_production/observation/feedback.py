#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisor Feedback Model: the human entrance of Shadow Observation.

Feedback records what a creator thought of one advisor run. It is the only
place where a human judgement about the advisor is stored.

Frozen boundaries:
- ``judgement_source`` is always ``human``: automated judgement is not allowed;
- it never edits the advisor, its rules or the Story Lock; it is only data;
- it never blocks production (``blocks_production`` stays False);
- no scoring: creator decision and recommendation result are qualitative labels.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .schema import (
    AUTHORITY,
    CREATOR_DECISIONS,
    JUDGEMENT_SOURCE_HUMAN,
    RECOMMENDATION_RESULTS,
    require_valid,
    validate_feedback,
)

DEFAULT_FEEDBACK_DIR = Path("reports") / "pre-production" / "advisor-feedback"


def _stamp(stamp: str | None = None) -> str:
    return stamp or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def report_sha256(advisor_report: dict) -> str:
    """Bind one feedback record to the exact advisor report revision it judges."""
    payload = json.dumps(advisor_report, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def feedback_id_for(advisor_report: dict) -> str:
    return "PFB-" + str(advisor_report.get("report_id") or "unknown")


def build_feedback(advisor_report: dict, *, creator_decision: str = None,
                   recommendation_result: str = None, risk_acknowledged=None,
                   revision_direction: str = "", final_effect: str = "", notes: str = "",
                   created_at=None) -> dict:
    """Build one Advisor Feedback record from an advisor report.

    ``creator_decision`` is one of ACCEPT / REVISE / IGNORE and
    ``recommendation_result`` one of USEFUL / PARTIAL / NOT_USEFUL.
    """
    record = {
        "schema": "advisor_feedback_model",
        "schema_version": 1,
        "feedback_id": feedback_id_for(advisor_report),
        "episode_id": str(advisor_report.get("episode_id") or ""),
        "advisor_report_id": str(advisor_report.get("report_id") or ""),
        "advisor_report_sha256": report_sha256(advisor_report),
        "advisor_decision": str(advisor_report.get("decision") or ""),
        "creator_decision": creator_decision,
        "recommendation_result": recommendation_result,
        "risk_acknowledged": risk_acknowledged,
        "revision_direction": str(revision_direction or ""),
        "final_effect": str(final_effect or ""),
        "notes": str(notes or ""),
        "judgement_source": JUDGEMENT_SOURCE_HUMAN,
        "created_time": _stamp(created_at),
        "advisory_only": True,
        "blocks_production": False,
        "authority": AUTHORITY,
    }
    require_valid(validate_feedback(record), "advisor_feedback")
    return record


def feedback_reference(feedback: dict) -> str:
    """Reference string used by the ledger to point at this feedback."""
    return str(feedback.get("feedback_id") or "")


def creator_decisions() -> tuple:
    return CREATOR_DECISIONS


def recommendation_results() -> tuple:
    return RECOMMENDATION_RESULTS


def save_feedback(feedback: dict, store_dir=None) -> Path:
    """Write one feedback record; re-recording the same report overwrites its file."""
    require_valid(validate_feedback(feedback), "advisor_feedback")
    base = Path(store_dir) if store_dir is not None else DEFAULT_FEEDBACK_DIR
    base.mkdir(parents=True, exist_ok=True)
    path = base / (str(feedback["feedback_id"]) + ".json")
    path.write_text(json.dumps(feedback, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return path


def load_feedback(path) -> dict | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    try:
        return json.loads(file_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def list_feedback(store_dir=None) -> list:
    base = Path(store_dir) if store_dir is not None else DEFAULT_FEEDBACK_DIR
    if not base.is_dir():
        return []
    return sorted(base.glob("*.json"))


__all__ = [
    "DEFAULT_FEEDBACK_DIR",
    "build_feedback",
    "creator_decisions",
    "feedback_id_for",
    "feedback_reference",
    "list_feedback",
    "load_feedback",
    "recommendation_results",
    "report_sha256",
    "save_feedback",
]

