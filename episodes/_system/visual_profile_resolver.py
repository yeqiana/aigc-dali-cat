#!/usr/bin/env python3
"""Story OS visual profile resolver (Visual Profile Governance Phase 2.1).

Resolve a Visual Profile reference through the registry
(standards/visual_profiles/index.json).

An unregistered profile id fails closed with VISUAL_PROFILE_NOT_REGISTERED. It is
never silently replaced by the default profile; the default is returned only when

  1. the caller did not ask for a profile at all (unspecified -> registry default), or
  2. the caller explicitly opts in with allow_fallback=True.

Resolution priority for a registered id:
  1. Episode local override    <episode>/assets/visual_profiles/<id>.json
  2. Registry path             standards/visual_profiles/<...>.json
  3. Legacy standards path     standards/visual_profiles/<id>.json
  4. Legacy sibling content repo (read-only compatibility probe)
"""
from __future__ import annotations

from pathlib import Path

import visual_profile_registry as registry

# Kept for backwards-compatible import. The authoritative default id is read
# from the registry (default_profile) at call time, never hardcoded here.
DEFAULT_PROFILE = "M00"


# Keyword routing hints. A route is inert until its target id is actually
# registered, so a planned-but-unshipped visual world can never leak into
# production as a silently accepted profile.
KEYWORD_ROUTES = [
    ("M00_HEAVEN_WORKER_DAILY_V1", ["天界", "云务", "送信", "天庭", "仙界工作"]),
    ("M00_ANCIENT_DAILY_LIFE_V1", ["江南", "古代", "姑娘", "书生", "茶", "卖花", "长安", "水乡"]),
]


def resolve_profile(
    profile_id: str | None,
    episode: Path | None = None,
    story_root: Path | None = None,
    allow_fallback: bool = False,
) -> dict:
    """Return resolved profile metadata and source path. Fails closed on unregistered ids."""
    return registry.resolve_registered_profile(
        profile_id,
        story_root=story_root,
        episode=episode,
        allow_fallback=allow_fallback,
    )


def infer_profile(title: str, story_root: Path | None = None) -> str:
    """Pick a Visual Profile for a title when the caller did not specify one.

    Only registered ids can be returned; unmatched titles fall back to the
    registry default profile because the profile is genuinely unspecified.
    """
    root = Path(story_root) if story_root else Path(__file__).resolve().parents[2]
    registered = set(registry.registry_ids(root))
    text = (title or "").lower()
    for profile_id, keywords in KEYWORD_ROUTES:
        if profile_id not in registered:
            continue
        if any(keyword.lower() in text for keyword in keywords):
            return profile_id
    return registry.default_profile_id(root)

