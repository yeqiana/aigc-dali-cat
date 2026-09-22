#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line entry point for Pre Production Intelligence.

Usage:
  python -m pre_production analyze <episode_dir> [--out-dir DIR] [--history PATH]...
  python -m pre_production shadow  <episode_dir> [--out-dir DIR] [--no-memory] [--dry-run]
  python -m pre_production observe record   [episode_dir] [--report ADVISOR_REPORT] [--ledger LEDGER] [--dry-run]
  python -m pre_production observe feedback --report ADVISOR_REPORT --creator-decision D --recommendation-result R --risk-acknowledged yes|no [--dry-run]
  python -m pre_production observe list     [--ledger LEDGER] [--episode ID] [--json]
  python -m pre_production experience save  --feedback PFB-*.json [--store DIR] [--observation OBS|FILE] [--similarity SIMILARITY_REPORT] [--dry-run]
  python -m pre_production experience query [--episode ID] [--story-dna REF] [--risk-type TYPE] [--token T]... [--limit N] [--json]
  python -m pre_production experience list  [--kind all|experience|pattern|decision] [--episode ID] [--json]
  python -m pre_production experience stats [--store DIR] [--feedback-store DIR] [--ledger PATH] [--json]
  python -m pre_production validate <yaml_file> --kind dna|similarity|advisor|review|feedback|observation
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .memory_adapter import (
    KIND_DECISION,
    KIND_EXPERIENCE,
    KIND_PATTERN,
    KINDS,
    JsonlExperienceStore,
    collect_stats,
    format_stats,
    ingest_feedback,
    pattern_from_evidence,
    validate_risk_pattern,
)
from .observation import (
    CREATOR_DECISIONS,
    DEFAULT_LEDGER_PATH,
    RECOMMENDATION_RESULTS,
    apply_feedback,
    build_feedback,
    find_record,
    read_records,
    run_observation,
    save_feedback,
    scan_ledger,
    summarize,
    validate_feedback,
    validate_observation_record,
)
from .shadow_mode import analyze_episode, run_shadow, write_artifacts
from .similarity_analysis.retrieval import REPO_ROOT
from .story_dna.validator import (
    validate_advisor_report,
    validate_dna,
    validate_review_reference,
    validate_similarity_report,
)


def _load_yaml(path: Path | str) -> dict:
    """Load one YAML mapping; an unreadable or malformed file yields {}."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError):
        return {}
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
    report = None
    if args.report:
        report = _load_yaml(args.report)
        if not report:
            print("ERROR: could not load advisor report:", args.report)
            return 1
    payload = run_observation(
        None if report else args.episode_dir,
        advisor_report=report,
        ledger=ledger,
        repo_root=args.repo_root,
        history_paths=tuple(args.history or ()),
        history_limit=args.limit,
        feedback_store=args.feedback_store,
        dry_run=args.dry_run,
    )
    print("ok         :", payload["ok"])
    print("observation:", payload["observation_id"])
    print("episode_id :", payload["episode_id"])
    print("decision   :", payload["advisor_decision"])
    print("status     :", payload["observation_status"])
    print("ledger     :", payload["ledger"])
    for err in payload["errors"]:
        print("error      :", err)
    print("note       : advisory only; blocks_production =", payload["blocks_production"])
    return 0 if payload["ok"] else 1


def _observe_feedback(args) -> int:
    report = _load_yaml(args.report)
    if not report:
        print("ERROR: could not load advisor report:", args.report)
        return 1
    feedback = build_feedback(
        report,
        creator_decision=args.creator_decision,
        recommendation_result=args.recommendation_result,
        risk_acknowledged=(args.risk_acknowledged == "yes"),
        revision_direction=args.revision_direction,
        final_effect=args.final_effect,
        notes=args.notes,
    )
    print("feedback_id           :", feedback["feedback_id"])
    print("episode_id            :", feedback["episode_id"])
    print("advisor_decision      :", feedback["advisor_decision"])
    print("creator_decision      :", feedback["creator_decision"])
    print("recommendation_result :", feedback["recommendation_result"])
    print("risk_acknowledged     :", feedback["risk_acknowledged"])
    print("judgement_source      :", feedback["judgement_source"], "(human-only)")
    if args.dry_run:
        print(json.dumps(feedback, ensure_ascii=False, indent=2))
        print("dry-run               : feedback not written")
        return 0
    path = save_feedback(feedback, store_dir=args.store)
    print("written               :", path)
    if args.no_update:
        return 0
    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER_PATH
    updated = apply_feedback(feedback, ledger=ledger)
    print("observation           :", updated["observation_id"], "->", updated["observation_status"])
    for err in updated["errors"]:
        print("warning               : observation not updated:", err)
    return 0


def _observe_list(args) -> int:
    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER_PATH
    raw_rows, malformed = scan_ledger(ledger)
    records = read_records(ledger)
    if args.episode:
        records = [record for record in records if str(record.get("episode_id")) == args.episode]
    summary = summarize(records)
    if args.json:
        print(json.dumps({"records": records, "summary": summary, "malformed": malformed},
                         ensure_ascii=False, indent=2))
        return 0
    print("ledger    :", ledger, "| exists:", Path(ledger).is_file())
    print("rows      :", len(raw_rows), "| observations:", summary["observations"],
          "| episodes:", summary["episodes"], "| with_feedback:", summary["with_feedback"])
    print("by_status :", summary["by_status"])
    for record in records:
        print("  ", record.get("observation_id"), record.get("episode_id"),
              record.get("observation_status"),
              "feedback=" + str(record.get("creator_feedback_reference")))
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


def _load_json(path):
    """Load one JSON mapping; an unreadable or malformed file yields None."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _experience_store(args) -> JsonlExperienceStore:
    return JsonlExperienceStore(getattr(args, "store", None))


