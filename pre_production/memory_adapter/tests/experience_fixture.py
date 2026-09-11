#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixture helper: seed the Experience Store from EP001 / EP002 / EP003.

The three episodes already exist in this checkout, so the fixture runs the real
advisor over them and pairs the result with an explicit, fixed human judgement.
It is derived test data, never authority, and it never writes into the
production chain: the store directory is always a caller-supplied temp path.

EP001  episodes/10_彼此的天上/01_不存在的夜行路        WARNING
EP002  episodes/10_彼此的天上/02_玻璃另一边的手        NEEDS_REVISION
EP003  episodes/_archive/*EP003*（雾中的另一座生活区） WARNING
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.memory_adapter import (  # noqa: E402
    ingest_feedback,
    pattern_from_evidence,
    validate_risk_pattern,
)
from pre_production.observation import build_feedback  # noqa: E402
from pre_production.observation.ledger import build_observation  # noqa: E402
from pre_production.observation.observation import (  # noqa: E402
    report_reference,
    story_dna_reference,
)

ACTIVE_SERIES = Path("episodes") / "10_彼此的天上"
FIXTURE_PATHS = {
    "EP001": ACTIVE_SERIES / "01_不存在的夜行路",
    "EP002": ACTIVE_SERIES / "02_玻璃另一边的手",
}
EP003_GLOB = "_archive/*EP003*"

# Fixed human judgements. The fixture never invents an automatic opinion: each
# label carries an explicit creator decision written by a person.
CREATOR_JUDGEMENTS = {
    "EP001": {"creator_decision": "IGNORE", "recommendation_result": "NOT_USEFUL",
              "risk_acknowledged": False, "revision_direction": "",
              "final_effect": "维持既有设计", "notes": "未发现需要改动的重复风险"},
    "EP002": {"creator_decision": "ACCEPT", "recommendation_result": "USEFUL",
              "risk_acknowledged": True, "revision_direction": "削弱与既有篇目的空间重叠",
              "final_effect": "按建议修订后继续", "notes": "采纳建议"},
    "EP003": {"creator_decision": "REVISE", "recommendation_result": "PARTIAL",
              "risk_acknowledged": True, "revision_direction": "重新设计异常机制",
              "final_effect": "改稿后仍未拉开差异，最终归档", "notes": "雾中生活区与既有篇目过近"},
}


def find_ep003_dir():
    """The archived EP003 episode directory, if this checkout still has it."""
    matches = sorted(item for item in (REPO_ROOT / "episodes").glob(EP003_GLOB) if item.is_dir())
    return matches[0] if matches else None


def fixture_episodes() -> dict:
    """label -> episode directory, limited to episodes present in this checkout."""
    found: dict = {}
    for label, relative in FIXTURE_PATHS.items():
        path = REPO_ROOT / relative
        if path.is_dir():
            found[label] = path
    archive = find_ep003_dir()
    if archive is not None:
        found["EP003"] = archive
    return found


def analyze_episode_dir(episode_dir):
    """Run the real advisor over one episode directory (read-only, no artifacts)."""
    from pre_production.shadow_mode import analyze_episode

    return analyze_episode(episode_dir)


def feedback_for(label: str, advisor_report: dict, **overrides) -> dict:
    """One human feedback record for a fixture label."""
    judgement = dict(CREATOR_JUDGEMENTS[label])
    judgement.update(overrides)
    return build_feedback(advisor_report, **judgement)


def observation_for(advisor_report: dict) -> dict:
    """Observation record for the fixture: references only, never written to a ledger."""
    return build_observation(
        str(advisor_report.get("episode_id") or ""),
        story_dna_reference=story_dna_reference(advisor_report),
        advisor_report_reference=report_reference(advisor_report),
    )


def patterns_for(evidence) -> list:
    """Risk patterns built from similarity evidence; incomplete evidence is skipped."""
    out: list = []
    for item in evidence or ():
        if not item.get("matched_features") or not item.get("related_episode_id"):
            continue
        record = pattern_from_evidence(item)
        if not validate_risk_pattern(record):
            out.append(record)
    return out


def seed_store(store, labels=None) -> dict:
    """Write fixture experience and risk patterns for EP001 / EP002 / EP003.

    Absent episodes are skipped rather than fabricated. Returns label -> data.
    """
    seeded: dict = {}
    for label, episode_dir in fixture_episodes().items():
        if labels is not None and label not in labels:
            continue
        analysis = analyze_episode_dir(episode_dir)
        report = analysis["advisor_report"]
        feedback = feedback_for(label, report)
        observation = observation_for(report)
        ingest = ingest_feedback(feedback, store=store, observation=observation)
        pattern_results = [store.save_risk_pattern(record)
                           for record in patterns_for(analysis["similarity_report"]["evidence"])]
        seeded[label] = {
            "episode_dir": str(episode_dir),
            "episode_id": str(report.get("episode_id") or ""),
            "story_id": str(report.get("story_id") or ""),
            "decision": str(report.get("decision") or ""),
            "advisor_report": report,
            "feedback": feedback,
            "observation": observation,
            "evidence": analysis["similarity_report"]["evidence"],
            "ingest": ingest,
            "patterns": [result["id"] for result in pattern_results],
        }
    return seeded


__all__ = [
    "ACTIVE_SERIES",
    "CREATOR_JUDGEMENTS",
    "EP003_GLOB",
    "FIXTURE_PATHS",
    "REPO_ROOT",
    "analyze_episode_dir",
    "feedback_for",
    "find_ep003_dir",
    "fixture_episodes",
    "observation_for",
    "patterns_for",
    "seed_store",
]
