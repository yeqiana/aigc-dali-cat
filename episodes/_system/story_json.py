#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS canonical JSON document I/O.

Single implementation source for the deterministic JSON persistence used by
Story OS runtime modules:

- read: UTF-8(-sig) tolerant; strict mode keeps existing raise-on-error
  behavior, lenient mode keeps the runtime_atomic_store fallback contract.
- write: ensure_ascii=False, indent=2, LF terminator, atomic os.replace
  commit (no partial files visible to readers).

Modules with private read_json/write_json should delegate here with the same
semantics they had; this module is not a second behavior authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import runtime_atomic_store as atomic

_UNSET = object()


def read_json(path: Path | str, *, default: Any = _UNSET,
              require_object: bool = True) -> Any:
    """Read one JSON document.

    strict mode (default omitted): missing file raises FileNotFoundError,
    malformed JSON raises json.JSONDecodeError, and a non-object root raises
    ValueError when require_object=True. This preserves modules that already
    failed loudly on bad evidence.

    lenient mode (default passed): any missing/bad read or non-object root
    returns `default`. This preserves runtime_atomic_store.read_json and
    other fail-soft telemetry readers.
    """
    p = Path(path)
    if default is not _UNSET:
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            return default
        if require_object and not isinstance(data, dict):
            return default
        return data
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if require_object and not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {p}")
    return data


def write_json(path: Path | str, data: Any) -> None:
    """Deterministic atomic JSON write (UTF-8, LF, indent=2, trailing LF)."""
    atomic.atomic_write_json(Path(path), data)


def json_text(data: Any) -> str:
    """Deterministic text form used before atomic write (mostly for tests)."""
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def self_test() -> None:
    import tempfile
    with tempfile.TemporaryDirectory(prefix="story json self test ") as td:
        p = Path(td) / "nested" / "a.json"
        payload = {"t": "中文帧", "n": 1, "ok": True}
        write_json(p, payload)
        assert read_json(p) == payload
        text = p.read_text(encoding="utf-8")
        assert text.endswith("\n") and "\r" not in text
        assert read_json(p / "missing.json", default={}) == {}
        try:
            read_json(p / "missing.json")
            raise AssertionError("strict missing read must raise")
        except FileNotFoundError:
            pass
    print("STORY JSON SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

