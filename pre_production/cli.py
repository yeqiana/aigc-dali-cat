#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line entry point for Pre Production Intelligence.

Usage:
  python -m pre_production analyze <episode_dir> [--out-dir DIR] [--history PATH]...
  python -m pre_production shadow  <episode_dir> [--out-dir DIR] [--no-memory] [--dry-run]
  python -m pre_production validate <yaml_file> --kind dna|similarity|advisor|review
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .shadow_mode import analyze_episode, run_shadow, write_artifacts
from .story_dna.validator import (
    validate_advisor_report,
    validate_dna,
    validate_review_reference,
    validate_similarity_report,
)


def _load_yaml(path: Path | str) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def cmd_analyze(args) -> int:
    result = analyze_episode(args.episode_dir, repo_root=args.repo_root,
                             history_paths=tuple(args.history or ()), history_limit=args.limit)
    report = result["advisor_report"]
    print("episode_id :", report.get("episode_id"))
    print("title      :", report.get("title"))
    print("decision   :", report.get("decision"))
    print("confidence :", report.get("confidence"))
    print("history    :", result["similarity_report"].get("history_size"), "episode(s)")
    for risk in report.get("risks") or []:
        print("risk       : [{0}] {1}".format(risk.get("level"), risk.get("summary")))
    for token in report.get("recommendations") or []:
        print("suggest    :", token)
    issues = [item for group in result["issues"].values() for item in group]
    if issues:
        print("issues     :", "; ".join(issues))
    if args.out_dir:
        written = write_artifacts(result, args.out_dir)
        for name, path in written.items():
            print("written    :", name, "->", path)
    if args.json:
        print(json.dumps({
            "episode_id": report.get("episode_id"),
            "decision": report.get("decision"),
            "confidence": report.get("confidence"),
            "risks": report.get("risks"),
            "recommendations": report.get("recommendations"),
        }, ensure_ascii=False, indent=2))
    return 0


def cmd_shadow(args) -> int:
    payload = run_shadow(args.episode_dir, out_dir=args.out_dir, repo_root=args.repo_root,
                         history_paths=tuple(args.history or ()), history_limit=args.limit,
                         write_memory=not args.no_memory, memory_store=args.memory_store,
                         dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    # Shadow mode never blocks the production flow.
    return 0


def cmd_validate(args) -> int:
    data = _load_yaml(args.file)
    validators = {
        "dna": validate_dna,
        "similarity": validate_similarity_report,
        "advisor": validate_advisor_report,
        "review": validate_review_reference,
    }
    issues = validators[args.kind](data)
    if issues:
        for issue in issues:
            print("INVALID:", issue)
        return 1
    print("VALID:", args.kind, args.file)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pre_production", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("--repo-root", default=None)
        p.add_argument("--history", action="append", default=[])
        p.add_argument("--limit", type=int, default=None)

    p = sub.add_parser("analyze", help="analyze one episode (read-only unless --out-dir)")
    p.add_argument("episode_dir")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--json", action="store_true")
    add_common(p)
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("shadow", help="shadow-mode run that never blocks production")
    p.add_argument("episode_dir")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--memory-store", default=None)
    p.add_argument("--no-memory", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    add_common(p)
    p.set_defaults(func=cmd_shadow)

    p = sub.add_parser("validate", help="validate one generated artifact")
    p.add_argument("file")
    p.add_argument("--kind", required=True, choices=["dna", "similarity", "advisor", "review"])
    p.set_defaults(func=cmd_validate)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

