#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed Unicode/UTF-8 health checks for Story OS semantic evidence."""
from __future__ import annotations

import json
from pathlib import Path

BAD_CODEPOINTS = {"\ufffd"}


def text_errors(value: str, *, label: str = "text") -> list[str]:
    errors: list[str] = []
    if any(ch in value for ch in BAD_CODEPOINTS):
        errors.append(f"{label} contains Unicode replacement character")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
        errors.append(f"{label} contains surrogate code point")
    try:
        if value.encode("utf-8").decode("utf-8") != value:
            errors.append(f"{label} fails UTF-8 roundtrip")
    except UnicodeError as exc:
        errors.append(f"{label} UTF-8 error: {exc}")
    return errors


def json_text_errors(data: object, *, label: str = "json") -> list[str]:
    errors: list[str] = []
    def walk(value: object, path: str) -> None:
        if isinstance(value, str):
            errors.extend(text_errors(value, label=path))
        elif isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                walk(child, f"{path}[{idx}]")
    walk(data, label)
    return errors


def file_errors(path: Path) -> list[str]:
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        return [f"{p}: invalid UTF-8: {exc}"]
    errors = text_errors(raw, label=str(p))
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
        except Exception as exc:
            return errors + [f"{p}: invalid JSON: {exc}"]
        errors.extend(json_text_errors(data, label=str(p)))
    return errors


def self_test() -> None:
    assert not text_errors("瓶中世界｜鳌太线·热汤")
    assert text_errors("bad\ufffdtext")
    print("TEXT ENCODING HEALTH V2.6.1 H2 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
