#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS runtime observability path/schema constants (B0).

Single registration point for the runtime performance/observability JSON
documents and the runtime trace event channel that S2.6 consumers share:

- meta/episode-performance-ledger.json
- meta/workflow-performance.json
- meta/workflow-observability.json
- meta/image-scheduler-performance.json (read side)
- meta/batch-runtime-performance.json
- meta/quota-observability.json
- meta/runtime/trace-events.jsonl

B0 only registers constants and helpers plus their self test; existing writers
keep their own REL constants until B6 migrates them to read this module.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EPISODE_PERFORMANCE_REL = Path("meta/episode-performance-ledger.json")
WORKFLOW_PERFORMANCE_REL = Path("meta/workflow-performance.json")
WORKFLOW_OBSERVABILITY_REL = Path("meta/workflow-observability.json")
IMAGE_SCHEDULER_PERFORMANCE_REL = Path("meta/image-scheduler-performance.json")
BATCH_RUNTIME_PERFORMANCE_REL = Path("meta/batch-runtime-performance.json")
QUOTA_OBSERVABILITY_REL = Path("meta/quota-observability.json")
TRACE_EVENTS_REL = Path("meta/runtime/trace-events.jsonl")

KNOWN_PATHS = {
    "episode_performance": EPISODE_PERFORMANCE_REL,
    "workflow_performance": WORKFLOW_PERFORMANCE_REL,
    "workflow_observability": WORKFLOW_OBSERVABILITY_REL,
    "image_scheduler_performance": IMAGE_SCHEDULER_PERFORMANCE_REL,
    "batch_runtime_performance": BATCH_RUNTIME_PERFORMANCE_REL,
    "quota_observability": QUOTA_OBSERVABILITY_REL,
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def summary_document(kind: str, payload: dict, *,
                     schema_version: int = 1) -> dict:
    """Stamp the shared summary envelope without clobbering writer fields.

    schema_version/generated_at/kind are only filled when missing so migrated
    writers that already produce richer docs keep their values.
    """
    data = dict(payload)
    data.setdefault("schema_version", int(schema_version))
    data.setdefault("generated_at", now())
    data.setdefault("kind", kind)
    return data


def resolve_known_path(rel: Path | str) -> Path:
    p = Path(rel)
    for kind, known in KNOWN_PATHS.items():
        if p == known:
            return p
    raise ValueError(f"observability path is not registered: {p}")


def write_summary(ep: Path | str, rel: Path | str, *, kind: str,
                  payload: dict, schema_version: int = 1) -> Path:
    """Deterministic atomic write of one registered observability summary."""
    import story_json

    target = Path(ep).resolve() / resolve_known_path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    story_json.write_json(
        target,
        summary_document(kind, payload, schema_version=schema_version),
    )
    return target


def append_trace_event(ep: Path | str, event: dict) -> Path:
    """Append one event line to the runtime trace channel (LF terminated)."""
    target = Path(ep).resolve() / TRACE_EVENTS_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
    return target


def self_test() -> None:
    import tempfile

    assert KNOWN_PATHS["episode_performance"].as_posix() == \
        "meta/episode-performance-ledger.json"
    assert TRACE_EVENTS_REL.as_posix() == "meta/runtime/trace-events.jsonl"
    with tempfile.TemporaryDirectory(prefix="observability self test ") as td:
        ep = Path(td)
        out = write_summary(ep, EPISODE_PERFORMANCE_REL, kind="episode",
                            payload={"active_wall_seconds": 12.5})
        import story_json

        data = story_json.read_json(out)
        assert data["kind"] == "episode"
        assert data["schema_version"] == 1
        assert "generated_at" in data
        assert data["active_wall_seconds"] == 12.5
        try:
            write_summary(ep, Path("meta/other.json"), kind="x", payload={})
            raise AssertionError("unregistered path must be rejected")
        except ValueError:
            pass
        trace = append_trace_event(ep, {"event": "phase6.batch.start"})
        append_trace_event(ep, {"event": "phase6.batch.done"})
        lines = [x for x in trace.read_text(encoding="utf-8").splitlines() if x]
        assert len(lines) == 2
    print("RUNTIME OBSERVABILITY SELF-TEST PASS")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="self-test")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
