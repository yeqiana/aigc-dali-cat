#!/usr/bin/env python3
"""Audit whether legacy PREIMAGE telemetry is eligible as a model-performance baseline."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def load_runtime_env() -> None:
    from scripts.phase9_runtime_launcher import load_runtime_env_file
    env, _ = load_runtime_env_file(
        ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ)
    )
    os.environ.update(env)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--baseline", default="reports/p1-preimage-production-baseline-20260926.json")
    args = ap.parse_args()
    load_runtime_env()
    from platform.repository.mysql.mysql_connection_pool import set_process_role
    set_process_role("scheduler")
    import episode_performance

    ep = Path(args.episode_dir).resolve()
    path = (ROOT / args.baseline).resolve()
    report = json.loads(path.read_text(encoding="utf-8"))
    perf = episode_performance.load(ep) or {}
    named = perf.get("named_spans") or {}
    mapping = {
        "CHARACTER_FINALIZE": "HOST_ACTION_PREIMAGE_CHARACTER_FINALIZE",
        "ENVIRONMENT_PREPARE": "HOST_ACTION_PREIMAGE_ENVIRONMENT_PREPARE",
        "WORLD_PREPARE": "HOST_ACTION_PREIMAGE_WORLD_PREPARE",
        "VISUAL_NARRATIVE_PREPARE": "HOST_ACTION_PREIMAGE_VISUAL_NARRATIVE_PREPARE",
    }
    ratios = []
    span_evidence = {}
    for item in report.get("tasks") or []:
        task_type = item.get("task_type")
        runs = ((named.get(mapping.get(task_type, "")) or {}).get("runs") or [])
        completed = [r for r in runs if r.get("duration_seconds") is not None]
        latest = completed[-1] if completed else None
        span = float(latest["duration_seconds"]) if latest else None
        handshake = item.get("wall_seconds")
        ratio = None
        if span and isinstance(handshake, (int, float)):
            ratio = float(handshake) / span
            ratios.append(ratio)
        span_evidence[task_type] = {
            "named_span": mapping.get(task_type),
            "host_action_span_seconds": span,
            "host_handshake_seconds": handshake,
            "handshake_to_span_ratio": ratio,
        }

    late_handshake = bool(ratios and max(ratios) < 0.25)
    report["audited_at"] = now()
    report["host_action_span_evidence"] = span_evidence
    report["model_wall_trusted"] = False
    report["performance_baseline_eligible"] = bool(
        report.get("token_evidence_complete") is True
        and report.get("repeated_read_evidence_complete") is True
        and report.get("timeout_evidence_complete") is True
        and report.get("failure_evidence_complete") is True
        and not late_handshake
    )
    report["measurement_warning"] = (
        "Legacy start-preimage handshakes occurred near finalize and cover only a small "
        "fraction of HOST_ACTION spans; handshake wall must not be used as model wall."
        if late_handshake
        else "Model wall remains untrusted until explicit provider/model telemetry exists."
    )
    report["note"] = (
        "Host request handshakes are retained as execution facts. Model wall/token/read/failure/"
        "timeout evidence is never inferred. This audit is fail-closed for P1 cutover."
    )
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({
        "performance_baseline_eligible": report["performance_baseline_eligible"],
        "model_wall_trusted": report["model_wall_trusted"],
        "late_handshake_detected": late_handshake,
        "host_action_span_evidence": span_evidence,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
