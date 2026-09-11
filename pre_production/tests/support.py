#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared, hermetic helpers for Pre Production Intelligence tests.

The helpers keep tests independent of the working directory: they resolve the
repository root from __file__ and build DNA documents in memory so unit tests
never depend on the current content of episodes/.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.story_dna.schema import empty_dna, iter_keys  # noqa: E402

# Substrings that must never appear in a key of any generated artifact: they
# would imply a numeric judgement where the MVP only allows risk levels.
FORBIDDEN_HINTS = ("score", "rating", "percent", "percentage", "points", "grade", "star", "rank")

EP003_GLOB = "_archive/*EP003*"


def build_dna(story_id: str = "CUR-01", title: str = "当前故事", **values) -> dict:
    """Build a DNA document from dimension__subfield=value keyword arguments."""
    dna = empty_dna(story_id, title)
    for key, value in values.items():
        dim, _, sub = key.partition("__")
        if not sub:
            raise ValueError("use dimension__subfield keys, got: " + key)
        dna.setdefault(dim, {})[sub] = value
    return dna


def forbidden_keys(obj) -> list:
    """Return every key in obj that looks like a score/percentage field."""
    return sorted({k for k in iter_keys(obj) if any(h in k.lower() for h in FORBIDDEN_HINTS)})


def assert_no_scores(case, obj, where: str = "payload") -> None:
    hits = forbidden_keys(obj)
    case.assertEqual(hits, [], where + " must not carry score-like keys: " + repr(hits))


def find_ep003_dir():
    """Return the archived EP003 episode directory, if it still exists."""
    matches = sorted((REPO_ROOT / "episodes").glob(EP003_GLOB))
    for candidate in matches:
        if candidate.is_dir():
            return candidate
    return None

