#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 9 observability aggregator.

Diagnostic evidence only. Never changes episode stage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

import runtime_trace

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/workflow-observability.json")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def maybe(ep: Path, rel: str) -> dict:
    p = ep / rel
    return read_json(p) if p.is_file() else {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def resolve_ep(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep


def counts(rows, key):
    return dict(Counter(str((x or {}).get(key) or "UNKNOWN") for x in rows if isinstance(x, dict)))


def collect(ep: Path, *, write: bool = True) -> dict:
    state = maybe(ep, "meta/episode-state.json")
    checkpoint = maybe(ep, "meta/runtime-checkpoint.json")
    performance = maybe(ep, "meta/workflow-performance.json")
    scheduler = maybe(ep, "meta/image-scheduler-performance.json")
    queue = maybe(ep, "meta/production-queue.json")
    ledger = maybe(ep, "meta/production-ledger.json")
    scout = maybe(ep, "meta/frame-scout-summary.json")
    snapshot = maybe(ep, "meta/final-candidate-snapshot.json")
    post = maybe(ep, "meta/post-publish-review.json")

    runs = performance.get("runs") or []
    latest_run = runs[-1] if runs else {}
    steps = latest_run.get("steps") or []
    slowest = sorted(
        [x for x in steps if isinstance(x, dict)],
        key=lambda x: float(x.get("elapsed_seconds") or 0),
        reverse=True,
    )[:8]

    qitems = queue.get("items") or []
    ledger_rows = list((ledger.get("frames") or {}).values())
    scout_rows = scout.get("rows") or []

    failure_taxonomy = {
        "technical_failures": sum(1 for x in qitems if (x or {}).get("status") == "tech_failed"),
        "dependency_or_hard_blocked": sum(1 for x in qitems if (x or {}).get("status") in {"blocked", "queued"}),
        "scout_repair": sum(1 for x in qitems if (x or {}).get("status") == "scout_repair"),
        "content_failed": sum(1 for x in ledger_rows if (x or {}).get("status") == "CONTENT_FAILED"),
        "failed_frames_checkpoint": len(checkpoint.get("failed_frames") or []),
        "scout_unresolved": len(scout.get("errors") or []),
    }

    waves = scheduler.get("waves") or []
    parallel = [int((x or {}).get("parallel") or 0) for x in waves if isinstance(x, dict)]
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "diagnostic_only": True,
        "stage_source": "meta/episode-state.json",
        "episode": ep.relative_to(ROOT).as_posix(),
        "current_state": state.get("current_state"),
        "latest_workflow_run": {
            "run_id": latest_run.get("run_id"),
            "status": latest_run.get("status"),
            "total_seconds": latest_run.get("total_seconds"),
            "slowest_steps": slowest,
        },
        "production": {
            "ledger_status_counts": counts(ledger_rows, "status"),
            "queue_status_counts": counts(qitems, "status"),
            "scheduler_wave_count": len(waves),
            "max_observed_parallel": max(parallel) if parallel else 0,
            "adaptive_parallel_current": scheduler.get("adaptive_parallel"),
        },
        "review": {
            "scout_decisions": counts(scout_rows, "decision"),
            "scout_summary_passed": ((scout.get("summary") or {}).get("passed")),
        },
        "release": {
            "snapshot_present": bool(snapshot),
            "snapshot_sha256": snapshot.get("snapshot_sha256"),
        },
        "post_publish": {
            "latest_checkpoint": post.get("latest_checkpoint"),
            "completed_checkpoints": post.get("completed_checkpoints") or [],
        },
        "runtime_trace": runtime_trace.summarize(ep, write=True),
        "failure_taxonomy": failure_taxonomy,
        "health": {
            "has_blockers": any(v for v in failure_taxonomy.values()),
            "workflow_status": latest_run.get("status") or "UNKNOWN",
        },
    }
    if write:
        write_json(ep / REL, report)
    return report


def self_test() -> None:
    assert REL.as_posix() == "meta/workflow-observability.json"
    assert counts([{"status": "A"}, {"status": "A"}, {"status": "B"}], "status") == {"A": 2, "B": 1}
    print("WORKFLOW OBSERVABILITY V2.1 PHASE9 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("collect"); p.add_argument("episode_dir")
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test":
        self_test(); return 0
    ep = resolve_ep(a.episode_dir)
    if a.cmd == "collect":
        print(json.dumps(collect(ep, write=True), ensure_ascii=False, indent=2)); return 0
    p = ep / REL
    if not p.is_file():
        collect(ep, write=True)
    print(p.read_text(encoding="utf-8")); return 0


if __name__ == "__main__":
    raise SystemExit(main())
