#!/usr/bin/env python3
"""Stable product aliases over the canonical Visual Profile Registry; no parallel authority."""
from __future__ import annotations
from pathlib import Path
import story_json

ROOT = Path(__file__).resolve().parents[2]
REL = Path("standards/style-registry.json")
def load(root: Path = ROOT) -> dict: return story_json.read_json(Path(root)/REL)
def resolve(style_id: str, *, root: Path = ROOT) -> dict:
    styles = load(root).get("styles") or {}
    style = styles.get(style_id)
    if not isinstance(style, dict): raise ValueError("STYLE_NOT_REGISTERED: " + str(style_id))
    return dict(style, style_id=style_id)
