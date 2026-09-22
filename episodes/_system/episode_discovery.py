#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical Story OS episode discovery.

Production Episodes are discovered through the configured Episode State authority.
Internal/test/archive trees and explicitly marked non-Episode reference sets are excluded.
"""
from __future__ import annotations

import json
from pathlib import Path

import episode_state_persistence

ROOT = Path(__file__).resolve().parents[2]
EPISODES = ROOT / "episodes"
STATE_REL = Path("meta/episode-state.json")
NON_EPISODE_MARKER = ".storyos-non-episode.json"
EXCLUDED_PARTS = {"_system", "_tests", "_archive", "__pycache__"}


def excluded(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(EPISODES.resolve())
    except ValueError:
        return True
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return True
    cur = path.resolve()
    while True:
        if (cur / NON_EPISODE_MARKER).is_file():
            return True
        if cur == EPISODES.resolve():
            break
        if EPISODES.resolve() not in cur.parents:
            break
        cur = cur.parent
    return False


def is_episode_root(path: Path) -> bool:
    ep = Path(path).resolve()
    if not ep.is_dir() or excluded(ep):
        return False
    mode = episode_state_persistence.authority_mode()
    if mode == "json":
        return (ep / STATE_REL).is_file()
    if mode == "dual" and (ep / STATE_REL).is_file():
        return True
    return episode_state_persistence.load(ep) is not None


def iter_episode_roots(episodes_root: Path | None = None) -> list[Path]:
    root = Path(episodes_root or EPISODES).resolve()
    rows: set[Path] = set()
    if not root.is_dir():
        return []
    mode = episode_state_persistence.authority_mode()
    if mode in {"json", "dual"}:
        for state in root.rglob(STATE_REL.as_posix()):
            ep = state.parents[1].resolve()
            if ep.is_dir() and not excluded(ep):
                rows.add(ep)
    if mode in {"dual", "mysql"}:
        canonical_root = EPISODES.resolve()
        for namespace in episode_state_persistence.list_episode_namespaces():
            candidate = (canonical_root / Path(str(namespace))).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            if candidate.is_dir() and not excluded(candidate):
                rows.add(candidate)
    return sorted(rows)


def iter_fingerprint_paths(episodes_root: Path | None = None) -> list[Path]:
    rows = []
    for ep in iter_episode_roots(episodes_root):
        p = ep / "meta/episode-fingerprint.json"
        if p.is_file():
            rows.append(p)
    return rows


def self_test() -> None:
    assert excluded(EPISODES / "_tests" / "fixture")
    assert excluded(EPISODES / "_system")
    assert excluded(EPISODES / "_archive" / "20260911_EP003_abandoned_fixture")
    assert all(
        "_tests" not in p.parts and "_system" not in p.parts and "_archive" not in p.parts
        for p in iter_episode_roots()
    )
    print("EPISODE DISCOVERY V2.6.1 H2 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
