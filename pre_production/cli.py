#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line entry point for Pre Production Intelligence.

Usage:
  python -m pre_production analyze <episode_dir> [--out-dir DIR] [--history PATH]...
  python -m pre_production shadow  <episode_dir> [--out-dir DIR] [--no-memory] [--dry-run]
  python -m pre_production observe record   <episode_dir> [--ledger LEDGER] [--dry-run]
  python -m pre_production observe feedback --report ADVISOR_REPORT [--store DIR] [--dry-run]
  python -m pre_production observe list     [--ledger LEDGER] [--episode ID] [--json]
  python -m pre_production validate <yaml_file> --kind dna|similarity|advisor|review|feedback|observation
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .shadow_mode import analyze_episode, run_shadow, write_artifacts
from .shadow_observation.feedback import (
    DEFAULT_FEEDBACK_DIR,
    build_feedback,
    save_feedback,
    unknown_evidence_refs,
)
from .shadow_observation.ledger import (
    DEFAULT_LEDGER_PATH,
    append_entry,
    build_entry,
    scan_ledger,
    summarize,
)
from .similarity_analysis.retrieval import REPO_ROOT
from .story_dna.schema import load_contract
from .story_dna.validator import (
    validate_advisor_feedback,
    validate_advisor_report,
    validate_dna,
    validate_observation_entry,
    validate_review_reference,
    validate_similarity_report,
)

_CREATOR_DECISIONS = list(load_contract("advisor_feedback.schema.json")["creator_decisions"])
_ACCURACY_LEVELS = list(load_contract("advisor_feedback.schema.json")["advisor_accuracy_levels"])


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



def _observe_record(args) -> int:
    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER_PATH
    result = analyze_episode(args.episode_dir, repo_root=args.repo_root,
                             history_paths=tuple(args.history or ()), history_limit=args.limit)
    report = result["advisor_report"]
    artifact_dir = None
    if args.out_dir and not args.dry_run:
        artifact_dir = args.out_dir
    entry = build_entry(report, similarity_report=result["similarity_report"],
                        artifact_dir=artifact_dir)
    if args.dry_run:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        print("dry-run    : ledger not written")
        return 0
    outcome = append_entry(ledger, entry)
    print("status     :", outcome["status"])
    print("observation:", entry["observation_id"])
    print("episode_id :", entry["episode_id"])
    print("decision   :", entry["decision"], "| highest_risk_level:", entry["highest_risk_level"])
    print("ledger     :", outcome["path"], "| rows:", outcome["total_entries"])
    print("note       : derived non-authority record; it never blocks production")
    return 0


def _observe_feedback(args) -> int:
    report = _load_yaml(args.report)
    if not report:
        print("ERROR: could not load advisor report:", args.report)
        return 1
    feedback = build_feedback(report, creator_decision=args.decision,
                              advisor_accuracy=args.accuracy,
                              confirmed_evidence=tuple(args.confirmed or ()),
                              refuted_evidence=tuple(args.refuted or ()),
                              missed_risks=tuple(args.missed or ()),
                              notes=args.notes or "")
    unknown = unknown_evidence_refs(feedback, report)
    print("feedback_id       :", feedback["feedback_id"])
    print("advisor_report_id :", feedback["advisor_report_id"])
    print("judgement_source  :", feedback["judgement_source"], "(human-only)")
    print("creator_decision  :", feedback["creator_decision"])
    print("advisor_accuracy  :", feedback["advisor_accuracy"])
    if args.dry_run:
        print(json.dumps(feedback, ensure_ascii=False, indent=2))
        print("dry-run           : feedback not written")
        return 0
    path = save_feedback(feedback, store_dir=args.store)
    print("written           :", path)
    if unknown:
        print("warning           : evidence ids not declared by the report:", ", ".join(unknown))
    return 0


def _observe_list(args) -> int:
    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER_PATH
    entries, malformed = scan_ledger(ledger)
    if args.episode:
        entries = [entry for entry in entries if str(entry.get("episode_id")) == args.episode]
    summary = summarize(entries)
    if args.json:
        print(json.dumps({"entries": entries, "summary": summary, "malformed": malformed},
                         ensure_ascii=False, indent=2))
        return 0
    print("ledger    :", ledger, "| exists:", Path(ledger).is_file())
    print("rows      :", summary["observations"], "| episodes:", summary["episodes"],
          "| with_feedback:", summary["with_feedback"])
    print("by_decision:", summary["by_decision"], "| by_highest_risk_level:",
          summary["by_highest_risk_level"])
    for entry in entries:
        print("  ", entry.get("observation_id"), entry.get("episode_id"),
              entry.get("decision"), entry.get("highest_risk_level"),
              "feedback=" + str(entry.get("feedback_id")))
    for item in malformed:
        print("malformed : line", item["line"], item["error"])
    return 0


def cmd_observe(args) -> int:
    if args.observe_cmd == "record":
        return _observe_record(args)
    if args.observe_cmd == "feedback":
        return _observe_feedback(args)
    if args.observe_cmd == "list":
        return _observe_list(args)
    print("ERROR: unknown observe action:", args.observe_cmd)
    return 2


def cmd_validate(args) -> int:
    data = _load_yaml(args.file)
    validators = {
        "dna": validate_dna,
        "similarity": validate_similarity_report,
        "advisor": validate_advisor_report,
        "review": validate_review_reference,
        "feedback": validate_advisor_feedback,
        "observation": validate_observation_entry,
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
    p.add_argument("--kind", required=True,
                   choices=["dna", "similarity", "advisor", "review", "feedback", "observation"])
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("observe", help="shadow observation ledger and human advisor feedback")
    obs = p.add_subparsers(dest="observe_cmd", required=True)

    r = obs.add_parser("record", help="record one shadow observation of an episode")
    r.add_argument("episode_dir")
    r.add_argument("--ledger", default=None)
    r.add_argument("--out-dir", default=None)
    r.add_argument("--dry-run", action="store_true")
    add_common(r)
    r.set_defaults(func=cmd_observe)

    f = obs.add_parser("feedback", help="record a human judgement of one advisor report")
    f.add_argument("--report", required=True, help="path to advisor_report.yaml")
    f.add_argument("--store", default=None, help="feedback store directory")
    f.add_argument("--decision", default="pending", choices=_CREATOR_DECISIONS)
    f.add_argument("--accuracy", default="unknown", choices=_ACCURACY_LEVELS)
    f.add_argument("--confirmed", action="append", default=[], help="confirmed evidence_id")
    f.add_argument("--refuted", action="append", default=[], help="refuted evidence_id")
    f.add_argument("--missed", action="append", default=[], help="risk the advisor missed")
    f.add_argument("--notes", default="")
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(func=cmd_observe)

    l = obs.add_parser("list", help="list recorded shadow observations")
    l.add_argument("--ledger", default=None)
    l.add_argument("--episode", default=None)
    l.add_argument("--json", action="store_true")
    l.set_defaults(func=cmd_observe)

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
