#!/usr/bin/env python3
"""Read-only timing aggregation for Story OS runtime observations."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
from pathlib import Path

import logical_asset_identity
import runtime_observability

ROOT = Path(__file__).resolve().parents[2]


def _parse(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _read_events(ep: Path) -> list[dict]:
    path = ep / runtime_observability.TRACE_EVENTS_REL
    if not path.is_file():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _read_legacy_performance(ep: Path) -> dict:
    path = ep / runtime_observability.EPISODE_PERFORMANCE_REL
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _union_ms(intervals) -> float | None:
    rows = []
    for start, end in intervals:
        a, b = _parse(start), _parse(end)
        if a is not None and b is not None and b >= a:
            rows.append((a, b))
    if not rows:
        return None
    rows.sort()
    total = 0.0
    start, end = rows[0]
    for a, b in rows[1:]:
        if a <= end:
            end = max(end, b)
        else:
            total += (end - start).total_seconds() * 1000
            start, end = a, b
    total += (end - start).total_seconds() * 1000
    return round(total, 3)


def _quantiles(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "total_ms": None, "median_ms": None, "p90_ms": None}
    ordered = sorted(values)
    p90_index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * 0.9 + 0.5)))
    return {"count": len(ordered), "total_ms": round(sum(ordered), 3),
            "median_ms": round(statistics.median(ordered), 3), "p90_ms": round(ordered[p90_index], 3)}


def _pairs(events: list[dict], start_type: str, end_type: str, key_fields: tuple[str, ...]):
    starts = {}
    out = []
    for event in events:
        key = tuple(event.get(name) for name in key_fields)
        timestamp = _parse(event.get("timestamp"))
        if timestamp is None:
            continue
        kind = event.get("event_type")
        if kind == start_type:
            starts[key] = event
        elif kind == end_type and key in starts:
            start = starts.pop(key)
            elapsed = (timestamp - _parse(start["timestamp"])).total_seconds() * 1000
            if elapsed >= 0:
                out.append((start, event, elapsed))
    return out


def build_baseline(ep: str | Path, *, source: str = "INSTRUMENTED_RUNTIME", run_id: str | None = None) -> dict:
    """Aggregate available evidence; absent timestamps stay unknown, never zero."""
    episode = Path(ep).resolve()
    eid = logical_asset_identity.episode_id(episode)
    events = _read_events(episode)
    legacy = _read_legacy_performance(episode)
    if run_id:
        events = [row for row in events if row.get("run_id") in {None, run_id}]
    generations = _pairs(events, "IMAGE_GENERATION_REQUESTED", "IMAGE_GENERATION_SUCCEEDED",
                         ("logical_asset_key", "generation_key"))
    reviews = _pairs(events, "REVIEW_STARTED", "REVIEW_FINISHED",
                     ("logical_asset_key", "generation_key"))
    review_waits = _pairs(events, "REVIEW_ENQUEUED", "REVIEW_STARTED",
                          ("logical_asset_key", "generation_key"))
    worker_walls = _pairs(events, "WORKER_DISPATCH_STARTED", "WORKER_RESULT_RECEIVED",
                          ("logical_asset_key", "generation_key"))
    dispatch_wait_ms = [float(row.get("wait_ms")) for row in events
                        if row.get("event_type") == "WORKER_DISPATCH_COMMITTED"
                        and isinstance(row.get("wait_ms"), (int, float))]
    artifact_save_ms = [float(row.get("duration_ms")) for row in events
                        if row.get("event_type") == "ARTIFACT_COMMITTED"
                        and isinstance(row.get("duration_ms"), (int, float))]
    repairs = _pairs(events, "REPAIR_STARTED", "REPAIR_FINISHED",
                     ("logical_asset_key", "generation_key"))
    gen_ms = [row[2] for row in generations]
    legacy_images = legacy.get("image_attempts") or []
    if not gen_ms:
        gen_ms = [float(row["elapsed_seconds"]) * 1000 for row in legacy_images
                  if isinstance(row, dict) and isinstance(row.get("elapsed_seconds"), (int, float))]
    review_ms = [row[2] for row in reviews]
    legacy_reviews = []
    for span_name, bucket in (legacy.get("named_spans") or {}).items():
        if not str(span_name).startswith("REVIEW_") or not isinstance(bucket, dict):
            continue
        for row in bucket.get("runs") or []:
            value = row.get("duration_seconds") if isinstance(row, dict) else None
            if isinstance(value, (int, float)) and value >= 0:
                legacy_reviews.append(float(value) * 1000)
    if not review_ms:
        review_ms = legacy_reviews
    repair_ms = [row[2] for row in repairs]
    repair_prompt_ms = [float(row.get("duration_ms")) for row in events
                        if row.get("event_type") == "REPAIR_PROMPT_FINISHED"
                        and isinstance(row.get("duration_ms"), (int, float))]
    queues = {name: max((int(row.get("queue_depth") or 0) for row in events
                         if row.get("queue_name") == name and isinstance(row.get("queue_depth"), (int, float))), default=None)
              for name in ("image", "review", "repair")}
    all_asset_keys = {row.get("logical_asset_key") for row in events if row.get("logical_asset_key")}
    run_start = next((_parse(row.get("timestamp")) for row in events if row.get("event_type") in {"EPISODE_RUN_STARTED", "CANARY_RUN_STARTED"} and _parse(row.get("timestamp"))), None)
    run_end = next((_parse(row.get("timestamp")) for row in reversed(events) if row.get("event_type") in {"EPISODE_RUN_FINISHED", "CANARY_RUN_FINISHED"} and _parse(row.get("timestamp"))), None)
    episode_ms = round((run_end - run_start).total_seconds() * 1000, 3) if run_start and run_end and run_end >= run_start else None
    user_wait = sum(row[2] for row in _pairs(events, "USER_WAIT_STARTED", "USER_WAIT_FINISHED", ("run_id", "step")))
    user_wait_ms = round(user_wait, 3) if any(row.get("event_type") == "USER_WAIT_STARTED" for row in events) else None
    performance = legacy if legacy else _read_legacy_performance(episode)
    if events:
        intervals = []
        for start_type, end_type in (("STEP_STARTED", "STEP_FINISHED"), ("STEP_STARTED", "STEP_FAILED"),
                                     ("IMAGE_GENERATION_REQUESTED", "IMAGE_GENERATION_SUCCEEDED"),
                                     ("IMAGE_GENERATION_REQUESTED", "IMAGE_GENERATION_FAILED"),
                                     ("REVIEW_STARTED", "REVIEW_FINISHED"),
                                     ("REPAIR_STARTED", "REPAIR_FINISHED"),
                                     ("WORKER_DISPATCH_STARTED", "WORKER_RESULT_RECEIVED")):
            keys = ("run_id", "step") if start_type.startswith("STEP_") else ("logical_asset_key", "generation_key")
            intervals.extend((a.get("timestamp"), b.get("timestamp")) for a, b, _ in
                             _pairs(events, start_type, end_type, keys))
        controlled_ms = _union_ms(intervals)
    else:
        breakdown = (performance.get("summary") or {}).get("duration_breakdown") or {}
        active = breakdown.get("runtime_active_seconds")
        controlled_ms = round(float(active) * 1000, 3) if isinstance(active, (int, float)) else None
    if not reviews and events and review_ms:
        # Only named FULL/PATCH frame-review spans are execution evidence. The
        # PRODUCT_REVIEW span includes host wait and is deliberately excluded.
        review_intervals = []
        for name, bucket in (legacy.get("named_spans") or {}).items():
            if not str(name).startswith("REVIEW_") or not isinstance(bucket, dict):
                continue
            review_intervals.extend((row.get("started_at"), row.get("ended_at"))
                                    for row in bucket.get("runs") or [] if isinstance(row, dict))
        review_union = _union_ms(review_intervals)
        if review_union is not None:
            review_ms = [review_union]
    if episode_ms is None and isinstance(performance.get("total_wall_seconds"), (int, float)):
        episode_ms = round(float(performance["total_wall_seconds"]) * 1000, 3)
    if user_wait_ms is None:
        breakdown = (performance.get("summary") or {}).get("duration_breakdown") or {}
        value = breakdown.get("user_wait_seconds")
        if isinstance(value, (int, float)):
            user_wait_ms = round(float(value) * 1000, 3)
    idle_ms = round(max(0, episode_ms - controlled_ms - (user_wait_ms or 0)), 3) if episode_ms is not None and controlled_ms is not None else None
    models = {}
    model_call_ids = {row.get("call_id") for row in events
                      if row.get("event_type") == "MODEL_EXECUTION" and row.get("call_id")}
    for event in events:
        bindings = [(event.get("model_role"), event.get("profile"), event.get("effective_model"),
                     event.get("reasoning_effort"), event.get("model_policy_sha256"))]
        if event.get("controller_model"):
            bindings.append(("image.controller", event.get("controller_profile"), event.get("controller_model"),
                             event.get("controller_effort"), event.get("controller_policy_sha256")))
        for role, profile, model, effort, policy_sha in bindings:
            if not model:
                continue
            key = (role, profile, model, effort, policy_sha)
            row = models.setdefault(key, {"role": role, "profile": profile, "model": model,
                                          "effort": effort, "policy_sha256": policy_sha,
                                          "count": 0, "wall_ms": 0.0})
            is_execution = event.get("event_type") == "MODEL_EXECUTION"
            is_legacy_terminal = event.get("event_type") in {
                "IMAGE_GENERATION_SUCCEEDED", "IMAGE_GENERATION_FAILED", "REVIEW_FINISHED",
                "STEP_FINISHED", "STEP_FAILED", "WORKER_RESULT_RECEIVED"}
            event_call_id = event.get("call_id") or event.get("generation_key")
            if (role == event.get("model_role") and
                    (is_execution or (is_legacy_terminal and event_call_id not in model_call_ids))):
                row["count"] += 1
                row["wall_ms"] += float(event.get("duration_ms") or 0)
    model_roles = {row.get("model_role") for row in events if row.get("event_type") == "MODEL_EXECUTION"}
    observed_roles = {"prompt.production", "vision.final", "orchestration"}
    if (source == "INSTRUMENTED_CANARY" and run_start and run_end and reviews
            and observed_roles.issubset(model_roles)):
        coverage = "complete_for_observed_scope"
    else:
        coverage = "complete" if run_start and run_end and generations and reviews else "partial"
    if source == "HISTORICAL_REPLAY" and not events:
        coverage = "partial"
    evidence_files = [runtime_observability.TRACE_EVENTS_REL,
                      runtime_observability.EPISODE_PERFORMANCE_REL,
                      runtime_observability.IMAGE_SCHEDULER_PERFORMANCE_REL,
                      runtime_observability.BATCH_RUNTIME_PERFORMANCE_REL,
                      Path("meta/runtime-request.json"),
                      Path("meta/provider-receipts"),
                      Path("meta/provider-receipts/model-executions")]
    evidence_inventory = [{"path": rel.as_posix(), "present": (episode / rel).exists()}
                          for rel in evidence_files]
    try:
        import runtime_request
        if runtime_request.authority_for_episode(episode):
            for item in evidence_inventory:
                if item["path"] == "meta/runtime-request.json":
                    item["present"] = True
                    item["authority_store"] = "episode_meta_store"
    except Exception:
        pass
    return {
        "schema_version": 1, "kind": "storyos_production_timing_baseline",
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source": source, "coverage": coverage,
        "episode_id": eid, "run_id": run_id, "frame_count": None,
        "logical_asset_count": len(all_asset_keys), "event_count": len(events),
        "episode_elapsed_ms": episode_ms, "pipeline_controlled_ms": controlled_ms,
        "external_user_wait_ms": user_wait_ms, "uncontrolled_idle_ms": idle_ms,
        "generation": {**_quantiles(gen_ms), "queue_wait_ms": round(sum(dispatch_wait_ms), 3) if dispatch_wait_ms else None,
                        "provider_wall_ms": None, "worker_wall_ms": round(sum(row[2] for row in worker_walls), 3) if worker_walls else None,
                        "artifact_save_ms": round(sum(artifact_save_ms), 3) if artifact_save_ms else None,
                        "observed_generation_wall_ms": round(sum(gen_ms), 3) if gen_ms else None},
        "review": {**_quantiles(review_ms), "queue_wait_ms": round(sum(row[2] for row in review_waits), 3) if review_waits else None,
                   "execution_ms": round(sum(review_ms), 3) if review_ms else None},
        "repair": {**_quantiles(repair_ms), "total_ms": round(sum(repair_ms), 3) if repair_ms else None,
                   "prompt_ms": round(sum(repair_prompt_ms), 3) if repair_prompt_ms else None,
                   "generation_ms": round(sum(repair_ms), 3) if repair_ms else None,
                   "review_ms": None},
        "model": [dict(row, wall_ms=round(row["wall_ms"], 3)) for row in models.values()],
        "queue": {"peak_image_queue": queues["image"], "peak_review_queue": queues["review"],
                  "peak_repair_queue": queues["repair"], "oldest_review_wait_ms": None,
                  "oldest_generation_wait_ms": None},
        "failure": {"count": sum(1 for row in events if row.get("event_type") in {"IMAGE_GENERATION_FAILED", "STEP_FAILED"}), "classes": {}},
        "source_evidence": evidence_inventory,
        "limitations": ["Missing timestamps remain null; no timestamp is inferred from file mtime.",
                        "Provider internal duration is null unless the Provider exposes it; observed wall is kept separate."],
    }


def write_baseline(ep: str | Path, output: str | Path, *, source: str = "INSTRUMENTED_RUNTIME") -> dict:
    data = build_baseline(ep, source=source)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--historical-replay", action="store_true")
    parser.add_argument("--source", choices=("INSTRUMENTED_RUNTIME", "INSTRUMENTED_CANARY"))
    args = parser.parse_args()
    source = "HISTORICAL_REPLAY" if args.historical_replay else (args.source or "INSTRUMENTED_RUNTIME")
    write_baseline(args.episode, args.output, source=source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
