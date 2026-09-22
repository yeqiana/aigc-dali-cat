#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Observation Runner.

Flow: Advisor Report -> create the observation ledger row -> wait for feedback
-> update the observation. The runner is the only automated entry point of the
Shadow Observation phase and a human invokes it.

Frozen boundaries:
- the runner never runs as part of the production Runtime and never modifies the
  advisor, the Story Lock, meta/episode-state.json or meta/story-gates.json;
- it never raises: every failure is returned as data with
  blocks_production=False, so an advisor/observation failure can never break the
  production flow;
- lifecycle is forward-only: OBSERVED -> FEEDBACK_PENDING -> COMPLETED.
"""
from __future__ import annotations

import traceback
from pathlib import Path

from .feedback import DEFAULT_FEEDBACK_DIR, feedback_id_for, feedback_reference, load_feedback
from .ledger import (
    DEFAULT_LEDGER_PATH,
    append_record,
    build_observation,
    complete_observation,
    find_record,
    mark_feedback_pending,
    observation_id as ledger_observation_id,
)
from .schema import (
    OBSERVATION_STATUS_COMPLETED,
    OBSERVATION_STATUS_FEEDBACK_PENDING,
    OBSERVATION_STATUS_OBSERVED,
)


def report_reference(advisor_report: dict) -> str:
    """Stable reference string for one advisor report revision."""
    return "advisor_report:" + str(advisor_report.get("report_id") or "unknown")


def story_dna_reference(advisor_report: dict) -> str:
    """Reference to the Story DNA the advisor report was built from."""
    source = advisor_report.get("source") or {}
    sha = str(source.get("story_lock_sha256") or "")
    story = str(advisor_report.get("story_id") or "")
    return "story_dna:" + story + "@" + (sha[:8] or "nohash")


def observation_id_for(advisor_report: dict) -> str:
    """Ledger observation id for one advisor report revision."""
    return ledger_observation_id(advisor_report.get("episode_id") or "",
                                 report_reference(advisor_report))


def _resolve_report(episode_dir, advisor_report, repo_root, history_paths, history_limit):
    """Return (advisor_report, story_dna_reference) without touching the advisor."""
    if advisor_report is not None:
        report = dict(advisor_report)
        return report, story_dna_reference(report)
    if episode_dir is None:
        raise ValueError("provide advisor_report or episode_dir")
    from ..shadow_mode import analyze_episode
    analyzed = analyze_episode(episode_dir, repo_root=repo_root,
                               history_paths=tuple(history_paths or ()),
                               history_limit=history_limit)
    report = analyzed["advisor_report"]
    return report, story_dna_reference(report)


def _feedback_for(advisor_report, feedback_store):
    base = Path(feedback_store) if feedback_store is not None else DEFAULT_FEEDBACK_DIR
    return load_feedback(base / (feedback_id_for(advisor_report) + ".json"))


def run_observation(episode_dir=None, *, advisor_report=None, ledger=None, repo_root=None,
                    history_paths=(), history_limit=None, feedback_store=None,
                    production_outcome=None, learning_summary=None, dry_run=False) -> dict:
    """Record one advisor run in the observation ledger and sync its lifecycle.

    Never raises: a failure is an ok=False payload with blocks_production=False.
    Re-running is idempotent and forward-only.
    """
    ledger_path = Path(ledger) if ledger is not None else DEFAULT_LEDGER_PATH
    try:
        report, dna_reference = _resolve_report(episode_dir, advisor_report, repo_root,
                                                history_paths, history_limit)
        oid = observation_id_for(report)
        feedback = _feedback_for(report, feedback_store)
        payload = {
            "ok": True,
            "observation_id": oid,
            "episode_id": str(report.get("episode_id") or ""),
            "advisor_decision": str(report.get("decision") or ""),
            "observation_status": OBSERVATION_STATUS_OBSERVED,
            "ledger": str(ledger_path),
            "feedback_reference": feedback_reference(feedback) if feedback else None,
            "blocks_production": False,
            "advisory_only": True,
            "errors": [],
        }
        if dry_run:
            payload["observation_status"] = (OBSERVATION_STATUS_COMPLETED if feedback
                                             else OBSERVATION_STATUS_FEEDBACK_PENDING)
            return payload

        if find_record(ledger_path, oid) is None:
            append_record(ledger_path, build_observation(
                payload["episode_id"], story_dna_reference=dna_reference,
                advisor_report_reference=report_reference(report)))

        if feedback is not None:
            current = find_record(ledger_path, oid)
            if str(current.get("observation_status")) != OBSERVATION_STATUS_COMPLETED:
                complete_observation(ledger_path, oid,
                                     creator_feedback_reference=feedback_reference(feedback),
                                     production_outcome=production_outcome,
                                     learning_summary=learning_summary if learning_summary is not None else "")
        elif str(find_record(ledger_path, oid).get("observation_status")) == OBSERVATION_STATUS_OBSERVED:
            mark_feedback_pending(ledger_path, oid)

        payload["observation_status"] = str(find_record(ledger_path, oid).get("observation_status"))
        return payload
    except Exception as exc:  # the observation must never break anything
        return {
            "ok": False,
            "observation_id": None,
            "episode_id": None,
            "advisor_decision": None,
            "observation_status": None,
            "ledger": str(ledger_path),
            "feedback_reference": None,
            "blocks_production": False,
            "advisory_only": True,
            "errors": [type(exc).__name__ + ": " + str(exc)],
            "traceback": traceback.format_exc(),
        }


def apply_feedback(feedback: dict, *, ledger=None, production_outcome=None,
                   learning_summary=None, dry_run=False) -> dict:
    """Update the observation that belongs to one feedback record (forward-only)."""
    ledger_path = Path(ledger) if ledger is not None else DEFAULT_LEDGER_PATH
    try:
        reference = "advisor_report:" + str(feedback.get("advisor_report_id") or "unknown")
        oid = ledger_observation_id(feedback.get("episode_id") or "", reference)
        payload = {
            "ok": True,
            "observation_id": oid,
            "episode_id": str(feedback.get("episode_id") or ""),
            "observation_status": OBSERVATION_STATUS_FEEDBACK_PENDING,
            "ledger": str(ledger_path),
            "feedback_reference": feedback_reference(feedback),
            "blocks_production": False,
            "advisory_only": True,
            "errors": [],
        }
        if dry_run:
            payload["observation_status"] = OBSERVATION_STATUS_COMPLETED
            return payload

        if find_record(ledger_path, oid) is None:
            append_record(ledger_path, build_observation(
                payload["episode_id"], advisor_report_reference=reference))
        current = find_record(ledger_path, oid)
        if str(current.get("observation_status")) != OBSERVATION_STATUS_COMPLETED:
            complete_observation(ledger_path, oid,
                                 creator_feedback_reference=feedback_reference(feedback),
                                 production_outcome=production_outcome,
                                 learning_summary=learning_summary if learning_summary is not None else "")
        payload["observation_status"] = str(find_record(ledger_path, oid).get("observation_status"))
        return payload
    except Exception as exc:
        return {
            "ok": False,
            "observation_id": None,
            "episode_id": None,
            "observation_status": None,
            "ledger": str(ledger_path),
            "feedback_reference": None,
            "blocks_production": False,
            "advisory_only": True,
            "errors": [type(exc).__name__ + ": " + str(exc)],
            "traceback": traceback.format_exc(),
        }


__all__ = [
    "apply_feedback",
    "observation_id_for",
    "report_reference",
    "run_observation",
    "story_dna_reference",
]

