#!/usr/bin/env python3
"""Stable business identity for assets observed by Story OS telemetry."""
from __future__ import annotations

import re
from pathlib import Path

import runtime_workspace


def episode_id(ep: str | Path) -> str:
    """Return stable repository Episode namespace, independent of DB availability."""
    return runtime_workspace.episode_namespace(Path(ep).resolve()).as_posix()


def frame_asset_key(ep: str | Path, frame_id: str | int) -> str:
    """Build the same logical key for a frame across attempts and file paths."""
    raw = str(frame_id).strip()
    match = re.fullmatch(r"(?:frame[-_ ]?)?(\d{1,4})", raw, re.IGNORECASE)
    if not match:
        raise ValueError(f"invalid frame identity: {frame_id!r}")
    return f"{episode_id(ep)}/frame-{int(match.group(1)):02d}"


def non_frame_asset_key(ep: str | Path, *segments: str) -> str:
    """Build a stable hierarchical key (for example visual-lock/P01)."""
    clean = []
    for segment in segments:
        value = str(segment or "").strip()
        if not value or value in {".", ".."} or "/" in value or "\\" in value:
            raise ValueError(f"invalid logical asset segment: {segment!r}")
        clean.append(value)
    if not clean:
        raise ValueError("at least one logical asset segment is required")
    return f"{episode_id(ep)}/" + "/".join(clean)
