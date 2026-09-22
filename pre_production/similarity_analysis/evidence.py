#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Similarity Evidence records.

Evidence carries only risk levels and matched features. It never carries a
similarity percentage or a score.
"""
from __future__ import annotations

from datetime import datetime, timezone

LEVEL_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def build_evidence(*, current_story_id: str, related_episode_id: str, related_title: str,
                   risk_level: str, matched_dimensions: list[str], matched_features: list[str],
                   explanation: str, source_path: str = "", risk_type: str = "similarity") -> dict:
    """Construct one evidence record (validated by story_dna.validator)."""
    return {
        "schema": "similarity_evidence",
        "schema_version": 1,
        "evidence_id": "SE-" + str(current_story_id) + "-" + str(related_episode_id),
        "current_story_id": current_story_id,
        "related_episode_id": related_episode_id,
        "related_title": related_title,
        "related_source_path": source_path,
        "risk_type": risk_type,
        "risk_level": risk_level,
        "matched_dimensions": sorted(matched_dimensions),
        "matched_features": sorted(matched_features),
        "explanation": explanation,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }


def sort_evidence(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda e: (LEVEL_ORDER.get(e.get("risk_level"), 9),
                                        str(e.get("related_episode_id", ""))))


def count_levels(items: list[dict]) -> dict:
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for item in items:
        level = item.get("risk_level")
        if level in counts:
            counts[level] += 1
    return counts


__all__ = ["build_evidence", "sort_evidence", "count_levels", "LEVEL_ORDER"]

