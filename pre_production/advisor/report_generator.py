#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisor Report generator.

The report never blocks production. It records a decision, the risks with their
evidence, non-binding recommendations and a confidence level.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from ..story_dna.schema import has_differentiation


def decide(risks: list[dict], dna: dict) -> str:
    """PASS / WARNING / NEEDS_REVISION.

    NEEDS_REVISION only when a HIGH risk exists and the Story Lock itself carries
    no differentiation evidence. Otherwise any MEDIUM/HIGH risk is a WARNING.
    """
    levels = {r.get("level") for r in risks}
    if "HIGH" in levels and not has_differentiation(dna):
        return "NEEDS_REVISION"
    if levels & {"HIGH", "MEDIUM"}:
        return "WARNING"
    return "PASS"


def confidence_level(history_size: int, evidence: list[dict]) -> str:
    if history_size <= 0:
        return "LOW"
    anomaly_hit = any("anomaly" in (e.get("matched_dimensions") or []) for e in evidence)
    if history_size >= 3 and anomaly_hit:
        return "HIGH"
    return "MEDIUM"


def _report_id(episode_id: str, story_lock_sha: str) -> str:
    seed = (str(episode_id) + "|" + str(story_lock_sha)).encode("utf-8")
    return "PPA-" + str(episode_id) + "-" + hashlib.sha256(seed).hexdigest()[:8]


def build_report(*, episode_id: str, dna: dict, evidence: list[dict], risks: list[dict],
                 recommendations: list[str], history_size: int | None = None,
                 created_at: str | None = None) -> dict:
    source = dna.get("source") or {}
    story_lock_sha = str(source.get("story_lock_sha256") or "")
    if history_size is None:
        history_size = len({e.get("related_episode_id") for e in evidence})
    stamp = created_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    return {
        "schema": "advisor_report",
        "schema_version": 1,
        "report_id": _report_id(episode_id, story_lock_sha),
        "episode_id": str(episode_id),
        "story_id": str(dna.get("story_id") or ""),
        "title": str(dna.get("title") or ""),
        "decision": decide(risks, dna),
        "risks": risks,
        "evidence": [str(e.get("evidence_id")) for e in evidence],
        "recommendations": list(recommendations),
        "confidence": confidence_level(history_size, evidence),
        "advisory_only": True,
        "boundaries": {
            "blocks_production": False,
            "mutates_episode_state": False,
            "mutates_story_gates": False,
            "replaces_story_lock": False,
            "grants_production_pass": False,
        },
        "source": {
            "story_lock_path": source.get("story_lock_path"),
            "story_lock_sha256": story_lock_sha,
            "rule_version": source.get("rule_version"),
        },
        "created_time": stamp,
    }


__all__ = ["decide", "confidence_level", "build_report"]

