from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

spec = importlib.util.spec_from_file_location(
    "p1_character_paired_benchmark",
    ROOT / "scripts/p1_character_paired_benchmark.py",
)
bench = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(bench)

import preimage_task_contract as tasks


def _task():
    cc = {
        "cast": {"members": [{"id": "P01", "name": "甲"}, {"id": "P02", "name": "乙"}]},
        "pov": {"character_id": "P01", "first_person": True},
    }
    cv = {
        "members": {
            "P01": {"story_identity_anchor": "甲造型"},
            "P02": {"story_identity_anchor": "乙造型"},
        }
    }
    return {
        "task_id": "task",
        "task_type": "CHARACTER_FINALIZE",
        "snapshot_id": "snap",
        "input_contract": {
            "source_authority_sha256": {},
            "authority_inputs": {
                "meta/character-contract.json": cc,
                "meta/character-visual-contract.json": cv,
            },
        },
        "authority_scope": ["character.finalize"],
        "verifier": "verify_character_finalize_candidate",
    }


def _candidate(task, wall, input_tokens, output_tokens, reads):
    row = tasks.candidate_template(task, {
        "character.finalize": {
            "character": {
                "visible_cast": ["P01 甲", "P02 乙"],
                "relationship": "同行伙伴",
                "continuity_rule": "身份稳定",
            },
            "identity": {"P01": "甲 identity", "P02": "乙 identity"},
            "pov": {
                "character_id": "P01",
                "person": "first_person",
                "capture_rule": "随手记录",
            },
            "appearance": {"P01": "甲造型", "P02": "乙造型"},
        }
    })
    row["model_execution"].update({
        "real_model_execution": True,
        "wall_seconds": wall,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "repeated_reads": reads,
        "failure": False,
        "timeout": False,
        "provider": "test",
        "model": "test",
        "telemetry_source": "fixture_receipt",
    })
    return row


def test_pair_passes_within_plan_thresholds():
    task = _task()
    result = bench.evaluate_pair(
        task,
        _candidate(task, 100.0, 1000, 200, 5),
        _candidate(task, 104.0, 1050, 200, 3),
        source_unchanged=True,
    )
    assert result["pass"] is True
    assert result["checks"]["wall_regression_within_5pct"] is True
    assert result["checks"]["token_regression_within_10pct"] is True
    assert abs(result["metrics"]["wall_regression"] - 0.04) < 1e-9


def test_pair_blocks_missing_telemetry():
    task = _task()
    legacy = _candidate(task, 100.0, 1000, 200, 5)
    shadow = tasks.candidate_template(task, legacy["payload"])
    result = bench.evaluate_pair(task, legacy, shadow, source_unchanged=True)
    assert result["pass"] is False
    assert result["checks"]["telemetry_complete"] is False


def test_pair_blocks_wall_or_token_regression():
    task = _task()
    result = bench.evaluate_pair(
        task,
        _candidate(task, 100.0, 1000, 200, 5),
        _candidate(task, 106.0, 1200, 200, 5),
        source_unchanged=True,
    )
    assert result["pass"] is False
    assert result["checks"]["wall_regression_within_5pct"] is False
    assert result["checks"]["token_regression_within_10pct"] is False


def test_pair_blocks_authority_drift():
    task = _task()
    row = _candidate(task, 100.0, 1000, 200, 5)
    result = bench.evaluate_pair(task, row, row, source_unchanged=False)
    assert result["pass"] is False
    assert result["checks"]["authority_zero_regression"] is False


def test_series_uses_five_run_median_and_keeps_single_wall_spike_visible():
    task = _task()
    reports = []
    for index, shadow_wall in enumerate((101.0, 102.0, 103.0, 104.0, 160.0), start=1):
        row = bench.evaluate_pair(
            task,
            _candidate(task, 100.0, 1000, 200, 5),
            _candidate(task, shadow_wall, 1000, 190, 4),
            source_unchanged=True,
        )
        row["run_index"] = index
        reports.append(row)
    result = bench.aggregate_series(reports, requested_runs=5)
    assert result["valid_run_count"] == 5
    assert result["metrics"]["shadow_wall_seconds"] == 103.0
    assert abs(result["metrics"]["wall_regression"] - 0.03) < 1e-9
    assert result["metrics"]["individual_wall_regressions"][-1] == 0.6
    assert result["checks"]["wall_regression_within_5pct"] is True
    assert result["pass"] is True


def test_series_blocks_when_fewer_than_five_valid_runs():
    task = _task()
    reports = [
        bench.evaluate_pair(
            task,
            _candidate(task, 100.0, 1000, 200, 5),
            _candidate(task, 101.0, 1000, 190, 4),
            source_unchanged=True,
        )
        for _ in range(4)
    ]
    result = bench.aggregate_series(reports, requested_runs=5)
    assert result["valid_run_count"] == 4
    assert result["checks"]["minimum_valid_runs"] is False
    assert result["pass"] is False
