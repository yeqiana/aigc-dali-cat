#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story Lock -> Story DNA extraction.

Structure only. The extractor never judges a story; it records which canonical
features are literally present in the Story Lock and keeps the keyword, the
anchor section and the source line as evidence for every token.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .lexicon import (
    DERIVED_FIELDS,
    FIELD_RULES,
    RULE_VERSION,
    SCOPE_HEADINGS,
    SCOPE_META,
    SCOPE_WHOLE,
)
from .schema import DIMENSIONS, dimension_tokens

REPO_ROOT = Path(__file__).resolve().parents[2]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
META_RE = re.compile(r"^>\s*(.+?)\s*$")
TITLE_RE = re.compile(r"《(.+?)》")
META_SEPARATORS = ("：", ":")
SKIP_PATH_PARTS = {"meta", "preimage-revisions", "__pycache__"}


# --- Story Lock discovery ---------------------------------------------------
def find_story_lock(episode_dir: Path | str) -> Path | None:
    """Return the best Story Lock markdown for an episode directory."""
    ep = Path(episode_dir).resolve()
    if not ep.is_dir():
        return None
    matches: list[Path] = []
    for path in ep.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".md":
            continue
        if "storylock" not in path.name.lower():
            continue
        rel_parts = path.relative_to(ep).parts[:-1]
        if any(part in SKIP_PATH_PARTS for part in rel_parts):
            continue
        matches.append(path)
    if not matches:
        return None

    def rank(path: Path) -> tuple[int, int, str]:
        rel = path.relative_to(ep)
        parts = rel.parts
        if parts and parts[0] == "docs":
            pref = 0
        elif parts and parts[0] == "story":
            pref = 1
        else:
            pref = 2
        return (pref, len(parts), str(rel))

    matches.sort(key=rank)
    return matches[0]


# --- Parsing ----------------------------------------------------------------
def _normalise(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_units(text: str) -> list[dict]:
    """Split markdown into (heading, body) units; preamble is heading ''."""
    units: list[dict] = [{"level": 0, "heading": "", "lines": []}]
    for raw in _normalise(text).split("\n"):
        match = HEADING_RE.match(raw)
        if match:
            units.append({"level": len(match.group(1)), "heading": match.group(2).strip(), "lines": []})
        else:
            units[-1]["lines"].append(raw)
    return units


def parse_metadata(text: str) -> dict[str, str]:
    """Collect '> key：value' metadata lines from a Story Lock header."""
    meta: dict[str, str] = {}
    for raw in _normalise(text).split("\n"):
        match = META_RE.match(raw)
        if not match:
            continue
        line = match.group(1)
        for sep in META_SEPARATORS:
            if sep in line:
                key, value = line.split(sep, 1)
                key, value = key.strip(), value.strip()
                if key and value:
                    meta.setdefault(key, value)
                break
    return meta


def _meta_text(meta: dict[str, str]) -> str:
    return "\n".join(f"{k}{META_SEPARATORS[0]}{v}" for k, v in meta.items())


def _scoped_units(scope: str, units: list[dict], meta: dict[str, str]) -> list[tuple[str, str]]:
    def unit_text(unit: dict) -> str:
        heading = unit["heading"]
        body = "\n".join(unit["lines"])
        return (heading + "\n" + body) if heading else body

    if scope == SCOPE_META:
        return [("meta", _meta_text(meta))] if meta else []
    if scope == SCOPE_WHOLE:
        out = [(u["heading"] or "(document)", unit_text(u)) for u in units]
        if meta:
            out.append(("meta", _meta_text(meta)))
        return out
    markers = tuple(m.lower() for m in SCOPE_HEADINGS.get(scope, ()))
    out = []
    for unit in units:
        heading = unit["heading"]
        if not heading:
            continue
        low = heading.lower()
        if any(marker in low for marker in markers):
            out.append((heading, unit_text(unit)))
    return out


def _snippet(text: str, keyword: str, limit: int = 160) -> str:
    for line in text.split("\n"):
        if keyword in line:
            return " ".join(line.split())[:limit]
    return ""


def _match_field(field: str, spec: dict, units: list[dict], meta: dict[str, str]) -> tuple[list[str], list[dict]]:
    tokens: list[str] = []
    evidence: list[dict] = []
    for anchor, text in _scoped_units(spec["scope"], units, meta):
        if not text:
            continue
        for token, keywords in spec["rules"]:
            if token in tokens:
                continue
            for keyword in keywords:
                if keyword in text:
                    tokens.append(token)
                    evidence.append({
                        "field": field,
                        "token": token,
                        "keyword": keyword,
                        "anchor": anchor,
                        "snippet": _snippet(text, keyword),
                    })
                    break
    return tokens, evidence


# --- Story id / title -------------------------------------------------------
def _read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def resolve_story_id(episode_dir: Path | str | None, meta: dict[str, str] | None = None,
                     explicit: str | None = None) -> str:
    """Resolve a stable story id from episode artifacts, then Story Lock meta."""
    if explicit:
        return str(explicit)
    meta = meta or {}
    if episode_dir is not None:
        ep = Path(episode_dir)
        for rel, key in (("meta/episode-fingerprint.json", "episode_id"),
                         ("meta/episode-state.json", "episode_id")):
            data = _read_json(ep / rel)
            if isinstance(data, dict) and data.get(key):
                return str(data[key])
    series = str(meta.get("系列") or "")
    ep_no = str(meta.get("集数") or "")
    series_num = re.match(r"\s*(\d+)", series)
    ep_num = re.search(r"(\d+)", ep_no)
    if series_num and ep_num:
        return f"{int(series_num.group(1)):02d}-{int(ep_num.group(1)):02d}"
    if episode_dir is not None:
        name = Path(episode_dir).name
        match = re.search(r"EP0*(\d+)", name)
        if match:
            return f"EP{int(match.group(1)):02d}"
        return name
    return ""


def resolve_title(units: list[dict], meta: dict[str, str], explicit: str | None = None) -> str:
    if explicit:
        return str(explicit)
    for unit in units:
        match = TITLE_RE.search(unit["heading"] or "")
        if match:
            return match.group(1).strip()
    return str(meta.get("标题") or "")


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path)


