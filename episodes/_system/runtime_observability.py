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
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EPISODE_PERFORMANCE_REL = Path("meta/episode-performance-ledger.json")
WORKFLOW_PERFORMANCE_REL = Path("meta/workflow-performance.json")
WORKFLOW_OBSERVABILITY_REL = Path("meta/workflow-observability.json")
IMAGE_SCHEDULER_PERFORMANCE_REL = Path("meta/image-scheduler-performance.json")
BATCH_RUNTIME_PERFORMANCE_REL = Path("meta/batch-runtime-performance.json")
QUOTA_OBSERVABILITY_REL = Path("meta/quota-observability.json")
TRACE_SUMMARY_REL = Path("meta/runtime/trace-summary.json")
TRACE_EVENTS_REL = Path("meta/runtime/trace-events.jsonl")
_TRACE_LOCK = threading.Lock()

RUNTIME_EVENT_TYPES = frozenset({
    "EPISODE_RUN_STARTED", "EPISODE_RUN_FINISHED", "STEP_READY", "STEP_DISPATCHED",
    "STEP_STARTED", "STEP_FINISHED", "STEP_FAILED", "WORKER_DISPATCH_STARTED",
    "WORKER_DISPATCH_COMMITTED", "WORKER_RESULT_RECEIVED", "IMAGE_GENERATION_REQUESTED",
    "IMAGE_GENERATION_OBSERVED", "IMAGE_GENERATION_SUCCEEDED", "IMAGE_GENERATION_FAILED", "ARTIFACT_COMMITTED",
    "REVIEW_ENQUEUED", "REVIEW_STARTED", "REVIEW_FINISHED", "REPAIR_ENQUEUED",
    "REPAIR_STARTED", "REPAIR_FINISHED", "REPAIR_PROMPT_STARTED", "REPAIR_PROMPT_FINISHED",
    "REPAIR_REVIEW_STARTED", "REPAIR_REVIEW_FINISHED", "REPAIR_GENERATION_STARTED",
    "REPAIR_GENERATION_FINISHED", "FIRST_PASS_REVIEW_COMPLETE", "REPAIR_WAVE_PLANNED",
    "REPAIR_WAVE_STARTED", "REPAIR_WAVE_COMPLETED", "REPAIR_WAVE_DENIED_SECOND_WAVE",
    "USER_WAIT_STARTED", "USER_WAIT_FINISHED",
    "CHECKPOINT_SAVED", "RESUME_STARTED", "MODEL_EXECUTION",
    "CANARY_RUN_STARTED", "CANARY_RUN_FINISHED",
    "ATTEMPT_REQUESTED", "ATTEMPT_RESERVED", "ATTEMPT_RELEASED_PRE_DISPATCH",
    "ATTEMPT_SUCCEEDED", "ATTEMPT_FAILED_AFTER_DISPATCH", "ATTEMPT_OUTCOME_UNKNOWN",
    "ATTEMPT_DENIED_BUDGET", "ATTEMPT_DENIED_ACTIVE", "ATTEMPT_DENIED_STALE_FENCE",
    "USER_ASSET_ADOPTED",
})

RUNTIME_EVENT_FIELDS = (
    "event_id", "timestamp", "episode_id", "run_id", "trace_id", "step", "event_type",
    "logical_asset_key", "frame_id", "model_role", "profile", "effective_model",
    "reasoning_effort", "model_policy_version", "model_policy_sha256", "provider", "runner",
    "worker_id", "attempt_index", "generation_key", "queue_name", "queue_depth",
    "duration_ms", "wait_ms", "status", "failure_class", "source", "evidence_ref",
    "controller_model", "controller_effort", "controller_profile", "controller_policy_sha256",
    "payload_model", "payload_quality",
    "call_id", "requested_model", "effective_model_source", "started_at", "finished_at",
    "fencing_token", "lease_token_hash", "attempt_consumed", "review_queue_depth_at_dispatch",
    "repair_wave_id", "source_generation_key", "repair_generation_key", "failure_codes",
    "remaining_attempts", "high_watermark", "low_watermark", "oldest_review_wait_ms",
)

KNOWN_PATHS = {
    "episode_performance": EPISODE_PERFORMANCE_REL,
    "workflow_performance": WORKFLOW_PERFORMANCE_REL,
    "workflow_observability": WORKFLOW_OBSERVABILITY_REL,
    "image_scheduler_performance": IMAGE_SCHEDULER_PERFORMANCE_REL,
    "batch_runtime_performance": BATCH_RUNTIME_PERFORMANCE_REL,
    "quota_observability": QUOTA_OBSERVABILITY_REL,
    "trace_summary": TRACE_SUMMARY_REL,
}


