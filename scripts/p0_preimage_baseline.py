#!/usr/bin/env python3
"""Freeze a repeatable P0 PREIMAGE protocol baseline before Agent cutover.

This is a deterministic fixture/protocol benchmark, not a production-model
latency claim. Production Episode wall/model/token evidence remains in the
existing Performance Ledger.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTS = (
    "tests/system/test_preimage_task_contract.py",
    "tests/system/test_preimage_parallel_execution.py",
    "tests/system/test_preimage_parallel_runtime.py",
    "tests/system/test_preimage_authority_inputs.py",
    "tests/system/test_preimage_authority_collision.py",
)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    ).strip()


def run_once(test_paths: tuple[str, ...]) -> dict:
    command = [sys.executable, "-m", "pytest", *test_paths, "-q"]
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    wall = time.perf_counter() - started
    return {
        "return_code": proc.returncode,
        "wall_seconds": round(wall, 6),
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-4:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-4:]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument(
        "--output",
        default="reports/p0-preimage-agent-baseline-20260926.json",
    )
    args = ap.parse_args()
    if args.runs < 5:
        raise SystemExit("P0 baseline requires at least 5 runs")
    porcelain = git("status", "--porcelain")
    clean = not bool(porcelain.strip())
    if not clean and not args.allow_dirty:
        raise SystemExit("P0 baseline requires a clean worktree; use --allow-dirty only for diagnostics")

    tests = tuple(DEFAULT_TESTS)
    rows = [run_once(tests) for _ in range(args.runs)]
    failed = [row for row in rows if row["return_code"] != 0]
    walls = [row["wall_seconds"] for row in rows if row["return_code"] == 0]
    report = {
        "schema_version": 1,
        "kind": "p0_preimage_agent_protocol_baseline",
        "benchmark_scope": "deterministic_fixture_protocol_only",
        "not_production_model_latency": True,
        "generated_at": now(),
        "git_head": git("rev-parse", "HEAD"),
        "git_branch": git("branch", "--show-current"),
        "git_worktree_clean": clean,
        "python": sys.version.split()[0],
        "platform": {"sys_platform": sys.platform, "os_name": os.name},
        "runs_requested": args.runs,
        "tests": list(tests),
        "runs": rows,
        "summary": {
            "successful_runs": len(walls),
            "failed_runs": len(failed),
            "median_wall_seconds": round(statistics.median(walls), 6) if walls else None,
            "min_wall_seconds": min(walls) if walls else None,
            "max_wall_seconds": max(walls) if walls else None,
            "p90_wall_seconds": None,
            "p95_wall_seconds": None,
            "percentile_note": "n<10; p90/p95 intentionally not reported",
        },
        "production_performance_summary": {
            "path": "reports/story-os-performance-summary.json",
            "sha256": sha_file(ROOT / "reports/story-os-performance-summary.json"),
        },
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(output.relative_to(ROOT).as_posix())
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
