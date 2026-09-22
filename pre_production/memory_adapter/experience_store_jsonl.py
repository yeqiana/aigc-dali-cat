#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONL-backed Experience Store (Experience Store Runtime MVP).

Implements ``ExperienceStoreRepository`` on plain append-only JSONL files. It is
a fact store: it never ranks, scores, learns or decides.

Default layout (``reports/pre-production/experience-store/``)::

    experience-records.jsonl    one Episode Experience per line
    risk-patterns.jsonl         one Risk Pattern per line
    creator-decisions.jsonl     one Creator Decision Experience per line

Guarantees:
- append only: a saved record is never rewritten, reordered or deleted;
- one independent JSON object per line;
- duplicate protection by primary id: a repeat save is reported REUSED and is
  not appended again;
- a save validates the contract first and raises a clear error; errors are not
  swallowed and a rejected save leaves the file untouched;
- a read tolerates a malformed line: it is reported by ``scan``, never raised.

Boundaries: nothing here touches the Runtime, ``episode-state.json`` or
``story-gates.json``; nothing here edits the advisor, its rules or the lexicon.
"""
from __future__ import annotations

import json
from pathlib import Path

from .experience_schema import (
    require_valid,
    validate_creator_decision_experience,
    validate_experience_record,
    validate_risk_pattern,
)
from .experience_store import ExperienceStoreRepository

DEFAULT_STORE_DIR = Path("reports") / "pre-production" / "experience-store"
EXPERIENCE_FILE = "experience-records.jsonl"
PATTERN_FILE = "risk-patterns.jsonl"
DECISION_FILE = "creator-decisions.jsonl"

KIND_EXPERIENCE = "experience"
KIND_PATTERN = "pattern"
KIND_DECISION = "decision"
KINDS = (KIND_EXPERIENCE, KIND_PATTERN, KIND_DECISION)


def scan_jsonl(path) -> tuple:
    """Return (rows, malformed line reports) for one JSONL file. Never raises."""
    file_path = Path(path)
    if not file_path.is_file():
        return [], []
    rows: list = []
    malformed: list = []
    for number, raw in enumerate(file_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            malformed.append({"line": number, "error": type(exc).__name__})
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            malformed.append({"line": number, "error": "not_an_object"})
    return rows, malformed


def _story_dna_query(story_dna) -> str:
    """Normalise the DNA query to a reference string.

    Accepts either a reference string (``story_dna:10-01@abcd1234``) or a Story
    DNA mapping, in which case ``story_id`` plus the Story Lock sha prefix form
    the same reference the observation module writes.
    """
    if story_dna is None:
        return ""
    if isinstance(story_dna, str):
        return story_dna.strip()
    if isinstance(story_dna, dict):
        story_id = str(story_dna.get("story_id") or "")
        if not story_id:
            return ""
        sha = str((story_dna.get("source") or {}).get("story_lock_sha256") or "")
        return "story_dna:" + story_id + (("@" + sha[:8]) if sha else "")
    return str(story_dna)


def _matches_reference(reference, query: str) -> bool:
    """Plain reference match: exact or prefix/substring. No similarity, no score."""
    text = str(reference or "")
    return text == query or query in text


class JsonlExperienceStore(ExperienceStoreRepository):
    """Append-only JSONL implementation of the Experience Store interface."""

    def __init__(self, store_dir: Path | str | None = None):
        self.store_dir = Path(store_dir) if store_dir is not None else DEFAULT_STORE_DIR

    # --- paths -------------------------------------------------------------
    def path_for(self, kind: str) -> Path:
        if kind == KIND_EXPERIENCE:
            return self.store_dir / EXPERIENCE_FILE
        if kind == KIND_PATTERN:
            return self.store_dir / PATTERN_FILE
        if kind == KIND_DECISION:
            return self.store_dir / DECISION_FILE
        raise ValueError("unknown experience store kind: " + str(kind))

    # --- write path --------------------------------------------------------
    def _append(self, record: dict, kind: str, id_field: str) -> dict:
        path = self.path_for(kind)
        rows, _ = scan_jsonl(path)
        wanted = str(record.get(id_field) or "")
        for row in rows:
            if str(row.get(id_field) or "") == wanted:
                return {"status": "REUSED", "id": wanted, id_field: wanted,
                        "record": row, "path": str(path), "rows": len(rows),
                        "unchanged": row == record}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"status": "APPENDED", "id": wanted, id_field: wanted,
                "record": record, "path": str(path), "rows": len(rows) + 1}

    def save_experience(self, record: dict) -> dict:
        """Validate and append one Episode Experience; return the save result."""
        require_valid(validate_experience_record(record), "experience_record")
        return self._append(record, KIND_EXPERIENCE, "experience_id")

    def save_risk_pattern(self, record: dict) -> dict:
        """Validate and append one Risk Pattern; return the save result."""
        require_valid(validate_risk_pattern(record), "risk_pattern")
        return self._append(record, KIND_PATTERN, "pattern_id")

    def save_creator_decision(self, record: dict) -> dict:
        """Validate and append one Creator Decision Experience; return the result."""
        require_valid(validate_creator_decision_experience(record),
                      "creator_decision_experience")
        return self._append(record, KIND_DECISION, "decision_experience_id")

    # --- read path ---------------------------------------------------------
    def read(self, kind: str) -> list:
        """All stored records of one kind, in append order. Malformed lines are skipped."""
        return scan_jsonl(self.path_for(kind))[0]

    def get_related_experience(self, *, story_dna: dict | None = None,
                               episode_id: str | None = None,
                               limit: int | None = None) -> list:
        """Candidate experience records matching episode_id / story_dna_reference.

        Plain reference filtering only: no ranking, no similarity, no score.
        """
        query = _story_dna_query(story_dna)
        found: list = []
        for record in self.read(KIND_EXPERIENCE):
            if episode_id is not None and str(record.get("episode_id") or "") != str(episode_id):
                continue
            if query and not _matches_reference(record.get("story_dna_reference"), query):
                continue
            found.append(record)
        return found if limit is None else found[:limit]

    def query_pattern(self, *, risk_type: str | None = None, tokens=(),
                      limit: int | None = None) -> list:
        """Candidate risk patterns matching risk_type and all given tokens.

        Token matching is a plain case-insensitive substring test over the
        pattern description and its related episodes. No similarity is computed.
        """
        wanted = [str(token).lower() for token in (tokens or ()) if str(token)]
        found: list = []
        for record in self.read(KIND_PATTERN):
            if risk_type is not None and str(record.get("risk_type") or "") != str(risk_type):
                continue
            if wanted:
                haystack = " ".join([str(record.get("pattern_description") or "")]
                                    + [str(item) for item in record.get("related_episode") or []]).lower()
                if not all(token in haystack for token in wanted):
                    continue
            found.append(record)
        return found if limit is None else found[:limit]

    def list_records(self, kind: str, *, episode_id: str | None = None) -> list:
        """Read-only listing for the CLI; optional episode filter, append order kept."""
        records = self.read(kind)
        if episode_id is None:
            return records
        return [r for r in records if str(r.get("episode_id") or "") == str(episode_id)]

    # --- audit -------------------------------------------------------------
    def malformed(self) -> dict:
        """Malformed line reports per kind (audit surface; reads never raise)."""
        return {kind: scan_jsonl(self.path_for(kind))[1] for kind in KINDS}

    def summarize(self) -> dict:
        """Real counts over stored records; no score, no learning signal."""
        counts = {}
        episodes = set()
        for kind in KINDS:
            rows = self.read(kind)
            counts[kind] = len(rows)
            episodes.update(str(row.get("episode_id") or "") for row in rows)
        return {
            "store_dir": str(self.store_dir),
            "files": {kind: str(self.path_for(kind)) for kind in KINDS},
            "counts": counts,
            "episodes": len([item for item in episodes if item]),
            "malformed": {kind: len(items) for kind, items in self.malformed().items()},
            "authority": "derived_non_authority",
        }


__all__ = [
    "DEFAULT_STORE_DIR",
    "DECISION_FILE",
    "EXPERIENCE_FILE",
    "JsonlExperienceStore",
    "KINDS",
    "KIND_DECISION",
    "KIND_EXPERIENCE",
    "KIND_PATTERN",
    "PATTERN_FILE",
    "scan_jsonl",
]