def _resolve_observation(args):
    """Resolve --observation to a record: a JSON file path, else an observation id."""
    value = getattr(args, "observation", None)
    if not value:
        return None
    path = Path(value)
    if path.is_file():
        return _load_json(path)
    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER_PATH
    record = find_record(ledger, value)
    if record is None:
        print("warning    : observation not found in the ledger, keeping the reference only:", value)
        return {"observation_id": value}
    return record


def _record_line(kind: str, record: dict) -> str:
    """One plain read-only line for the CLI; no sort, no score, no judgement."""
    if kind == KIND_PATTERN:
        return " ".join([
            str(record.get("pattern_id")),
            str(record.get("risk_type")),
            str(record.get("pattern_description")),
            "episodes=" + ",".join(str(item) for item in record.get("related_episode") or []),
        ])
    if kind == KIND_DECISION:
        return " ".join([
            str(record.get("decision_experience_id")),
            str(record.get("episode_id")),
            str(record.get("advisor_decision")),
            "->",
            str(record.get("creator_action")),
            str(record.get("recommendation_result")),
        ])
    return " ".join([
        str(record.get("experience_id")),
        str(record.get("episode_id")),
        str(record.get("advisor_report_reference")),
    ])


def _patterns_from_similarity(similarity: dict) -> list:
    """Risk patterns from a similarity report; incomplete evidence is skipped."""
    records: list = []
    for item in similarity.get("evidence") or []:
        if not isinstance(item, dict) or not item.get("matched_features"):
            continue
        record = pattern_from_evidence(item)
        if not validate_risk_pattern(record):
            records.append(record)
    return records


def _experience_save(args) -> int:
    feedback = _load_json(args.feedback)
    if not feedback:
        print("ERROR: could not load advisor feedback:", args.feedback)
        return 1
    patterns = []
    if args.similarity:
        similarity = _load_yaml(args.similarity)
        if not similarity:
            print("ERROR: could not load similarity report:", args.similarity)
            return 1
        patterns = _patterns_from_similarity(similarity)
    store = _experience_store(args)
    try:
        payload = ingest_feedback(
            feedback,
            store=store,
            observation=_resolve_observation(args),
            story_dna_reference=args.story_dna_reference or "",
            production_outcome=args.production_outcome,
            dry_run=args.dry_run,
        )
        pattern_status = []
        for record in patterns:
            pattern_status.append("DRY_RUN" if args.dry_run
                                  else store.save_risk_pattern(record)["status"])
    except (ValueError, OSError) as exc:
        # The store raises on a rejected record; the CLI reports it and stops.
        print("ERROR:", type(exc).__name__ + ":", exc)
        return 1
    print("episode_id            :", payload["episode_id"])
    print("experience_id         :", payload["experience_id"], "->", payload["experience_status"])
    print("decision_experience_id:", payload["decision_experience_id"], "->", payload["decision_status"])
    if patterns:
        print("risk_patterns         :", len(patterns), "->", ",".join(pattern_status))
    print("advisor_report_ref    :", payload["advisor_report_reference"])
    print("observation_ref       :", payload["observation_reference"])
    print("feedback_ref          :", payload["feedback_reference"])
    print("store_dir             :", payload["store_dir"])
    if payload["dry_run"]:
        print("dry-run               : nothing written")
    print("note                  : advisory only; blocks_production =", payload["blocks_production"])
    return 0


def _experience_query(args) -> int:
    store = _experience_store(args)
    tokens = tuple(args.token or ())
    if args.risk_type or tokens:
        kind = KIND_PATTERN
        records = store.query_pattern(risk_type=args.risk_type, tokens=tokens, limit=args.limit)
    else:
        kind = KIND_EXPERIENCE
        records = store.get_related_experience(story_dna=args.story_dna,
                                               episode_id=args.episode, limit=args.limit)
    if args.json:
        print(json.dumps({"kind": kind, "records": records}, ensure_ascii=False, indent=2))
        return 0
    print("store     :", store.store_dir)
    print("kind      :", kind, "| candidates:", len(records))
    for record in records:
        print("  ", _record_line(kind, record))
    return 0


