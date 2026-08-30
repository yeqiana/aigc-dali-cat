#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 workflow performance telemetry.

Telemetry is diagnostic evidence only and never changes episode state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path

REL = Path("meta/workflow-performance.json")
RUN_LOG = Path("meta/workflow-run.jsonl")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read(ep: Path) -> dict:
    p = ep / REL
    if not p.is_file():
        return {"schema_version": 1, "note": "Performance evidence only; NOT a stage source.", "runs": []}
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("workflow performance root must be object")
    data.setdefault("runs", [])
    return data


def write(ep: Path, data: dict) -> None:
    p = ep / REL
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(p)


def append_log(ep: Path, row: dict) -> None:
    p = ep / RUN_LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def start_run(ep: Path, runtime: str, mode: str) -> str:
    run_id = f"{int(time.time())}-{runtime.lower()}"
    data = read(ep)
    row = {"run_id": run_id, "runtime": runtime, "mode": mode, "started_at": now(), "steps": [], "status": "RUNNING"}
    data["runs"].append(row)
    data["active_run_id"] = run_id
    data["updated_at"] = now()
    write(ep, data)
    append_log(ep, {"event": "RUN_START", **row})
    return run_id


def _find_run(data: dict, run_id: str) -> dict:
    for row in data.get("runs") or []:
        if row.get("run_id") == run_id:
            return row
    raise ValueError(f"workflow run not found: {run_id}")


def record_step(ep: Path, run_id: str, step: str, status: str, elapsed_seconds: float, note: str = "") -> None:
    data = read(ep)
    run = _find_run(data, run_id)
    row = {"step": step, "status": status, "elapsed_seconds": round(float(elapsed_seconds), 3), "recorded_at": now(), "note": note}
    run.setdefault("steps", []).append(row)
    data["updated_at"] = now()
    write(ep, data)
    append_log(ep, {"event": "STEP", "run_id": run_id, **row})


def finish_run(ep: Path, run_id: str, status: str, total_seconds: float) -> None:
    data = read(ep)
    run = _find_run(data, run_id)
    run["status"] = status
    run["finished_at"] = now()
    run["total_seconds"] = round(float(total_seconds), 3)
    slow = sorted(run.get("steps") or [], key=lambda x: float(x.get("elapsed_seconds") or 0), reverse=True)[:5]
    run["slowest_steps"] = slow
    if data.get("active_run_id") == run_id:
        data.pop("active_run_id", None)
    data["updated_at"] = now()
    write(ep, data)
    append_log(ep, {"event": "RUN_FINISH", "run_id": run_id, "status": status, "total_seconds": round(float(total_seconds), 3)})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        assert REL.as_posix() == "meta/workflow-performance.json"
        assert RUN_LOG.as_posix() == "meta/workflow-run.jsonl"
        print("WORKFLOW PERFORMANCE SELF-TEST PASS")
        return 0
    ep = Path(args.episode_dir).resolve()
    print(json.dumps(read(ep), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
