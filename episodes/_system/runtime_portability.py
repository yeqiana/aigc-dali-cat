#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable path guards for Story OS runtime evidence.

Formal path fields must be repository-relative. Diagnostic strings may mention
absolute paths, but they are normalized before persistence so worktree moves do
not poison resume/debug evidence.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_WINDOWS_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_ABS_EPISODE_IN_TEXT = re.compile(r"[A-Za-z]:[\\/][^\r\n]*?[\\/]episodes[\\/]", re.IGNORECASE)


def is_absolute_like(raw: object) -> bool:
    text = str(raw or "").strip()
    return bool(text and (_WINDOWS_ABS.match(text) or Path(text).is_absolute()))


def validate_repo_relative(raw: object, *, field: str) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    if is_absolute_like(text):
        return [f"{field} must be repository-relative, got absolute path"]
    p = Path(text)
    if ".." in p.parts:
        return [f"{field} must not escape repository"]
    return []


def validate_episode_directory(path: Path) -> list[str]:
    """Reject repository-local pseudo Episodes outside the canonical episodes root."""
    resolved = Path(path).resolve()
    try:
        rel = resolved.relative_to(ROOT.resolve())
    except ValueError:
        # External unit-test fixtures are allowed; production paths inside this
        # checkout must live below episodes/.
        return []
    parts = rel.parts
    if len(parts) < 2 or parts[0] != "episodes" or parts[1] == "_system":
        return [f"episode directory must be under episodes/, got {rel.as_posix() or '.'}"]
    return []


def assert_episode_directory(path: Path) -> None:
    errors = validate_episode_directory(path)
    if errors:
        raise ValueError(errors[0])


def episode_label(path: Path) -> str:
    """Portable evidence label for a formal Episode or an external test fixture."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        # External fixtures are permitted by validate_episode_directory() for unit
        # tests, but persisted/derived evidence must never embed machine-specific
        # absolute paths.
        return f"external-fixture/{resolved.name}"


def sanitize_diagnostic_text(raw: object) -> str:
    text = str(raw or "")
    root_text = str(ROOT.resolve())
    text = text.replace(root_text + "\\", "").replace(root_text + "/", "")
    text = _ABS_EPISODE_IN_TEXT.sub("episodes/", text)
    return text.replace("\\", "/")


def queue_path_errors(queue: dict) -> list[str]:
    errors: list[str] = []
    for idx, item in enumerate(queue.get("items") or []):
        if not isinstance(item, dict):
            continue
        for key in ("prompt_file", "output_path", "log_path"):
            errors.extend(validate_repo_relative(item.get(key), field=f"items[{idx}].{key}"))
        for ridx, ref in enumerate(item.get("references") or []):
            if isinstance(ref, dict):
                errors.extend(validate_repo_relative(ref.get("path"), field=f"items[{idx}].references[{ridx}].path"))
    return errors


def self_test() -> None:
    assert validate_repo_relative("episodes/x/meta/a.json", field="x") == []
    assert validate_repo_relative("D:/repo/episodes/x/a.png", field="x")
    assert "D:" not in sanitize_diagnostic_text(r"D:\repo\episodes\x\meta\a.json")
    print("RUNTIME PORTABILITY V2.6.1 H2 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
