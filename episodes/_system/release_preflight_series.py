#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_preflight series-lock domain (B4 split)."""

from __future__ import annotations

import argparse
from pathlib import Path
from story_os_contract import story_os_version
from release_preflight_core import *

def series_meta(ep: Path) -> Path:
    return ep.parent / "meta"

def series_lock_path(ep: Path) -> Path:
    return series_meta(ep) / "series-lock.json"

def series_continuity_path(ep: Path) -> Path:
    return series_meta(ep) / SERIES_CONTINUITY_NAME

def series_continuity_status(ep: Path) -> tuple[bool, list[str]]:
    """Return whether continuity is explicitly enabled plus declaration errors.

    Directory sibling count is intentionally NOT a signal. A content category may
    contain many unrelated episodes. Continuous-world semantics must be explicit.
    """
    p = series_continuity_path(ep)
    if not p.is_file():
        return False, []
    try:
        data = read_json(p)
    except Exception as exc:
        return True, [f"invalid series continuity declaration: {exc}"]
    enabled = data.get("enabled")
    if enabled is False:
        return False, []
    if enabled is not True:
        return True, ["series-continuity.json enabled must be true or false"]
    errors = []
    if not str(data.get("series_id") or "").strip():
        errors.append("series-continuity.json series_id required when enabled=true")
    return True, errors

def series_lock_required(ep: Path) -> bool:
    if not guard_required(ep):
        return False
    if series_lock_path(ep).is_file():
        return True
    enabled, _ = series_continuity_status(ep)
    return enabled

def write_series_continuity(series_dir: Path, series_id: str, source: str) -> Path:
    out = series_dir / "meta" / SERIES_CONTINUITY_NAME
    write_json(out, {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "enabled": True,
        "series_id": series_id.strip(),
        "declared_at": now(),
        "source": source,
    })
    return out

def cmd_declare_series(args: argparse.Namespace) -> int:
    series_dir = Path(args.series_dir).resolve()
    try:
        series_dir.relative_to((ROOT / "episodes").resolve())
    except ValueError:
        raise SystemExit("series_dir must be inside repository episodes/")
    if not series_dir.is_dir():
        raise SystemExit(f"series directory not found: {series_dir}")
    series_id = str(args.series_id or series_dir.name).strip()
    if not series_id:
        raise SystemExit("series_id must not be empty")
    out = write_series_continuity(series_dir, series_id, "explicit_declare_series")
    print(f"SERIES CONTINUITY: ENABLED {out.relative_to(ROOT)}")
    return 0

def cmd_init_series_lock(args: argparse.Namespace) -> int:
    series_dir = Path(args.series_dir).resolve()
    try:
        series_dir.relative_to((ROOT / "episodes").resolve())
    except ValueError:
        raise SystemExit("series_dir must be inside repository episodes/")
    source = Path(args.source).resolve()
    data = read_json(source)
    anchors = data.get("anchors")
    rules = data.get("world_rules")
    if not isinstance(anchors, list) or not anchors:
        raise SystemExit("series lock source requires non-empty anchors[]")
    if not isinstance(rules, list) or not rules:
        raise SystemExit("series lock source requires non-empty world_rules[]")
    data["schema_version"] = 1
    data["story_os_version"] = story_os_version()
    data["approved"] = True
    data["locked_at"] = now()
    series_id = str(data.get("series_id") or series_dir.name).strip()
    write_series_continuity(series_dir, series_id, "init_series_lock")
    out = series_dir / "meta/series-lock.json"
    write_json(out, data)
    print(f"SERIES LOCK: {out.relative_to(ROOT)} sha256={sha256_file(out)}")
    return 0

def cmd_bind_series(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    lock = series_lock_path(ep)
    if not lock.is_file():
        raise SystemExit("series-lock.json missing; run init-series-lock first")
    binding = {
        "schema_version": 1,
        "story_os_version": episode_contract_version(ep),
        "series_lock_path": repo_rel(lock),
        "series_lock_sha256": sha256_file(lock),
        "bound_at": now(),
    }
    write_json(ep / "meta/series-lock-binding.json", binding)
    print("SERIES BIND: PASS")
    return 0

def verify_series_lock(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    declared, declaration_errors = series_continuity_status(ep)
    lock = series_lock_path(ep)
    if not lock.is_file() and not declared:
        return []
    errors = list(declaration_errors)
    binding = ep / "meta/series-lock-binding.json"
    if not lock.is_file():
        errors.append("explicit continuous series requires <series>/meta/series-lock.json")
        return errors
    if not binding.is_file():
        return ["meta/series-lock-binding.json missing; run bind-series"]
    try:
        ld = read_json(lock)
        bd = read_json(binding)
    except Exception as exc:
        return [str(exc)]
    if ld.get("approved") is not True:
        errors.append("series lock must be approved=true")
    if not isinstance(ld.get("world_rules"), list) or not ld.get("world_rules"):
        errors.append("series lock world_rules[] required")
    if not isinstance(ld.get("anchors"), list) or not ld.get("anchors"):
        errors.append("series lock anchors[] required")
    for idx, row in enumerate(ld.get("anchors") or []):
        if not isinstance(row, dict) or not str(row.get("id") or "").strip() or not str(row.get("contract") or "").strip():
            errors.append(f"series lock anchor[{idx}] requires id + contract")
    actual = sha256_file(lock)
    if str(bd.get("series_lock_sha256") or "").lower() != actual.lower():
        errors.append("series lock SHA drift; re-bind episode")
    if str(bd.get("series_lock_path") or "") != repo_rel(lock):
        errors.append("series lock binding path mismatch")
    return errors

