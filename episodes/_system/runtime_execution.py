#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutable runtime execution overlay.

runtime-request.json remains immutable user intent.
runtime-execution.json may change only the current execution mode for handoff/resume operations.
"""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
import story_json
import runtime_workspace
import runtime_request

REL=Path("meta/runtime-execution.json")
MODES={"full_auto","preproduction_only","image_continue","resume","repair_only","release_only","data_review"}

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    return story_json.read_json(p)
def write_json(p,d): story_json.write_json(p, d)
def request_mode(ep):
    try:
        request=runtime_request.authority_for_episode(Path(ep).resolve()) or {}
        return str(request.get("mode") or "full_auto")
    except Exception:return "full_auto"
def effective_mode(ep):
    p=runtime_workspace.resolve_read_path(ep,REL)
    if p.is_file():
        try:
            d=read_json(p)
            if d.get("active") is True and d.get("mode") in MODES:return d["mode"]
        except Exception:pass
    return request_mode(ep)
def set_mode(ep,mode,source="explicit"):
    if mode not in MODES:raise ValueError(f"invalid execution mode: {mode}")
    d={"schema_version":1,"active":True,"mode":mode,"source":source,"updated_at":now(),"runtime_request_unchanged":True}
    runtime_workspace.write_json(ep,REL,d);return d
def clear(ep):
    # Explicit clear must remove both copies, otherwise legacy fallback could
    # silently reactivate a stale execution override after the workspace copy is removed.
    for p in runtime_workspace.read_candidates(ep,REL):
        if p.is_file():p.unlink()
def self_test():
    assert "image_continue" in MODES and "preproduction_only" in MODES
    print("RUNTIME EXECUTION OVERLAY SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("set");p.add_argument("episode_dir");p.add_argument("mode",choices=sorted(MODES));p.add_argument("--source",default="explicit")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    p=sub.add_parser("clear");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="set":print(json.dumps(set_mode(ep,a.mode,a.source),ensure_ascii=False,indent=2));return 0
    if a.cmd=="clear":clear(ep);print("RUNTIME EXECUTION OVERLAY CLEARED");return 0
    overlay_path=runtime_workspace.resolve_read_path(ep,REL)
    print(json.dumps({"effective_mode":effective_mode(ep),"overlay":read_json(overlay_path) if overlay_path.is_file() else None},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
