from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_performance_benchmark as benchmark


def _row(eid, elapsed, active, wait, *, needs=False, override=False, automatic=True):
    return {
        "episode_id": eid,
        "coverage": "complete",
        "episode_elapsed_ms": elapsed,
        "pipeline_controlled_ms": active,
        "external_user_wait_ms": wait,
        "outcome": {
            "needs_user": needs,
            "user_override": override,
            "automatic_completion": automatic,
        },
    }


def test_three_episode_benchmark_reports_median_p90_and_user_burden_rates():
    rows = [
        _row("ep-a", 1000, 600, 100),
        _row("ep-b", 2000, 1200, 200, needs=True, automatic=False),
        _row("ep-c", 3000, 1800, 300, override=True, automatic=False),
    ]
    result = benchmark.aggregate(rows)
    assert result["episode_count"] == 3
    assert result["timing"]["episode_elapsed"]["median_ms"] == 2000
    assert result["timing"]["episode_elapsed"]["p90_ms"] == 3000
    assert result["timing"]["pipeline_controlled"]["median_ms"] == 1200
    assert result["user_burden"]["needs_user_rate"]["rate"] == 0.333333
    assert result["user_burden"]["user_override_rate"]["rate"] == 0.333333
    assert result["user_burden"]["automatic_completion_rate"]["rate"] == 0.333333


def test_unknown_user_burden_is_not_counted_as_false():
    rows = [
        _row("ep-a", 1000, 600, 100),
        _row("ep-b", 2000, 1200, 200),
        {
            "episode_id": "ep-c",
            "coverage": "partial",
            "episode_elapsed_ms": None,
            "pipeline_controlled_ms": None,
            "external_user_wait_ms": None,
            "outcome": {
                "needs_user": None,
                "user_override": None,
                "automatic_completion": None,
            },
        },
    ]
    result = benchmark.aggregate(rows)
    assert result["user_burden"]["needs_user_rate"]["known"] == 2
    assert result["user_burden"]["needs_user_rate"]["unknown"] == 1
    assert result["timing"]["pipeline_controlled"]["known"] == 2


def test_benchmark_requires_three_distinct_episodes():
    rows = [_row("ep-a", 1, 1, 0), _row("ep-b", 2, 2, 0)]
    try:
        benchmark.aggregate(rows)
    except ValueError as exc:
        assert "REQUIRES_3_EPISODES" in str(exc)
    else:
        raise AssertionError("benchmark must require at least three episodes")

    duplicate = [
        _row("ep-a", 1, 1, 0),
        _row("ep-a", 2, 2, 0),
        _row("ep-c", 3, 3, 0),
    ]
    try:
        benchmark.aggregate(duplicate)
    except ValueError as exc:
        assert "MUST_BE_DISTINCT" in str(exc)
    else:
        raise AssertionError("benchmark must reject duplicate episodes")
