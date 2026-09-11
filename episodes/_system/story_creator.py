#!/usr/bin/env python3
"""Story OS one sentence episode bootstrap.

Purpose:
    Natural language request -> episode skeleton.

This module only creates bootstrap assets. It does not replace Runtime DAG,
story gates, or workflow execution.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from visual_profile_resolver import infer_profile, resolve_profile


def slugify(title: str) -> str:
    title = re.sub(r"[^\w\u4e00-\u9fff]+", "_", title).strip("_")
    return title or "untitled_episode"


def create_episode(root: Path, title: str, visual_profile: str | None = None) -> Path:
    visual_profile = visual_profile or infer_profile(title)
    episode = root / "episodes" / slugify(title)
    meta = episode / "meta"
    meta.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    (meta / "episode-state.json").write_text(json.dumps({
        "episode_id": slugify(title),
        "title": title,
        "current_state": "IDEA_LOCKED",
        "created_at": now
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    resolved = resolve_profile(visual_profile, episode=episode, story_root=root)

    (meta / "runtime-request.json").write_text(json.dumps({
        "schema_version": 1,
        "intent": "CREATE_EPISODE",
        "request": title,
        "execution_mode": "dag",
        "visual_profile": visual_profile,
        "visual_profile_resolution": {
            "source": resolved["source"],
            "resolved_profile_id": resolved["profile_id"]
        }
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    return episode
