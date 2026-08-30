#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 dependency/invalidation matrix.

This module describes dirty propagation only. It never stores episode stage truth.
"""
from __future__ import annotations

import argparse
import json
from collections import deque

DEPENDENCIES = {
    "TOPIC": {"STORY", "STORYBOARD", "VISUAL", "FRAMES", "TEXT", "RELEASE"},
    "STORY": {"STORYBOARD", "VISUAL", "FRAMES", "TEXT", "RELEASE"},
    "STORYBOARD": {"VISUAL", "FRAMES", "TEXT", "RELEASE"},
    "AUTHENTICITY": {"VISUAL", "FRAMES", "RELEASE"},
    "CAPTURE_PROFILE": {"VISUAL", "FRAMES", "RELEASE"},
    "ENVIRONMENT": {"VISUAL", "FRAMES", "RELEASE"},
    "VISUAL_PROFILE": {"VISUAL", "FRAMES", "RELEASE"},
    "VISUAL": {"FRAMES", "RELEASE"},
    "FRAMES": {"TEXT", "RELEASE"},
    "TEXT": {"RELEASE"},
    "COVER": {"RELEASE"},
    "TITLE_DESCRIPTION": {"RELEASE"},
    "RELEASE": set(),
}


def affected(source: str) -> list[str]:
    root = source.strip().upper()
    if root not in DEPENDENCIES:
        raise ValueError(f"unknown source: {source}")
    seen: set[str] = set()
    q = deque([root])
    while q:
        cur = q.popleft()
        for nxt in sorted(DEPENDENCIES.get(cur, set())):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return sorted(seen)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("affected"); p.add_argument("source")
    sub.add_parser("show")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        assert "RELEASE" in affected("STORY")
        assert "FRAMES" in affected("ENVIRONMENT")
        assert affected("RELEASE") == []
        print("WORKFLOW DEPENDENCIES SELF-TEST PASS")
        return 0
    if args.cmd == "show":
        print(json.dumps({k: sorted(v) for k, v in DEPENDENCIES.items()}, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({"source": args.source.upper(), "affected": affected(args.source)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
