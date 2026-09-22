#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story DNA schema accessors (single source: pre_production/contracts/*.json)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

CONTRACTS_DIR = Path(__file__).resolve().parents[1] / "contracts"

_CACHE: dict[str, dict] = {}


def load_contract(name: str) -> dict:
    """Load one contract JSON document by file name (cached)."""
    if name not in _CACHE:
        path = CONTRACTS_DIR / name
        with path.open("r", encoding="utf-8") as fh:
            _CACHE[name] = json.load(fh)
    return _CACHE[name]


STORY_DNA_SCHEMA = load_contract("story_dna.schema.json")
REQUIRED_TOP_LEVEL: tuple[str, ...] = tuple(STORY_DNA_SCHEMA["required_top_level"])
DIMENSIONS: dict[str, list[str]] = {k: list(v) for k, v in STORY_DNA_SCHEMA["dimensions"].items()}
COMPARISON_FIELDS: dict[str, list[str]] = {k: list(v) for k, v in STORY_DNA_SCHEMA["comparison_fields"].items()}
FORBIDDEN_KEY_PATTERNS: tuple[str, ...] = tuple(STORY_DNA_SCHEMA["forbidden_key_patterns"])

# Tokens shared by essentially the whole account. They describe the account's
# baseline voice (first-person ordinary-people reality anomaly) rather than a
# story-specific overlap, so similarity must ignore them.
GENERIC_TOKENS: frozenset = frozenset({
    "first_person_handheld_capture",
    "ordinary_young_adult",
    "open_double_explanation",
    "reality_grounded_anomaly",
    "ordinary_person_uncanny",
    "phone_screen_capture",
    "phone_screen_motif",
})


def empty_dna(story_id: str = "", title: str = "") -> dict:
    """Return a schema-shaped DNA with empty (no-evidence) values."""
    dna: dict[str, Any] = {
        "schema": "story_dna",
        "schema_version": 1,
        "story_id": story_id,
        "title": title,
    }
    for dim, subs in DIMENSIONS.items():
        dna[dim] = {sub: [] for sub in subs}
    return dna


def token_set(value: Any) -> set[str]:
    """Normalise a subfield value (str | list | None) to a set of tokens."""
    if value is None:
        return set()
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, (list, tuple, set)):
        return {str(v) for v in value if str(v)}
    return set()


def dimension_tokens(dna: dict, dimension: str) -> set[str]:
    """All tokens a DNA carries for one dimension (every subfield)."""
    out: set[str] = set()
    values = dna.get(dimension) or {}
    if isinstance(values, dict):
        for value in values.values():
            out |= token_set(value)
    return out


def comparison_tokens(dna: dict) -> dict[str, set[str]]:
    """Tokens used for similarity: contract comparison fields minus GENERIC_TOKENS."""
    out: dict[str, set[str]] = {}
    for dim, fields in COMPARISON_FIELDS.items():
        tokens: set[str] = set()
        values = dna.get(dim) or {}
        if isinstance(values, dict):
            for field in fields:
                tokens |= token_set(values.get(field))
        out[dim] = tokens - GENERIC_TOKENS
    return out


def has_differentiation(dna: dict) -> bool:
    """True when the Story Lock itself declares differentiation evidence."""
    series_fit = dna.get("series_fit") or {}
    if not isinstance(series_fit, dict):
        return False
    return bool(token_set(series_fit.get("differentiation_evidence")))


def missing_subfields(dna: dict) -> list[str]:
    """Return 'dimension.subfield' entries absent from a DNA document."""
    missing: list[str] = []
    for dim, subs in DIMENSIONS.items():
        values = dna.get(dim)
        if not isinstance(values, dict):
            missing.append(dim)
            continue
        for sub in subs:
            if sub not in values:
                missing.append(f"{dim}.{sub}")
    return missing


def iter_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key)
            yield from iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_keys(item)
