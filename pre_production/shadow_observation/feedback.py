#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisor Feedback: the human entrance for the Shadow Observation phase.

Feedback records what the creator thought of one Advisor Report. It is the only
place where a human judgement about the advisor is stored.

Frozen boundaries:
- judgement_source is always human; automated judgement is not allowed here;
- accuracy is one of four qualitative labels, never a number;
- feedback never mutates the advisor report, the Story Lock, episode state or
  story gates, and it is written only when a human runs the observe command.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ..story_dna.validator import require_valid, validate_advisor_feedback

DEFAULT_FEEDBACK_DIR = Path("reports") / "pre-production" / "advisor-feedback"
JUDGEMENT_SOURCE_HUMAN = "human"


def _stamp(created_at=None) -> str:
    return created_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def feedback_id_for(advisor_report: dict) -> str:
    return "PFB-" + str(advisor_report.get("report_id") or "unknown")


def report_sha256(advisor_report: dict) -> str:
    """Bind one feedback record to the exact advisor report revision it judges."""
    payload = json.dumps(advisor_report, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_feedback(advisor_report: dict, *, creator_decision: str = "pending",
                   advisor_accuracy: str = "unknown", confirmed_evidence=(),
                   refuted_evidence=(), missed_risks=(), notes: str = "",
                   review_reference_id: str | None = None, created_at=None) -> dict:
    """Build one Advisor Feedback record from an advisor report."""
    return {
        "schema": "advisor_feedback",
        "schema_version": 1,
        "feedback_id": feedback_id_for(advisor_report),
        "advisor_report_id": str(advisor_report.get("report_id") or ""),
        "advisor_report_sha256": report_sha256(advisor_report),
        "episode_id": str(advisor_report.get("episode_id") or ""),
        "advisor_decision": str(advisor_report.get("decision") or ""),
        "judgement_source": JUDGEMENT_SOURCE_HUMAN,
        "creator_decision": creator_decision,
        "advisor_accuracy": advisor_accuracy,
        "confirmed_evidence": [str(item) for item in confirmed_evidence],
        "refuted_evidence": [str(item) for item in refuted_evidence],
        "missed_risks": [str(item) for item in missed_risks],
        "notes": str(notes or ""),
        "review_reference_id": review_reference_id,
        "created_time": _stamp(created_at),
    }


def declared_evidence_ids(advisor_report: dict) -> set:
    """Every evidence id the report actually states (top level and inside risks)."""
    ids = {str(item) for item in (advisor_report.get("evidence") or []) if item}
    for risk in advisor_report.get("risks") or []:
        for item in (risk or {}).get("evidence") or []:
            if isinstance(item, dict) and item.get("evidence_id"):
                ids.add(str(item["evidence_id"]))
    return ids


def unknown_evidence_refs(feedback: dict, advisor_report: dict) -> list:
    """Feedback references that the advisor report does not declare (advisory warning)."""
    declared = declared_evidence_ids(advisor_report)
    refs = [str(item) for item in (feedback.get("confirmed_evidence") or [])]
    refs += [str(item) for item in (feedback.get("refuted_evidence") or [])]
    return sorted({ref for ref in refs if ref not in declared})


def save_feedback(feedback: dict, store_dir=None) -> Path:
    """Write one feedback record; re-recording the same report overwrites only that file."""
    require_valid(validate_advisor_feedback(feedback), "advisor_feedback")
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
    "JUDGEMENT_SOURCE_HUMAN",
    "build_feedback",
    "declared_evidence_ids",
    "feedback_id_for",
    "list_feedback",
    "load_feedback",
    "report_sha256",
    "save_feedback",
    "unknown_evidence_refs",
]

