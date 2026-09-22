#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Mode integration for Pre Production Intelligence.

Flow: Story Lock -> Advisor -> report only -> continue the normal production flow.

Guarantees:
- run_shadow never raises and never returns anything that blocks production;
- it never writes episode-state.json, story-gates.json or any production asset;
- artifacts are written only under the requested output directory (default:
  <episode>/meta/pre-production/).
"""
from __future__ import annotations

import traceback
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .advisor import assess_risks, build_recommendations, build_report
from .memory_adapter import MemoryAdapter
from .similarity_analysis.analyzer import analyze_similarity
from .similarity_analysis.retrieval import REPO_ROOT, build_history
from .story_dna.extractor import extract_story_dna, find_story_lock
from .story_dna.validator import (
    validate_advisor_report,
    validate_dna,
    validate_similarity_report,
)

DEFAULT_OUT_SUBDIR = Path("meta") / "pre-production"
ARTIFACT_NAMES = ("story_fingerprint.yaml", "similarity_report.yaml", "advisor_report.yaml")


def _stamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _sample_id(sample) -> str:
    """Episode id of a history entry, accepting HistoricalSample or plain DNA."""
    if hasattr(sample, "episode_id"):
        return str(sample.episode_id)
    return str((sample or {}).get("story_id") or "") if isinstance(sample, dict) else ""


def _sample_summary(sample) -> dict:
    """Compact history entry, accepting HistoricalSample or plain DNA."""
    if hasattr(sample, "summary"):
        return sample.summary()
    dna = sample if isinstance(sample, dict) else {}
    return {
        "episode_id": str(dna.get("story_id") or ""),
        "title": str(dna.get("title") or ""),
        "source_path": "",
    }


def analyze_episode(episode_dir: Path | str, *, repo_root: Path | str | None = None,
                    history_paths: tuple = (), history_limit: int | None = None,
                    story_lock: Path | str | None = None, story_id: str | None = None,
                    history: list | None = None) -> dict:
    """Run the read-only Story DNA -> Similarity -> Advisor chain for one episode."""
    ep = Path(episode_dir).resolve()
    if not ep.is_dir():
        raise FileNotFoundError("episode directory not found: " + str(episode_dir))

    lock_path = Path(story_lock).resolve() if story_lock else find_story_lock(ep)
    if lock_path is None:
        raise FileNotFoundError("no Story Lock found under " + str(ep))

    dna = extract_story_dna(story_lock_path=lock_path, episode_dir=ep, story_id=story_id)

    if history is None:
        history = build_history(repo_root=repo_root or REPO_ROOT, exclude_dirs=(ep,),
                                explicit_paths=tuple(history_paths), limit=history_limit)

    evidence = analyze_similarity(dna, history)
    risks = assess_risks(dna, evidence)
    recommendations = build_recommendations(risks, dna)
    report = build_report(episode_id=str(dna.get("story_id") or ""), dna=dna, evidence=evidence,
                          risks=risks, recommendations=recommendations, history_size=len(history))

    similarity_report = {
        "schema": "similarity_report",
        "schema_version": 1,
        "current_story_id": str(dna.get("story_id") or ""),
        "current_story_title": str(dna.get("title") or ""),
        "generated_at": _stamp(),
        "history_size": len(history),
        "history_episode_ids": [_sample_id(s) for s in history],
        "evidence": evidence,
    }

    return {
        "episode_dir": str(ep),
        "story_lock": str(lock_path),
        "dna": dna,
        "similarity_report": similarity_report,
        "advisor_report": report,
        "history": [_sample_summary(s) for s in history],
        "issues": {
            "story_dna": validate_dna(dna),
            "similarity_report": validate_similarity_report(similarity_report),
            "advisor_report": validate_advisor_report(report),
        },
    }


def _dump_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def write_artifacts(result: dict, out_dir: Path | str) -> dict:
    """Write story_fingerprint / similarity_report / advisor_report YAML files."""
    out = Path(out_dir)
    written = {
        "story_fingerprint.yaml": _dump_yaml(out / "story_fingerprint.yaml", result["dna"]),
        "similarity_report.yaml": _dump_yaml(out / "similarity_report.yaml", result["similarity_report"]),
        "advisor_report.yaml": _dump_yaml(out / "advisor_report.yaml", result["advisor_report"]),
    }
    return {name: str(path) for name, path in written.items()}


def run_shadow(episode_dir: Path | str, *, out_dir: Path | str | None = None,
               repo_root: Path | str | None = None, history_paths: tuple = (),
               history_limit: int | None = None, write_memory: bool = True,
               memory_store: Path | str | None = None, dry_run: bool = False) -> dict:
    """Shadow-mode entry point. Never raises; never blocks production."""
    ep = Path(episode_dir)
    result_out = Path(out_dir) if out_dir is not None else (ep / DEFAULT_OUT_SUBDIR)
    try:
        analyzed = analyze_episode(episode_dir, repo_root=repo_root, history_paths=history_paths,
                                   history_limit=history_limit)
        report = analyzed["advisor_report"]
        payload = {
            "ok": True,
            "episode_id": report.get("episode_id"),
            "title": report.get("title"),
            "decision": report.get("decision"),
            "confidence": report.get("confidence"),
            "risk_count": len(report.get("risks") or []),
            "recommendations": report.get("recommendations") or [],
            "artifacts": {},
            "review_reference": None,
            "issues": analyzed["issues"],
            "errors": [],
            "advisory_only": True,
            "blocks_production": False,
        }
        if dry_run:
            return payload

        payload["artifacts"] = write_artifacts(analyzed, result_out)
        if write_memory:
            adapter = MemoryAdapter(repo_root=repo_root, store_dir=memory_store)
            payload["review_reference"] = str(adapter.save_review_reference(report))
        return payload
    except Exception as exc:  # shadow mode must never break the production flow
        return {
            "ok": False,
            "episode_id": None,
            "decision": "UNKNOWN",
            "artifacts": {},
            "review_reference": None,
            "errors": [type(exc).__name__ + ": " + str(exc)],
            "traceback": traceback.format_exc(),
            "advisory_only": True,
            "blocks_production": False,
        }


__all__ = ["analyze_episode", "write_artifacts", "run_shadow", "DEFAULT_OUT_SUBDIR", "ARTIFACT_NAMES"]
