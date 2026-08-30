#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode fingerprint utility backed by the authoritative Recent-5 Release Guard."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from release_preflight import (
    RECENT5_REL,
    build_recent5,
    fingerprint_complete,
    load_registry,
    write_json,
)
from story_os_contract import story_os_version

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "standards" / "templates" / "episode-fingerprint.template.json"
REG = ROOT / "reports" / "account-pattern-registry.json"

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("episode_dir")

    p = sub.add_parser("register")
    p.add_argument("episode_dir")

    p = sub.add_parser("compare")
    p.add_argument("episode_dir")
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=1800)

    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    fp = ep / "meta" / "episode-fingerprint.json"

    if args.cmd == "init":
        if not fp.exists():
            data = read_json(TPL)
            data["story_os_version"] = story_os_version()
            write(fp, data)
        print(fp)
        return 0

    if not fp.exists():
        raise SystemExit("fingerprint missing")
    cur = read_json(fp)

    if args.cmd == "register":
        if not fingerprint_complete(cur):
            raise SystemExit("fingerprint incomplete")
        reg = load_registry()
        row = {
            "episode_id": cur["episode_id"],
            "title": cur["title"],
            "dimensions": cur["dimensions"],
            "source": "episode_fingerprint_register",
        }
        reg["story_os_version"] = story_os_version()
        reg["episodes"] = [
            x for x in reg.get("episodes", [])
            if isinstance(x, dict) and x.get("episode_id") != row["episode_id"]
        ] + [row]
        write(REG, reg)
        print("REGISTERED")
        return 0

    data = build_recent5(ep, codex=args.codex, timeout=args.timeout)
    write_json(ep / RECENT5_REL, data)
    for row in data.get("compared", []):
        exact = row.get("exact_similarity_score")
        semantic = row.get("semantic_similarity_score")
        effective = row.get("similarity_score")
        veto = row.get("mechanism_veto") is True
        semantic_text = "-" if semantic is None else str(semantic)
        print(
            f"{effective:03d} {'VETO' if veto else 'BLOCK' if effective >= 55 else 'PASS'} "
            f"exact={exact} semantic={semantic_text} {row.get('title', '')}"
        )
    print("DECISION:", data.get("decision"))
    return 0 if data.get("decision") == "pass" else 3

if __name__ == "__main__":
    raise SystemExit(main())
