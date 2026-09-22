#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only Memory/Experience advice for the next creative Story step.

This module deliberately has no Episode authority.  It reads the existing
PreProduction Experience Store and returns bounded historical watch-outs for
CREATIVE_STORY.  It never mutates Runtime Request, Episode state, gates, Story
Lock or production ledgers, and a missing/corrupt memory store fails soft.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_LIMIT = 8


def _pattern_row(row: dict[str, Any]) -> dict[str, Any] | None:
    description = str(row.get("pattern_description") or "").strip()
    if not description:
        return None
    return {
        "pattern_id": str(row.get("pattern_id") or ""),
        "risk_type": str(row.get("risk_type") or ""),
        "risk_level": row.get("risk_level"),
        "pattern_description": description,
        "related_episode": [str(item) for item in (row.get("related_episode") or [])],
        "evidence": [str(item) for item in (row.get("evidence") or [])],
    }


def advice_for_episode(
    episode: Path | str | None = None,
    *,
    store_dir: Path | str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Return bounded account-history watch-outs; never raise to production."""
    bounded = max(0, min(int(limit), 20))
    base = {
        "schema_version": 1,
        "advisory_only": True,
        "blocks_production": False,
        "mutates_episode_state": False,
        "mutates_story_gates": False,
        "replaces_runtime_request": False,
        "authority": "derived_non_authority",
        "scope": "account_history_watchouts",
        "selection": "latest_distinct_risk_patterns_no_score",
        "episode": None,
        "status": "EMPTY",
        "patterns": [],
        "instructions": [
            "Historical patterns are watch-outs, not commands. Explicit user constraints and canonical Story OS standards always win.",
            "First create the strongest story for the current request; only revise when the new concept actually repeats one of these historical patterns.",
            "Do not copy historical episode details, faces, scenes, wording, or anomaly mechanisms merely because they appear in memory.",
        ],
    }
    try:
        if episode is not None:
            ep = Path(episode).resolve()
            try:
                base["episode"] = ep.relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                base["episode"] = ep.name
        if bounded == 0:
            return base
        from pre_production.memory_adapter.experience_store_jsonl import (
            JsonlExperienceStore,
            KIND_PATTERN,
        )

        store = JsonlExperienceStore(store_dir)
        rows = store.read(KIND_PATTERN)
        seen: set[str] = set()
        selected: list[dict[str, Any]] = []
        for row in reversed(rows):
            if not isinstance(row, dict):
                continue
            normalized = _pattern_row(row)
            if normalized is None:
                continue
            key = normalized["pattern_id"] or (
                normalized["risk_type"] + "|" + normalized["pattern_description"]
            )
            if key in seen:
                continue
            seen.add(key)
            selected.append(normalized)
            if len(selected) >= bounded:
                break
        selected.reverse()
        base["patterns"] = selected
        base["status"] = "AVAILABLE" if selected else "EMPTY"
        base["source_record_count"] = len(rows)
        return base
    except Exception as exc:
        base["status"] = "UNAVAILABLE"
        base["error"] = type(exc).__name__
        return base


def prompt_block(episode: Path | str | None = None, *, limit: int = DEFAULT_LIMIT) -> str:
    """Compact natural-language block for a creative model prompt."""
    advice = advice_for_episode(episode, limit=limit)
    lines = [
        "<MEMORY_ADVICE advisory_only=\"true\" blocks_production=\"false\">",
        "Memory is read-only historical advice. Never let it override explicit user constraints or Story OS authority.",
    ]
    for row in advice.get("patterns") or []:
        level = str(row.get("risk_level") or "UNSPECIFIED")
        risk_type = str(row.get("risk_type") or "pattern")
        description = str(row.get("pattern_description") or "")
        lines.append(f"- [{level}/{risk_type}] historical watch-out: {description}")
    if not (advice.get("patterns") or []):
        lines.append("- No usable historical risk pattern is currently available; continue normally.")
    lines.append("</MEMORY_ADVICE>")
    return "\n".join(lines)


__all__ = ["DEFAULT_LIMIT", "advice_for_episode", "prompt_block"]
