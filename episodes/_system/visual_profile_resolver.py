#!/usr/bin/env python3
"""Story OS visual profile resolver.

Resolve Visual Profile references without duplicating content-asset profiles.
Priority:
1. Episode local override
2. Story OS local standards
3. aigc-dali-cat content asset repository
4. Built-in default
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PROFILE = "M00_MP4_网吧_流水席_旧数码"


KEYWORD_ROUTES = [
    ("M00_HEAVEN_WORKER_DAILY_V1", ["天界", "云务", "送信", "天庭", "仙界工作"]),
    ("M00_ANCIENT_DAILY_LIFE_V1", ["江南", "古代", "姑娘", "书生", "茶", "卖花", "长安", "水乡"]),
]


def _load_profile(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def resolve_profile(profile_id: str | None, episode: Path | None = None, story_root: Path | None = None) -> dict[str, Any]:
    """Return resolved profile metadata and source path."""
    story_root = story_root or Path(__file__).resolve().parents[2]
    asset_root = story_root.parent / "aigc-dali-cat"

    candidates = []
    if episode:
        candidates.append(episode / "assets" / "visual_profiles" / f"{profile_id}.json")
    candidates.append(story_root / "standards" / "visual_profiles" / f"{profile_id}.json")
    candidates.append(asset_root / "standards" / "visual_profiles" / f"{profile_id}.json")

    for path in candidates:
        data = _load_profile(path)
        if data is not None:
            return {"profile_id": profile_id, "source": str(path), "profile": data}

    return {"profile_id": DEFAULT_PROFILE, "source": "default", "profile": {}}


def infer_profile(title: str) -> str:
    text = title.lower()
    for profile, keywords in KEYWORD_ROUTES:
        if any(k.lower() in text for k in keywords):
            return profile
    return DEFAULT_PROFILE
