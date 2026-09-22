#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Historical Episode DNA retrieval.

History is read from Story Lock documents (the story authority), never from
invented data. Every sample keeps the Story Lock path and SHA so a similarity
finding can be traced back to a real source.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..story_dna.extractor import extract_story_dna, find_story_lock, resolve_story_id

REPO_ROOT = Path(__file__).resolve().parents[2]
SKIP_TOP_PARTS = {"_system", "_tests", "_candidates", "__pycache__", "meta"}


@dataclass
class HistoricalSample:
    episode_id: str
    title: str
    source_path: str
    dna: dict
    alias: str = ""

    def summary(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "title": self.title,
            "source_path": self.source_path,
        }


def _episode_dir_for(lock_path: Path, root: Path) -> Path:
    """Nearest ancestor holding a meta/ directory, else the docs/story parent."""
    cur = lock_path.parent
    while True:
        if (cur / "meta").is_dir():
            return cur
        if cur == root or cur.parent == cur:
            break
        cur = cur.parent
    if lock_path.parent.name in {"docs", "story"}:
        return lock_path.parent.parent
    return lock_path.parent


def discover_story_locks(repo_root: Path | str = REPO_ROOT,
                         exclude_dirs: tuple = ()) -> list[Path]:
    """Find every Story Lock markdown under episodes/ (excluding test systems)."""
    root = Path(repo_root)
    episodes = root / "episodes"
    if not episodes.is_dir():
        return []
    excluded = {Path(p).resolve() for p in exclude_dirs}
    found: list[Path] = []
    for path in episodes.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        if "storylock" not in path.name.lower():
            continue
        rel_parts = path.relative_to(episodes).parts
        if any(part in SKIP_TOP_PARTS or part.startswith("_") for part in rel_parts[:-1]):
            continue
        ep_dir = _episode_dir_for(path.resolve(), root)
        if ep_dir.resolve() in excluded:
            continue
        found.append(path)
    found.sort()
    return found


def load_sample(lock_path: Path | str, repo_root: Path | str = REPO_ROOT) -> HistoricalSample:
    """Extract a historical DNA sample from one Story Lock file."""
    path = Path(lock_path).resolve()
    ep_dir = _episode_dir_for(path, Path(repo_root))
    dna = extract_story_dna(story_lock_path=path, episode_dir=ep_dir)
    story_id = dna.get("story_id") or resolve_story_id(ep_dir)
    source_path = (dna.get("source") or {}).get("story_lock_path") or str(path)
    return HistoricalSample(
        episode_id=str(story_id),
        title=str(dna.get("title") or ""),
        source_path=str(source_path),
        dna=dna,
    )


def _resolve_explicit(entry: Path | str) -> Path | None:
    path = Path(entry)
    if path.is_dir():
        return find_story_lock(path)
    if path.is_file():
        return path
    return None


def build_history(repo_root: Path | str = REPO_ROOT,
                  exclude_dirs: tuple = (),
                  explicit_paths: tuple = (),
                  limit: int | None = None) -> list[HistoricalSample]:
    """Build the historical sample list, deduplicated by episode id."""
    root = Path(repo_root)
    lock_paths: list[Path] = []
    for entry in explicit_paths or ():
        resolved = _resolve_explicit(entry)
        if resolved is not None:
            lock_paths.append(resolved)
    lock_paths.extend(discover_story_locks(root, exclude_dirs=exclude_dirs))

    history: list[HistoricalSample] = []
    seen: set[str] = set()
    for path in lock_paths:
        try:
            sample = load_sample(path, repo_root=root)
        except Exception:
            continue
        if not sample.episode_id or sample.episode_id in seen:
            continue
        seen.add(sample.episode_id)
        history.append(sample)
        if limit is not None and len(history) >= limit:
            break
    return history


__all__ = ["HistoricalSample", "build_history", "discover_story_locks", "load_sample"]

