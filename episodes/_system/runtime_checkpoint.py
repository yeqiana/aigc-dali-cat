#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

REL = Path("meta/runtime-checkpoint.json")
VALID_STEP_STATUS = {"PASS", "REUSED", "DIRTY", "FAILED", "BLOCKED", "HOST_WAIT", "SKIPPED_NOT_APPLICABLE"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def rd(p: Path) -> dict:
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SystemExit("runtime checkpoint root must be object")
    return data


def wr(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(p)


def ensure_shape(d: dict) -> dict:
    d.setdefault("schema_version", 2)
    d.setdefault("story_os_version", "2.0")
    d.setdefault("last_completed", "RUNTIME_INITIALIZED")
    d.setdefault("next_action", "READ_EPISODE_STATE")
    d.setdefault("locked_frames", [])
    d.setdefault("failed_frames", [])
    d.setdefault("step_runs", [])
    d.setdefault("note", "Recovery evidence only; NOT a stage source.")
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("episode_dir"); p.add_argument("--runtime", required=True, choices=["CODEX", "WORK", "WEB"]); p.add_argument("--full-auto", action="store_true")
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    p = sub.add_parser("set"); p.add_argument("episode_dir"); p.add_argument("--last-completed"); p.add_argument("--next-action"); p.add_argument("--lock-frame", action="append", default=[]); p.add_argument("--fail-frame", action="append", default=[])
    p = sub.add_parser("record-step"); p.add_argument("episode_dir"); p.add_argument("--step", required=True); p.add_argument("--status", required=True, choices=sorted(VALID_STEP_STATUS)); p.add_argument("--input-hash"); p.add_argument("--output-hash"); p.add_argument("--attempt", type=int, default=1); p.add_argument("--started-at"); p.add_argument("--finished-at"); p.add_argument("--note", default="")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test":
        d = ensure_shape({})
        assert isinstance(d["step_runs"], list)
        print("RUNTIME CHECKPOINT SELF-TEST PASS")
        return 0
    ep = Path(a.episode_dir).resolve(); path = ep / REL
    if a.cmd == "init":
        d = ensure_shape(rd(path) if path.exists() else {})
        d["runtime"] = a.runtime
        if a.full_auto:
            d["continuous_execution_authorized"] = True
            d["approval_basis"] = "delegated_continuous_execution"
        else:
            d.setdefault("continuous_execution_authorized", False)
            d.setdefault("approval_basis", "interactive")
        d["updated_at"] = now(); wr(path, d); print(path); return 0
    if not path.exists():
        raise SystemExit("runtime checkpoint missing")
    d = ensure_shape(rd(path))
    if a.cmd == "show":
        print(json.dumps(d, ensure_ascii=False, indent=2)); return 0
    if a.cmd == "record-step":
        row = {
            "step": a.step,
            "status": a.status,
            "input_hash": a.input_hash,
            "output_hash": a.output_hash,
            "attempt": a.attempt,
            "started_at": a.started_at,
            "finished_at": a.finished_at or now(),
            "note": a.note,
        }
        d["step_runs"].append(row)
        # Keep the latest 200 entries to prevent unbounded growth.
        d["step_runs"] = d["step_runs"][-200:]
        d["updated_at"] = now(); wr(path, d); print(path); return 0
    if a.last_completed: d["last_completed"] = a.last_completed
    if a.next_action: d["next_action"] = a.next_action
    d["locked_frames"] = sorted(set(d.get("locked_frames", [])) | {str(x).zfill(2) for x in a.lock_frame})
    d["failed_frames"] = sorted(set(d.get("failed_frames", [])) | {str(x).zfill(2) for x in a.fail_frame})
    d["updated_at"] = now(); wr(path, d); print(path); return 0


if __name__ == "__main__":
    raise SystemExit(main())