def kind_for_path(rel: Path | str) -> str:
    p = Path(rel)
    for kind, known in KNOWN_PATHS.items():
        if p == known:
            return kind
    raise ValueError(f"observability path is not registered: {p}")


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


def read_summary(ep: Path | str, rel: Path | str, *, default: dict | None = None) -> dict:
    """Read one metric summary from its configured authority.

    ``dual`` keeps the compatibility-file fallback. ``mysql`` is fail-closed:
    a MySQL failure or missing row never resurrects a local JSON projection.
    """
    import story_json
    import storage_config

    episode = Path(ep).resolve()
    known = resolve_known_path(rel)
    kind = kind_for_path(known)
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        try:
            import metric_snapshot_persistence
            loaded = metric_snapshot_persistence.load_latest(episode, kind)
            if isinstance(loaded, dict):
                return loaded
        except Exception:
            if mode == "mysql":
                raise
        if mode == "mysql":
            return dict(default or {})
    target = episode / known
    if target.is_file():
        data = story_json.read_json(target, require_object=False)
        if isinstance(data, dict):
            return data
    return dict(default or {})


def write_summary(ep: Path | str, rel: Path | str, *, kind: str,
                  payload: dict, schema_version: int = 1) -> Path:
    """Persist one registered summary using its configured authority.

    ``dual`` remains fail-soft for migration. ``mysql`` propagates persistence
    failures and never creates a local JSON shadow that could become a false
    authority.
    """
    import story_json
    import storage_config

    target = Path(ep).resolve() / resolve_known_path(rel)
    data = summary_document(kind, payload, schema_version=schema_version)
    mode = storage_config.episode_meta_store_config()["mode"]
    db_saved = False
    if mode in {"dual", "mysql"}:
        try:
            import metric_snapshot_persistence
            metric_snapshot_persistence.save(Path(ep).resolve(), kind, data)
            db_saved = True
        except Exception:
            if mode == "mysql":
                raise
            db_saved = False
    if mode != "mysql" or not db_saved:
        target.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(target, data)
    return target


def append_trace_event(ep: Path | str, event: dict) -> Path:
    """Append one event line to the runtime trace channel (LF terminated)."""
    target = Path(ep).resolve() / TRACE_EVENTS_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    with _TRACE_LOCK:
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
    return target


def runtime_event(ep: Path | str, event_type: str, **fields) -> dict:
    """Return a normalized observation event; it never carries control authority."""
    name = str(event_type or "").strip().upper()
    if name not in RUNTIME_EVENT_TYPES:
        raise ValueError(f"unknown runtime telemetry event: {name}")
    row = {key: None for key in RUNTIME_EVENT_FIELDS}
    row.update({
        "event_id": uuid.uuid4().hex,
        "timestamp": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds"),
        "event_type": name,
        "source": fields.pop("source", "storyos_runtime"),
        "telemetry_only": True,
    })
    unknown = set(fields) - set(RUNTIME_EVENT_FIELDS)
    if unknown:
        raise ValueError("unknown runtime telemetry fields: " + ", ".join(sorted(unknown)))
    row.update(fields)
    return row


def safe_record_runtime_event(ep: Path | str, event_type: str, **fields) -> bool:
    """Best-effort JSONL event write; telemetry errors never change production flow."""
    try:
        append_trace_event(ep, runtime_event(ep, event_type, **fields))
        return True
    except Exception:
        return False


def write_model_execution_receipt(ep: Path | str, *, receipt: dict) -> Path:
    """Persist one per-call model execution receipt as evidence, not authority."""
    required = (
        "receipt_schema_version", "episode_id", "run_id", "trace_id", "step", "call_id",
        "model_role", "profile", "requested_model", "effective_model", "reasoning_effort",
        "model_policy_version", "model_policy_sha256", "provider", "runner", "started_at",
        "finished_at", "duration_ms", "status", "model_binding_source", "effective_model_source",
    )
    missing = [key for key in required if receipt.get(key) in (None, "")]
    if missing:
        raise ValueError("model execution receipt missing: " + ", ".join(missing))
    target = Path(ep).resolve() / "meta/provider-receipts/model-executions" / f"{receipt['call_id']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
