#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS runtime-log retention policy and Git hygiene audit.

High-volume worker/trace logs are local derived diagnostics, not Story/Release
authority. This module never deletes files or mutates Git; it reports historical
tracked raw logs so maintainers can untrack/GC them deliberately.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_ONLY_PATTERNS = (
    "episodes/**/meta/image-workers/**",
    "episodes/**/meta/rolling-review-workers/**",
    "episodes/**/meta/scoped-workers/**",
    "episodes/**/meta/codex-auto-run.jsonl",
    "episodes/**/meta/runtime/trace-events.jsonl",
    "episodes/**/meta/workflow-run.jsonl",
)


def tracked_local_logs(root: Path = ROOT) -> list[Path]:
    if not (root / ".git").exists():
        return []
    cmd = ["git", "-C", str(root), "ls-files", "--", *LOCAL_ONLY_PATTERNS]
    cp = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if cp.returncode != 0:
        return []
    return [root / line.strip() for line in cp.stdout.splitlines() if line.strip()]


def audit(root: Path = ROOT) -> dict:
    tracked = tracked_local_logs(root)
    existing = [p for p in tracked if p.is_file()]
    total = sum(p.stat().st_size for p in existing)
    return {
        "schema_version": 1,
        "policy": "local_derived_not_git_authority",
        "tracked_historical_count": len(tracked),
        "tracked_existing_count": len(existing),
        "tracked_existing_bytes": total,
        "paths": [p.relative_to(root).as_posix() for p in existing],
        "action": "historical tracked logs may be git rm --cached then git gc; do not delete formal review JSON/SHA evidence",
    }


def self_test() -> None:
    assert "episodes/**/meta/image-workers/**" in LOCAL_ONLY_PATTERNS
    assert "episodes/**/meta/workflow-run.jsonl" in LOCAL_ONLY_PATTERNS
    print("RUNTIME LOG POLICY V2.6.1.1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["audit", "self-test"], nargs="?", default="audit")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
