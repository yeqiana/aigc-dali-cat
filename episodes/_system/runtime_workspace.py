#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""External Runtime Workspace path resolver with legacy Episode fallback.

The Episode remains the authority boundary. This module only relocates mutable
operational state and rebuildable caches; it never relocates canonical authority
or formal evidence by itself.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any

import story_json

ROOT = Path(__file__).resolve().parents[2]
EPISODES_ROOT = ROOT / "episodes"
ENV_ROOT = "STORY_OS_RUNTIME_WORKSPACE"
DEFAULT_ROOT = ROOT / ".storyos" / "runtime" / "episodes"


def _safe_rel(rel: str | Path | PurePosixPath) -> Path:
    normalized = str(rel).replace("\\", "/")
    posix = PurePosixPath(normalized)
    path = Path(normalized)
    if (
        posix.is_absolute()
        or path.is_absolute()
        or bool(path.drive)
        or normalized.startswith("/")
        or any(part in {"", ".."} for part in posix.parts)
    ):
        raise ValueError(f"runtime relative path required: {rel}")
    return path


def runtime_root() -> Path:
    raw = os.environ.get(ENV_ROOT, "").strip()
    if not raw:
        return DEFAULT_ROOT.resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def episode_namespace(ep: str | Path) -> Path:
    resolved = Path(ep).resolve()
    try:
        rel = resolved.relative_to(EPISODES_ROOT.resolve())
        if rel.parts and all(part not in {".", ".."} for part in rel.parts):
            return rel
    except ValueError:
        pass
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]
    return Path("_external") / digest


def legacy_path(ep: str | Path, rel: str | Path | PurePosixPath) -> Path:
    return Path(ep).resolve() / _safe_rel(rel)


def workspace_path(ep: str | Path, rel: str | Path | PurePosixPath) -> Path:
    return runtime_root() / episode_namespace(ep) / _safe_rel(rel)


def read_candidates(ep: str | Path, rel: str | Path | PurePosixPath) -> tuple[Path, Path]:
    """Return new workspace first, legacy Episode path second."""
    return workspace_path(ep, rel), legacy_path(ep, rel)


def resolve_read_path(ep: str | Path, rel: str | Path | PurePosixPath) -> Path:
    """Prefer the external Runtime Workspace, then fall back to legacy Episode data."""
    workspace, legacy = read_candidates(ep, rel)
    if workspace.is_file():
        return workspace
    if legacy.is_file():
        return legacy
    return workspace


def read_json(ep: str | Path, rel: str | Path | PurePosixPath, default: Any = None) -> Any:
    path = resolve_read_path(ep, rel)
    return story_json.read_json(path, default=default, require_object=False)


def write_json(ep: str | Path, rel: str | Path | PurePosixPath, data: Any) -> Path:
    """Write only to the external Runtime Workspace using canonical atomic JSON I/O."""
    path = workspace_path(ep, rel)
    story_json.write_json(path, data)
    return path


def source_kind(ep: str | Path, rel: str | Path | PurePosixPath) -> str:
    path = resolve_read_path(ep, rel)
    if path == workspace_path(ep, rel) and path.is_file():
        return "runtime_workspace"
    if path == legacy_path(ep, rel) and path.is_file():
        return "legacy_episode"
    return "missing"
