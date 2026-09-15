#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asset boundary validation.

Production media and test/demo assets must stay isolated.
This gate is intentionally non-destructive: it only reports violations.
"""
from __future__ import annotations

from pathlib import Path

import story_json


TEST_ROOTS = (
    "assets/placeholders/",
    "assets/fixtures/",
    "assets/demo/",
)

PRODUCTION_ROOTS = (
    "/media/raw/",
    "/media/candidates/",
    "./media/approved/",
    "./media/publish/",
)


def is_test_asset(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(normalized.startswith(root) or f"/{root}" in f"/{normalized}" for root in TEST_ROOTS)


def check_asset_path(path: str) -> list[str]:
    """Return violations without modifying files."""
    normalized = path.replace("\\", "/")
    errors: list[str] = []

    if is_test_asset(normalized) and "/media/" in normalized:
        errors.append("placeholder/test asset cannot enter production media")

    if any(root in normalized for root in PRODUCTION_ROOTS):
        if is_test_asset(normalized):
            errors.append("production asset references test boundary")

    return errors


def classify(path: str) -> str:
    if is_test_asset(path):
        return "TEST_ASSET"
    return "PRODUCTION_OR_UNKNOWN"


def _candidate_path(value) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        raw = value.get("path") or value.get("output_path")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def production_asset_references(ep: Path) -> list[tuple[str, str]]:
    """Return paths that are authoritative production/release asset references."""
    ep = Path(ep).resolve()
    refs: list[tuple[str, str]] = []
    ledger = story_json.read_json(ep / "meta/production-ledger.json", default={})
    for frame, row in (ledger.get("frames") or {}).items():
        if not isinstance(row, dict):
            continue
        for field in ("current_candidate", "approved_asset"):
            path = _candidate_path(row.get(field))
            if path:
                refs.append((f"ledger.frames.{frame}.{field}", path))
        for index, attempt in enumerate(row.get("attempts") or []):
            if not isinstance(attempt, dict):
                continue
            path = _candidate_path(attempt.get("candidate"))
            if path:
                refs.append((f"ledger.frames.{frame}.attempts[{index}].candidate", path))

    manifest = story_json.read_json(ep / "meta/release-manifest.json", default={})
    release = manifest.get("release") or {}
    for field in ("publish_dir", "cover_path", "contact_sheet_path"):
        path = _candidate_path(release.get(field))
        if path:
            refs.append((f"manifest.release.{field}", path))
    return refs


def verify_episode(ep: Path) -> list[str]:
    errors: list[str] = []
    for where, path in production_asset_references(ep):
        if is_test_asset(path):
            errors.append(f"{where}: test/demo asset is forbidden in production: {path}")
    return errors


def self_test() -> None:
    assert classify("assets/placeholders/demo.png") == "TEST_ASSET"
    assert not check_asset_path("assets/placeholders/demo.png")
    assert check_asset_path("assets/placeholders/demo.png/media/raw/x.png")
    assert is_test_asset("episodes/_tests/x/assets/placeholders/demo.png")
    print("ASSET BOUNDARY GATE SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
