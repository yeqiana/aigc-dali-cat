#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode Observation Ledger for the Shadow Observation phase.

One append-only JSONL row per shadow observation run, so a creator can look
back at what the advisor said before a story was produced.

Frozen boundaries:
- derived, never authority: it never grants PASS and never replaces
  meta/episode-state.json or meta/story-gates.json;
- written only when a human runs the observe command, never by the production
  Runtime;
- a correction is a new row; existing rows are never rewritten;
- deleting the ledger loses experience history, not production truth.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..story_dna.validator import require_valid, validate_observation_entry

DEFAULT_LEDGER_PATH = Path("reports") / "pre-production" / "observation-ledger.jsonl"
AUTHORITY = "derived_non_authority"
RUN_MODE_SHADOW = "shadow"
LEVEL_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}


def _stamp(recorded_at=None) -> str:
    return recorded_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def observation_id(episode_id: str, story_lock_sha256: str) -> str:
    """Stable observation id: episode + the Story Lock revision it observed."""
    short = str(story_lock_sha256 or "")[:8] or "nohash"
    return "OB-" + (str(episode_id) or "unknown") + "-" + short


def highest_risk_level(risks) -> str:
    """Highest risk level present in a risk list (NONE when there is none)."""
    best = "NONE"
    for risk in risks or []:
        level = str((risk or {}).get("level") or "")
        if level in LEVEL_ORDER and LEVEL_ORDER[level] < LEVEL_ORDER[best]:
            best = level
    return best


def build_entry(advisor_report: dict, *, similarity_report: dict | None = None,
                artifact_dir=None, run_mode: str = RUN_MODE_SHADOW,
                recorded_at=None, feedback_id=None) -> dict:
    """Build one observation ledger entry from an advisor report."""
    source = advisor_report.get("source") or {}
    risks = advisor_report.get("risks") or []
    evidence_ids = [str(item) for item in (advisor_report.get("evidence") or [])]
    if not evidence_ids and similarity_report:
        evidence_ids = [str(item.get("evidence_id")) for item in (similarity_report.get("evidence") or [])]
    sha = str(source.get("story_lock_sha256") or "")
    episode_id = str(advisor_report.get("episode_id") or "")

    return {
        "schema": "observation_ledger_entry",
        "schema_version": 1,
        "observation_id": observation_id(episode_id, sha),
        "recorded_at": _stamp(recorded_at),
        "run_mode": run_mode,
        "episode_id": episode_id,
        "title": str(advisor_report.get("title") or ""),
        "advisor_report_id": str(advisor_report.get("report_id") or ""),
        "story_lock_sha256": sha,
        "rule_version": str(source.get("rule_version") or ""),
        "decision": str(advisor_report.get("decision") or ""),
        "confidence": str(advisor_report.get("confidence") or ""),
        "risk_count": len(risks),
        "evidence_count": len(evidence_ids),
        "highest_risk_level": highest_risk_level(risks),
        "matched_dimensions": sorted({str(dim) for risk in risks
                                      for dim in (risk.get("matched_dimensions") or [])}),
        "recommendations": [str(token) for token in (advisor_report.get("recommendations") or [])],
        "artifact_dir": str(artifact_dir) if artifact_dir else None,
        "feedback_id": feedback_id,
        "advisory_only": True,
        "blocks_production": False,
        "mutates_episode_state": False,
        "mutates_story_gates": False,
        "authority": AUTHORITY,
    }


def entry_key(entry: dict) -> tuple:
    """Dedupe key: one observation per (run mode, episode, Story Lock revision)."""
    return (entry.get("run_mode"), entry.get("episode_id"), entry.get("story_lock_sha256"))


def scan_ledger(path) -> tuple:
    """Return (valid entries, malformed line reports). Never raises."""
    file_path = Path(path)
    if not file_path.is_file():
        return [], []
    entries: list = []
    malformed: list = []
    for number, raw in enumerate(file_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception as exc:
            malformed.append({"line": number, "error": type(exc).__name__})
            continue
        if isinstance(data, dict):
            entries.append(data)
        else:
            malformed.append({"line": number, "error": "not_an_object"})
    return entries, malformed


def read_entries(path) -> list:
    """Valid ledger entries; malformed lines are reported by scan_ledger, not raised."""
    return scan_ledger(path)[0]


def find_entry(entries, key) -> dict | None:
    for entry in entries:
        if entry_key(entry) == key:
            return entry
    return None


def append_entry(path, entry: dict, *, allow_duplicate: bool = False) -> dict:
    """Append one entry unless the same Story Lock revision was already observed."""
    require_valid(validate_observation_entry(entry), "observation_ledger_entry")
    file_path = Path(path)
    entries = read_entries(file_path)
    existing = find_entry(entries, entry_key(entry))
    if existing is not None and not allow_duplicate:
        return {"status": "REUSED", "entry": existing, "path": str(file_path),
                "entry_index": None, "total_entries": len(entries)}

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"status": "APPENDED", "entry": entry, "path": str(file_path),
            "entry_index": len(entries) + 1, "total_entries": len(entries) + 1}


def index_by_episode(entries) -> dict:
    out: dict = {}
    for entry in entries:
        out.setdefault(str(entry.get("episode_id") or ""), []).append(entry)
    return out


def summarize(entries) -> dict:
    """Real counts over recorded observations; no score of any kind."""
    by_decision: dict = {}
    by_level: dict = {}
    for entry in entries:
        decision = str(entry.get("decision"))
        level = str(entry.get("highest_risk_level"))
        by_decision[decision] = by_decision.get(decision, 0) + 1
        by_level[level] = by_level.get(level, 0) + 1
    stamps = sorted(str(entry.get("recorded_at") or "") for entry in entries if entry.get("recorded_at"))
    return {
        "observations": len(entries),
        "episodes": len({str(entry.get("episode_id") or "") for entry in entries}),
        "with_feedback": len([entry for entry in entries if entry.get("feedback_id")]),
        "by_decision": by_decision,
        "by_highest_risk_level": by_level,
        "latest_recorded_at": stamps[-1] if stamps else None,
        "authority": AUTHORITY,
    }


__all__ = [
    "AUTHORITY",
    "DEFAULT_LEDGER_PATH",
    "RUN_MODE_SHADOW",
    "append_entry",
    "build_entry",
    "entry_key",
    "find_entry",
    "highest_risk_level",
    "index_by_episode",
    "observation_id",
    "read_entries",
    "scan_ledger",
    "summarize",
]

