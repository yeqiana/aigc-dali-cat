#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode-local final acceptance evidence reader (Story OS controlled exception).

A valid <episode>/meta/final-acceptance.json records that the direct user
accepted the current approved assets as final and accepts known defects on
publish. Gates honor it only for the episode that carries the file; every other
episode keeps full enforcement. Removing the file restores full gates.
"""
from __future__ import annotations
import json
from pathlib import Path

REL = Path("meta/final-acceptance.json")


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid(episode_dir) -> dict | None:
    """Return the acceptance payload when valid for gates, else None."""
    ep = Path(episode_dir).resolve()
    path = ep / REL
    if not path.is_file():
        return None
    try:
        data = read_json(path)
    except Exception:
        return None
    if data.get("schema_version") != 1:
        return None
    if data.get("decision") != "accept_current_as_final":
        return None
    if data.get("basis") != "direct_user_review":
        return None
    if data.get("accepted_assets") is not True:
        return None
    if data.get("revokes") is True:
        return None
    if not _nonempty(data.get("user_statement")):
        return None
    if not _nonempty(data.get("declared_at")):
        return None
    frames = data.get("known_defect_frames")
    if not isinstance(frames, list) or not frames:
        return None
    return data


def covers(episode_dir, frame) -> bool:
    data = valid(episode_dir)
    if data is None:
        return False
    wanted = f"{int(frame):02d}"
    known = {f"{int(x):02d}" for x in data.get("known_defect_frames", [])}
    return wanted in known
