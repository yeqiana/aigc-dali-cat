#!/usr/bin/env python3
"""Aggregate StoryOS production timing baselines across multiple Episodes."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import production_timing_baseline


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(x) for x in values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * q + 0.5)))
    return round(ordered[index], 3)


def _distribution(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
    return {
        "known": len(values),
        "unknown": len(rows) - len(values),
        "median_ms": round(statistics.median(values), 3) if values else None,
        "p90_ms": _percentile(values, 0.90),
        "min_ms": round(min(values), 3) if values else None,
        "max_ms": round(max(values), 3) if values else None,
    }


def _rate(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = []
    for row in rows:
        outcome = row.get("outcome") if isinstance(row.get("outcome"), dict) else {}
        value = outcome.get(field)
        if isinstance(value, bool):
            values.append(value)
    positives = sum(1 for value in values if value)
    return {
        "known": len(values),
        "unknown": len(rows) - len(values),
        "positive": positives,
        "rate": round(positives / len(values), 6) if values else None,
    }


def aggregate(rows: list[dict[str, Any]], *, require_min_episodes: int = 3) -> dict[str, Any]:
    if len(rows) < int(require_min_episodes):
        raise ValueError(
            f"PRODUCTION_BENCHMARK_REQUIRES_{int(require_min_episodes)}_EPISODES: got {len(rows)}"
        )
    episode_ids = [str(row.get("episode_id") or "") for row in rows]
    if len(set(episode_ids)) != len(episode_ids):
        raise ValueError("PRODUCTION_BENCHMARK_EPISODES_MUST_BE_DISTINCT")
    return {
        "schema_version": 1,
        "kind": "storyos_production_performance_benchmark",
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "episode_count": len(rows),
        "episode_ids": episode_ids,
        "coverage": {
            "complete": sum(str(row.get("coverage") or "").startswith("complete") for row in rows),
            "partial": sum(not str(row.get("coverage") or "").startswith("complete") for row in rows),
        },
        "timing": {
            "episode_elapsed": _distribution(rows, "episode_elapsed_ms"),
            "pipeline_controlled": _distribution(rows, "pipeline_controlled_ms"),
            "external_user_wait": _distribution(rows, "external_user_wait_ms"),
        },
        "user_burden": {
            "needs_user_rate": _rate(rows, "needs_user"),
            "user_override_rate": _rate(rows, "user_override"),
            "automatic_completion_rate": _rate(rows, "automatic_completion"),
        },
        "episodes": [{
            "episode_id": row.get("episode_id"),
            "coverage": row.get("coverage"),
            "episode_elapsed_ms": row.get("episode_elapsed_ms"),
            "pipeline_controlled_ms": row.get("pipeline_controlled_ms"),
            "external_user_wait_ms": row.get("external_user_wait_ms"),
            "outcome": row.get("outcome"),
        } for row in rows],
    }


def build(episodes: list[str | Path], *, source: str = "INSTRUMENTED_RUNTIME",
          require_min_episodes: int = 3) -> dict[str, Any]:
    rows = [
        production_timing_baseline.build_baseline(Path(ep).resolve(), source=source)
        for ep in episodes
    ]
    return aggregate(rows, require_min_episodes=require_min_episodes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="+", type=Path)
    ap.add_argument("--source", default="INSTRUMENTED_RUNTIME")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--min-episodes", type=int, default=3)
    args = ap.parse_args()
    try:
        data = build(
            args.episodes,
            source=args.source,
            require_min_episodes=max(1, int(args.min_episodes)),
        )
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", **data}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
