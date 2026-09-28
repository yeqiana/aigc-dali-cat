#!/usr/bin/env python3
"""Create a new, immutable repair-scope assessment from the frozen P3 benchmark."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path("reports/p3-preimage-semantic-critic-paired-benchmark-20260928.json")
OUTPUT = Path("reports/p3-preimage-semantic-critic-repair-scope-assessment-v2-20260928.json")
FIXTURE = Path("tests/fixtures/p3_preimage_semantic_critic/cases.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def assess(benchmark: dict, *, benchmark_sha256: str, fixture_sha256: str | None = None,
           generated_at: str | None = None) -> dict:
    cases = benchmark.get("cases")
    if not isinstance(cases, list):
        raise ValueError("benchmark cases are missing")
    labelled_fail = [row for row in cases if row.get("reference_label") == "FAIL"]
    repair_rows = []
    for row in labelled_fail:
        expected = set(row.get("repair_scope_expected") or [])
        observed = set(row.get("repair_scope_observed") or [])
        if not expected:
            continue
        correct = expected & observed
        precision = len(correct) / len(observed) if observed else 0.0
        recall = len(correct) / len(expected)
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        repair_rows.append({
            "sample_id": row.get("sample_id"),
            "expected_scope": sorted(expected),
            "observed_scope": sorted(observed),
            "correct_scope": sorted(correct),
            "decision": row.get("critic_decision"),
            "repair_proposed": row.get("critic_decision") == "REPAIR" and bool(observed),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })
    precisions = [row["precision"] for row in repair_rows]
    recalls = [row["recall"] for row in repair_rows]
    f1s = [row["f1"] for row in repair_rows]
    all_fails_proposed = bool(labelled_fail) and all(
        any(metric["sample_id"] == row.get("sample_id") and metric["repair_proposed"] for metric in repair_rows)
        for row in labelled_fail
    )
    median_precision, median_recall, median_f1 = map(_median, (precisions, recalls, f1s))
    minimum_recall = min(recalls) if recalls else None
    # No repair thresholds are specified in the final architecture. This conservative
    # default is advisory-only and requires every labelled FAIL to receive a proposal.
    policy = {
        "policy_source": "cutover_gate_conservative_default",
        "minimum_median_precision": 0.8,
        "minimum_median_recall": 0.8,
        "minimum_recall_exclusive": 0.0,
        "all_labelled_failures_require_repair_proposal": True,
    }
    repair_value_v2 = bool(
        all_fails_proposed
        and median_precision is not None and median_precision >= policy["minimum_median_precision"]
        and median_recall is not None and median_recall >= policy["minimum_median_recall"]
        and minimum_recall is not None and minimum_recall > policy["minimum_recall_exclusive"]
    )
    return {
        "schema_version": 1,
        "kind": "p3_preimage_semantic_critic_repair_scope_assessment_v2",
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "immutable": True,
        "source_benchmark": {"path": BENCHMARK.as_posix(), "sha256": benchmark_sha256},
        "fixture_sha256": fixture_sha256,
        "labelled_fail_count": len(labelled_fail),
        "repair_sample_count": len(repair_rows),
        "all_labelled_failures_have_repair_proposal": all_fails_proposed,
        "repair_scope_precision_median": median_precision,
        "repair_scope_recall_median": median_recall,
        "repair_scope_f1_median": median_f1,
        "minimum_repair_scope_recall": minimum_recall,
        "repair_value_v2": repair_value_v2,
        "repair_value_blocking": False,
        "repair_mode_at_cutover": "STRICTLY_ADVISORY_NO_AUTOMATIC_REPAIR",
        "policy": policy,
        "issue_code_recall": "NOT_COMPARABLE",
        "issue_code_taxonomy_mapping_available": False,
        "issue_code_note": "No existing parent-child or semantic issue-family mapping was found; generic fixture code and specific Critic codes are not string-comparable.",
        "samples": repair_rows,
        "warnings": (["MINIMUM_REPAIR_SCOPE_RECALL_BELOW_0_8"] if minimum_recall is not None and minimum_recall < 0.8 else []),
    }


def write_immutable(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / OUTPUT)
    args = parser.parse_args()
    source = ROOT / BENCHMARK
    fixture = ROOT / FIXTURE
    benchmark = json.loads(source.read_text(encoding="utf-8"))
    report = assess(benchmark, benchmark_sha256=sha256(source), fixture_sha256=sha256(fixture))
    write_immutable(args.output, report)
    print(json.dumps({
        "path": args.output.relative_to(ROOT).as_posix(),
        "precision_median": report["repair_scope_precision_median"],
        "recall_median": report["repair_scope_recall_median"],
        "f1_median": report["repair_scope_f1_median"],
        "minimum_recall": report["minimum_repair_scope_recall"],
        "repair_value_v2": report["repair_value_v2"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
