#!/usr/bin/env python3
"""Story OS one sentence episode bootstrap.

Purpose:
    Natural language request -> episode skeleton + Visual Lock draft.

This module only creates bootstrap assets. It does not replace Runtime DAG,
story gates, or workflow execution.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import visual_profile_selector
from visual_profile_lock_adapter import (
    build_selector_input,
    create_visual_lock_draft,
    lifecycle_of_lock,
    read_lock as read_visual_lock,
    selection_record,
    write_visual_lock_draft,
)
from visual_profile_resolver import infer_profile, resolve_profile


def slugify(title: str) -> str:
    title = re.sub(r"[^\w\u4e00-\u9fff]+", "_", title).strip("_")
    return title or "untitled_episode"


def create_episode(
    root: Path,
    title: str,
    visual_profile: str | None = None,
    *,
    story_intent: dict | None = None,
    selector_input: dict | None = None,
    episode_context: dict | None = None,
    audience_expectation: dict | None = None,
) -> Path:
    """Create an Episode skeleton and its Visual Lock draft.

    Visual Profile Governance Phase 4.1: the profile is chosen by the Selector
    (visual_profile_selector) from the declared Story Intent and recorded as a
    Visual Lock *draft* at meta/visual-profile.json. A draft is not a lock;
    confirmation belongs to a later phase.

    Selection happens before anything is written, so an invalid selector input or
    an unregistered profile id fails closed instead of leaving a half-created
    Episode. An Episode that already carries a Visual Lock is read, never
    re-selected and never overwritten.
    """
    root = Path(root)
    episode = root / "episodes" / slugify(title)
    existing_lock, existing_source = read_visual_lock(episode)

    if existing_lock is not None:
        # Read, do not re-select. A declared profile wins; an unmanaged lock keeps
        # the pre-Phase-4.1 resolution path.
        declared = str(existing_lock.get("profile_id") or "").strip()
        resolved = resolve_profile(
            declared or visual_profile or infer_profile(title, story_root=root),
            episode=episode,
            story_root=root,
        )
        lock_report = {
            "source": "existing",
            "written": False,
            "lock_path": existing_source,
            "lifecycle_state": lifecycle_of_lock(existing_lock),
            "selector_output": None,
            "draft": None,
            "profile_id": declared or None,
            "status": str(existing_lock.get("status") or "").strip() or None,
        }
    else:
        payload = selector_input if isinstance(selector_input, dict) else build_selector_input(
            story_intent=story_intent,
            episode_context=episode_context,
            audience_expectation=audience_expectation,
            forced_profile_id=visual_profile,
        )
        output = visual_profile_selector.select(payload, story_root=root, strict=True)
        draft = create_visual_lock_draft(payload, output, story_root=root)
        chosen = str(output.get("selected_profile") or "").strip()
        resolved = resolve_profile(chosen, episode=episode, story_root=root) if chosen else None
        lock_report = {
            "source": "selector",
            "written": False,
            "lock_path": None,
            "lifecycle_state": draft["lifecycle_state"],
            "selector_output": output,
            "draft": draft,
            "profile_id": chosen or None,
            "status": output["status"],
        }
        write_visual_lock_draft(episode, draft, story_root=root)
        lock_report["written"] = True
        lock_report["lock_path"] = "meta/visual-profile.json"

    meta = episode / "meta"
    meta.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    (meta / "episode-state.json").write_text(json.dumps({
        "episode_id": slugify(title),
        "title": title,
        "current_state": "IDEA_LOCKED",
        "created_at": now
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    request = {
        "schema_version": 1,
        "intent": "CREATE_EPISODE",
        "request": title,
        "execution_mode": "dag",
        "visual_profile": (resolved or {}).get("profile_id") or "",
        "visual_profile_resolution": {
            "source": resolved["source"] if resolved else None,
            "resolved_profile_id": resolved["profile_id"] if resolved else None,
            "requested_profile_id": (
                resolved.get("requested_profile_id", visual_profile) if resolved else None
            ),
            "registered": resolved.get("registered", True) if resolved else False,
            "fallback": resolved.get("fallback", False) if resolved else False,
            "resolution": resolved.get("resolution") if resolved else "needs_confirmation",
            "registry": "standards/visual_profiles/index.json",
        },
    }
    if lock_report["source"] == "selector":
        request["visual_profile_selection"] = selection_record(lock_report)

    (meta / "runtime-request.json").write_text(
        json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")

    return episode
