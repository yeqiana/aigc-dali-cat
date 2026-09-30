#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Execution-only direct-user visual reference overlays.

These references are intentionally outside Resolved Frame Contract hash material.
They let a user bind an already-produced image as a generation reference without
invalidating every existing candidate in the Episode.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import episode_contract_persistence

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/user-visual-reference-contract.json")
CONTRACT_TYPE = "USER_VISUAL_REFERENCE"
ALLOWED_KINDS = {"identity", "prop", "location", "capture_style"}
ALLOWED_SCOPES = {"batch", "repair", "visual_lock"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _repo_file(raw: str) -> Path:
    p = Path(str(raw))
    p = p.resolve() if p.is_absolute() else (ROOT / p).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("user visual reference escapes repository") from exc
    if not p.is_file():
        raise ValueError(f"user visual reference missing: {raw}")
    return p


def load(ep: Path) -> dict:
    ep = Path(ep).resolve()
    data = episode_contract_persistence.load_latest(
        ep,
        CONTRACT_TYPE,
        legacy_path=ep / REL,
    )
    if data is None:
        return {"schema_version": 1, "items": []}
    if not isinstance(data, dict):
        raise ValueError("user visual reference contract must be an object")
    return data


def persist(ep: Path, payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("user visual reference contract must be an object")
    return episode_contract_persistence.save(
        Path(ep).resolve(),
        CONTRACT_TYPE,
        REL,
        payload,
        status="LOCKED",
    )


def references_for_frame(ep: Path, frame: int, scope: str) -> list[dict]:
    frame = int(frame)
    scope = str(scope or "batch")
    if scope not in ALLOWED_SCOPES:
        return []
    result: list[dict] = []
    for item in load(ep).get("items") or []:
        if not isinstance(item, dict) or str(item.get("decision") or "locked") not in {"locked", "pass", "passed"}:
            continue
        frames = {int(x) for x in (item.get("frames") or []) if str(x).isdigit()}
        if frames and frame not in frames:
            continue
        scopes = {str(x) for x in (item.get("scopes") or ["batch", "repair"])}
        if scope not in scopes:
            continue
        kind = str(item.get("kind") or item.get("reference_kind") or "")
        if kind not in ALLOWED_KINDS:
            raise ValueError(f"invalid user visual reference kind: {kind}")
        path = _repo_file(str(item.get("path") or ""))
        expected = str(item.get("sha256") or "").lower()
        actual = _sha256(path)
        if len(expected) != 64 or actual != expected:
            raise ValueError(f"user visual reference SHA drift: {path}")
        result.append({
            "id": item.get("id"),
            "path": path.relative_to(ROOT.resolve()).as_posix(),
            "role": str(item.get("role") or "user_visual_reference"),
            "kind": kind,
            "anchor": item.get("anchor") or item.get("id"),
            "sha256": actual,
        })
    return result