def _experience_list(args) -> int:
    store = _experience_store(args)
    kinds = list(KINDS) if args.kind == "all" else [args.kind]
    records = {kind: store.list_records(kind, episode_id=args.episode) for kind in kinds}
    if args.json:
        print(json.dumps({"summary": store.summarize(), "records": records},
                         ensure_ascii=False, indent=2))
        return 0
    summary = store.summarize()
    print("store     :", store.store_dir)
    print("counts    :", summary["counts"], "| malformed:", summary["malformed"])
    if args.episode:
        print("episode   :", args.episode)
    for kind in kinds:
        print("--", kind, "(" + str(len(records[kind])) + ")")
        for record in records[kind]:
            print("  ", _record_line(kind, record))
    return 0


def cmd_experience(args) -> int:
    if args.experience_cmd == "save":
        return _experience_save(args)
    if args.experience_cmd == "query":
        return _experience_query(args)
    if args.experience_cmd == "list":
        return _experience_list(args)
    if args.experience_cmd == "stats":
        return _experience_stats(args)
    print("ERROR: unknown experience action:", args.experience_cmd)
    return 2


def _experience_stats(args) -> int:
    """Read-only accumulation statistics; writes nothing, ranks nothing."""
    store = _experience_store(args)
    payload = collect_stats(store,
                            feedback_dir=getattr(args, "feedback_store", None),
                            ledger_path=getattr(args, "ledger", None))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    for line in format_stats(payload):
        print(line)
    return 0


def cmd_validate(args) -> int:
    if not Path(args.file).is_file():
        print("ERROR: file not found:", args.file)
        return 1
    data = _load_yaml(args.file)
    validators = {
        "dna": validate_dna,
        "similarity": validate_similarity_report,
        "advisor": validate_advisor_report,
        "review": validate_review_reference,
        "feedback": validate_feedback,
        "observation": validate_observation_record,
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

    p = sub.add_parser("observe", help="shadow observation ledger and human feedback (advisory only)")
    obs = p.add_subparsers(dest="observe_cmd", required=True)

    r = obs.add_parser("record", help="record one advisor run in the observation ledger")
    r.add_argument("episode_dir", nargs="?", default=None)
    r.add_argument("--report", default=None, help="record an existing advisor_report.yaml")
    r.add_argument("--ledger", default=None)
    r.add_argument("--feedback-store", default=None)
    r.add_argument("--dry-run", action="store_true")
    add_common(r)
    r.set_defaults(func=cmd_observe)

    f = obs.add_parser("feedback", help="record a human judgement of one advisor report")
    f.add_argument("--report", required=True, help="path to advisor_report.yaml")
    f.add_argument("--creator-decision", required=True, choices=list(CREATOR_DECISIONS))
    f.add_argument("--recommendation-result", required=True, choices=list(RECOMMENDATION_RESULTS))
    f.add_argument("--risk-acknowledged", required=True, choices=["yes", "no"])
    f.add_argument("--revision-direction", default="")
    f.add_argument("--final-effect", default="")
    f.add_argument("--notes", default="")
    f.add_argument("--store", default=None, help="feedback store directory")
    f.add_argument("--ledger", default=None)
    f.add_argument("--no-update", action="store_true", help="do not update the observation ledger")
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(func=cmd_observe)

    l = obs.add_parser("list", help="list recorded shadow observations")
    l.add_argument("--ledger", default=None)
    l.add_argument("--episode", default=None)
    l.add_argument("--json", action="store_true")
    l.set_defaults(func=cmd_observe)

    p = sub.add_parser("experience", help="Experience Store: store and read creative experience (advisory only)")
    exp = p.add_subparsers(dest="experience_cmd", required=True)

    s = exp.add_parser("save", help="turn one human feedback record into stored experience")
    s.add_argument("--feedback", required=True, help="path to a stored advisor feedback JSON")
    s.add_argument("--store", default=None, help="experience store directory")
    s.add_argument("--observation", default=None,
                   help="observation JSON path or an observation id already in the ledger")
    s.add_argument("--ledger", default=None)
    s.add_argument("--similarity", default=None,
                   help="optional similarity_report.yaml; its evidence becomes risk patterns")
    s.add_argument("--story-dna-reference", default="")
    s.add_argument("--production-outcome", default=None)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_experience)

    q = exp.add_parser("query", help="read candidate experience / risk patterns (no ranking)")
    q.add_argument("--episode", default=None)
    q.add_argument("--story-dna", default=None, help="story_dna_reference or a Story DNA YAML path")
    q.add_argument("--risk-type", default=None, help="switch to risk pattern query, e.g. similarity")
    q.add_argument("--token", action="append", default=[], help="token that must appear in a pattern")
    q.add_argument("--limit", type=int, default=None)
    q.add_argument("--store", default=None)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_experience)

    l = exp.add_parser("list", help="list stored experience records (read-only)")
    l.add_argument("--kind", default="all", choices=["all"] + list(KINDS))
    l.add_argument("--episode", default=None)
    l.add_argument("--store", default=None)
    l.add_argument("--json", action="store_true")
    l.set_defaults(func=cmd_experience)

    st = exp.add_parser("stats", help="read-only accumulation statistics (no score, no verdict)")
    st.add_argument("--store", default=None, help="experience store directory")
    st.add_argument("--feedback-store", default=None, help="advisor feedback directory")
    st.add_argument("--ledger", default=None, help="observation ledger path")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_experience)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