# --- Extraction -------------------------------------------------------------
def extract_story_dna(*, story_lock_path: Path | str | None = None,
                      text: str | None = None,
                      episode_dir: Path | str | None = None,
                      story_id: str | None = None,
                      title: str | None = None,
                      extracted_at: str | None = None) -> dict:
    """Extract story_fingerprint data from a Story Lock source.

    Provide exactly one of story_lock_path / text / episode_dir (episode_dir is
    searched for the Story Lock automatically).
    """
    source_path: Path | None = None
    if text is None:
        if story_lock_path is None and episode_dir is not None:
            story_lock_path = find_story_lock(episode_dir)
            if story_lock_path is None:
                raise FileNotFoundError(f"no Story Lock found under {episode_dir}")
        if story_lock_path is None:
            raise ValueError("extract_story_dna needs story_lock_path, text or episode_dir")
        source_path = Path(story_lock_path).resolve()
        text = source_path.read_text(encoding="utf-8-sig")
    elif story_lock_path is not None:
        source_path = Path(story_lock_path).resolve()

    text = _normalise(text)
    units = parse_units(text)
    meta = parse_metadata(text)

    resolved_id = resolve_story_id(episode_dir if episode_dir is not None else
                                   (source_path.parent if source_path else None), meta, story_id)
    resolved_title = resolve_title(units, meta, title)

    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    stamp = extracted_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    dna: dict[str, Any] = {
        "schema": "story_dna",
        "schema_version": 1,
        "story_id": resolved_id,
        "title": resolved_title,
        "source": {
            "story_lock_path": _relative(source_path) if source_path else None,
            "story_lock_sha256": sha,
            "extracted_at": stamp,
            "rule_version": RULE_VERSION,
        },
    }

    evidence: list[dict] = []
    for dim, subs in DIMENSIONS.items():
        dna[dim] = {}
        for sub in subs:
            field = f"{dim}.{sub}"
            spec = FIELD_RULES.get((dim, sub))
            if spec is None:
                dna[dim][sub] = []
                continue
            tokens, field_evidence = _match_field(field, spec, units, meta)
            dna[dim][sub] = tokens
            evidence.extend(field_evidence)

    for (dim, sub), (src_dim, src_sub) in DERIVED_FIELDS.items():
        if dna.get(dim, {}).get(sub):
            continue
        source_tokens = list(dna.get(src_dim, {}).get(src_sub) or [])
        dna[dim][sub] = source_tokens
        for token in source_tokens:
            evidence.append({
                "field": f"{dim}.{sub}",
                "token": token,
                "keyword": f"(derived:{src_dim}.{src_sub})",
                "anchor": "(derived)",
                "snippet": "",
            })

    warnings: list[str] = []
    for dim in DIMENSIONS:
        if not dimension_tokens(dna, dim):
            warnings.append(f"{dim}: no lexicon evidence found in Story Lock")

    dna["extraction_trace"] = {
        "rule_version": RULE_VERSION,
        "sections": [u["heading"] for u in units if u["heading"]],
        "metadata_keys": sorted(meta.keys()),
        "warnings": warnings,
    }
    dna["evidence"] = evidence
    return dna


__all__ = [
    "extract_story_dna",
    "find_story_lock",
    "parse_metadata",
    "parse_units",
    "resolve_story_id",
    "resolve_title",
]
