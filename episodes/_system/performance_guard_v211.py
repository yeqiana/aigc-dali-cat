#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1.1 production performance budget and slow-step report."""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path

WORKFLOW_REL = Path("meta/workflow-performance.json")
EP_PERF_REL = Path("meta/episode-performance-ledger.json")
BUDGET_REL = Path("meta/performance-budget.json")
SLOW_REL = Path("meta/slow-step-report.json")
SOFT_DIAGNOSTIC_SECONDS = 60 * 60
WARNING_SECONDS = 90 * 60
EXCEEDED_SECONDS = 120 * 60
CRITICAL_SECONDS = 150 * 60
GENERATION_UTILIZATION_WARN = 0.15
GENERATION_UTILIZATION_TARGET = 0.25


def now_dt(): return dt.datetime.now(dt.timezone.utc).astimezone()
def now(): return now_dt().isoformat(timespec="seconds")

def parse_ts(raw):
    if not raw: return None
    try: return dt.datetime.fromisoformat(str(raw))
    except Exception: return None

def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)

def _pick_run(wf: dict, run_id: str | None):
    rows = wf.get("runs") or []
    if run_id:
        for r in rows:
            if r.get("run_id") == run_id: return r
    active = wf.get("active_run_id")
    for r in reversed(rows):
        if r.get("run_id") == active: return r
    return rows[-1] if rows else None

def _status(elapsed: float) -> str:
    if elapsed >= CRITICAL_SECONDS: return "PERFORMANCE_CRITICAL"
    if elapsed >= EXCEEDED_SECONDS: return "PERFORMANCE_BUDGET_EXCEEDED"
    if elapsed >= WARNING_SECONDS: return "PERFORMANCE_DEGRADED"
    if elapsed >= SOFT_DIAGNOSTIC_SECONDS: return "PERFORMANCE_DIAGNOSTIC"
    return "WITHIN_BUDGET"

def observe(ep: Path, run_id: str | None = None, context: str = "") -> dict:
    ep = Path(ep).resolve()
    wf_path = ep / WORKFLOW_REL
    wf = read_json(wf_path) if wf_path.is_file() else {"runs": []}
    run = _pick_run(wf, run_id)
    if not run: return {"status": "NO_RUN", "context": context}
    started = parse_ts(run.get("started_at")); finished = parse_ts(run.get("finished_at"))
    end = finished or now_dt()
    elapsed = max(0.0, (end - started).total_seconds()) if started else float(run.get("total_seconds") or 0.0)
    steps = list(run.get("steps") or [])
    classified = sum(float(x.get("elapsed_seconds") or 0) for x in steps)
    unclassified = max(0.0, elapsed - classified)
    image_backend = 0.0
    ep_perf_path = ep / EP_PERF_REL
    if ep_perf_path.is_file():
        ep_perf = read_json(ep_perf_path)
        image_backend = float((((ep_perf.get("summary") or {}).get("images") or {}).get("image_backend_seconds")) or 0.0)
    util = (image_backend / elapsed) if elapsed > 0 else 0.0
    status = _status(elapsed)
    budget = {
        "schema_version": 1, "observed_at": now(), "run_id": run.get("run_id"), "context": context,
        "elapsed_seconds": round(elapsed, 3), "elapsed_minutes": round(elapsed / 60.0, 2),
        "performance_status": status,
        "budgets_seconds": {"diagnostic": SOFT_DIAGNOSTIC_SECONDS, "warning": WARNING_SECONDS,
                            "exceeded": EXCEEDED_SECONDS, "critical": CRITICAL_SECONDS},
        "image_backend_resource_seconds": round(image_backend, 3),
        "generation_utilization_upper_bound": round(util, 4),
        "generation_utilization_target_floor": GENERATION_UTILIZATION_TARGET,
        "orchestration_bottleneck": util < GENERATION_UTILIZATION_WARN and elapsed >= SOFT_DIAGNOSTIC_SECONDS,
        "classified_step_seconds": round(classified, 3),
        "unclassified_wall_seconds": round(unclassified, 3),
        "unclassified_wall_ratio": round(unclassified / elapsed, 4) if elapsed else 0.0,
    }
    write_json(ep / BUDGET_REL, budget)
    run["performance_budget"] = {
        "status": status, "elapsed_seconds": budget["elapsed_seconds"],
        "generation_utilization_upper_bound": budget["generation_utilization_upper_bound"],
        "unclassified_wall_ratio": budget["unclassified_wall_ratio"],
    }
    wf["performance_budget_updated_at"] = budget["observed_at"]
    write_json(wf_path, wf)
    if elapsed >= EXCEEDED_SECONDS:
        slow = sorted(steps, key=lambda x: float(x.get("elapsed_seconds") or 0), reverse=True)[:5]
        report = {
            "schema_version": 1, "generated_at": now(), "run_id": run.get("run_id"),
            "performance_status": status, "elapsed_seconds": round(elapsed, 3), "top_slow_steps": slow,
            "image_backend_resource_seconds": round(image_backend, 3),
            "generation_utilization_upper_bound": round(util, 4),
            "unclassified_wall_seconds": round(unclassified, 3),
            "unclassified_wall_ratio": round(unclassified / elapsed, 4) if elapsed else 0.0,
            "diagnosis": "ORCHESTRATION_BOTTLENECK" if util < GENERATION_UTILIZATION_WARN else "IMAGE_OR_REVIEW_HEAVY",
            "note": "Telemetry only. This report never changes Story/Visual/Release authority.",
        }
        write_json(ep / SLOW_REL, report)
    return budget

def self_test():
    assert _status(119 * 60) == "PERFORMANCE_DEGRADED"
    assert _status(120 * 60) == "PERFORMANCE_BUDGET_EXCEEDED"
    print("PERFORMANCE GUARD V2.1.1 SELF-TEST PASS")

if __name__ == "__main__": self_test()
