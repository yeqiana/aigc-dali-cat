#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memory Adapter (interface layer only).

Responsibilities:
- read historical experience (Story Lock DNA) for the advisor,
- persist one Review Reference so the creator decision can later be recorded.

Non-goals: it is not a rule engine, keeps no hard rules and no fixed scores, and
it never writes episode-state.json or story-gates.json. A future Experience
Store can replace this implementation behind the same interface.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..similarity_analysis.retrieval import REPO_ROOT, build_history
from ..story_dna.validator import require_valid, validate_review_reference

DEFAULT_STORE_DIR = "reports/pre-production"


class MemoryAdapter:
    """Thin read/write facade over historical experience and review references."""

    def __init__(self, repo_root: Path | str | None = None, store_dir: Path | str | None = None):
        self.repo_root = Path(repo_root) if repo_root is not None else REPO_ROOT
        base = Path(store_dir) if store_dir is not None else (self.repo_root / DEFAULT_STORE_DIR)
        self.store_dir = base
        self.review_dir = base / "review-references"

    # --- read path ---------------------------------------------------------
    def history(self, *, limit: int | None = None, exclude_dirs: tuple = (),
                explicit_paths: tuple = ()) -> list:
        """Return historical Episode DNA samples for similarity analysis."""
        return build_history(repo_root=self.repo_root, exclude_dirs=exclude_dirs,
                             explicit_paths=explicit_paths, limit=limit)

    def list_review_references(self) -> list[Path]:
        if not self.review_dir.is_dir():
            return []
        return sorted(self.review_dir.glob("*.json"))

    def read_review_reference(self, review_id: str) -> dict | None:
        path = self.review_dir / (review_id + ".json")
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None

    # --- write path --------------------------------------------------------
    def build_review_reference(self, advisor_report: dict, *, creator_decision: str = "pending",
                               feedback: str = "", final_result: str = "") -> dict:
        stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        report_id = str(advisor_report.get("report_id") or "")
        episode_id = str(advisor_report.get("episode_id") or "")
        return {
            "schema": "review_reference",
            "schema_version": 1,
            "review_id": "PPR-" + report_id,
            "advisor_report_id": report_id,
            "episode_id": episode_id,
            "advisor_decision": advisor_report.get("decision"),
            "creator_decision": creator_decision,
            "final_result": final_result,
            "feedback": feedback,
            "created_time": stamp,
        }

    def save_review_reference(self, advisor_report: dict, *, creator_decision: str = "pending",
                              feedback: str = "", final_result: str = "") -> Path:
        """Persist one Review Reference (Memory Reference), returning its path."""
        ref = self.build_review_reference(advisor_report, creator_decision=creator_decision,
                                          feedback=feedback, final_result=final_result)
        require_valid(validate_review_reference(ref), "review_reference")
        self.review_dir.mkdir(parents=True, exist_ok=True)
        path = self.review_dir / (ref["review_id"] + ".json")
        path.write_text(json.dumps(ref, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        return path


__all__ = ["MemoryAdapter", "DEFAULT_STORE_DIR"]

