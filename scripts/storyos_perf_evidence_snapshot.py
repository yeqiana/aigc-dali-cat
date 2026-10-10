#!/usr/bin/env python3
"""Read-only performance snapshot from already persisted local Episode evidence.

No MySQL, model or Provider calls. Local evidence may be incomplete when
production uses database authority. Missing metrics are null, never estimated.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

RECEIPTS = Path("meta/provider-receipts/model-executions")
TRACE = Path("meta/runtime/trace-events.jsonl")


def percentile(values: list[float], part: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    return round(float(sorted_values[max(0, math.ceil(len(sorted_values) * part) - 1)]), 3)


def _usage(receipt: dict) -> tuple[int | None, int | None]:
    usage = receipt.get("usage")
    if not isinstance(usage, dict):
        usage = receipt.get("tokens")
    if not isinstance(usage, dict):
        return None, None
    def positive_int(keys):
        for key in keys:
            value = usage.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return value
        return None
    return positive_int(("input_tokens", "prompt_tokens")), positive_int(("output_tokens", "completion_tokens"))


def snapshot(episode: Path) -> dict:
    episode = Path(episode).resolve()
    if not episode.is_dir():
        raise ValueError("Episode directory does not exist")
    durations: list[float] = []
    input_tokens = 0
    output_tokens = 0
    observed_input = 0
    observed_output = 0
    roles = Counter()
    statuses = Counter()
    valid = 0
    invalid = 0
    for path in sorted((episode / RECEIPTS).glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, ValueError):
            invalid += 1
            continue
        if not isinstance(row, dict) or not row.get("call_id"):
            invalid += 1
            continue
        valid += 1
        roles[str(row.get("model_role") or "UNKNOWN")] += 1
        statuses[str(row.get("status") or "UNKNOWN")] += 1
        duration = row.get("duration_ms")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(duration) and duration >= 0:
            durations.append(float(duration))
        incoming, outgoing = _usage(row)
        if incoming is not None:
            input_tokens += incoming
            observed_input += 1
        if outgoing is not None:
            output_tokens += outgoing
            observed_output += 1

    spans: list[float] = []
    trace_path = episode / TRACE
    malformed_trace = 0
    if trace_path.is_file():
        with trace_path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except ValueError:
                    malformed_trace += 1
                    continue
                if not isinstance(event, dict) or event.get("event") != "SPAN_END":
                    continue
                value = event.get("elapsed_ms")
                if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
                    spans.append(float(value))
    return {
        "schema_version": 1,
        "evidence_only": True,
        "calls_paid_models": False,
        "changes_episode_state": False,
        "model_receipts_observed": valid,
        "model_receipts_malformed": invalid,
        "calls_by_role": dict(sorted(roles.items())),
        "calls_by_status": dict(sorted(statuses.items())),
        "model_duration_ms_sample_count": len(durations),
        "model_duration_ms_p50": percentile(durations, 0.5),
        "model_duration_ms_p95": percentile(durations, 0.95),
        "model_duration_ms_sum": round(sum(durations), 3) if durations else None,
        "input_tokens_observed_receipts": observed_input,
        "input_tokens_observed_sum": input_tokens if observed_input else None,
        "output_tokens_observed_receipts": observed_output,
        "output_tokens_observed_sum": output_tokens if observed_output else None,
        "local_trace_present": trace_path.is_file(),
        "local_trace_malformed_lines": malformed_trace,
        "span_duration_ms_sample_count": len(spans),
        "span_duration_ms_p50": percentile(spans, 0.5),
        "span_duration_ms_p95": percentile(spans, 0.95),
        "production_wall_time_ms": None,
        "image_quality_score": None,
        "resume_success_rate": None,
        "caveats": [
            "partial evidence is not a complete Episode run",
            "durations can overlap and sum is not wall-clock",
            "MySQL authoritative events are NOT silently reconstructed from local files",
            "missing token counters are unknown, not zero",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print(json.dumps(snapshot(args.episode_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
