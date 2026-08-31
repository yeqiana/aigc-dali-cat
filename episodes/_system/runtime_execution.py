#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutable runtime execution overlay.

runtime-request.json remains immutable user intent.
runtime-execution.json may change only the current execution mode for handoff/resume operations.
"""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path

REL=Path("meta/runtime-execution.json")
MODES={"full_auto","preproduction_only","image_continue","resume","repair_only","release_only","data_review"}

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def request_mode(ep):
    p=ep/"meta/runtime-request.json"
    if not p.is_file():return "full_auto"
    try:return str(read_json(p).get("mode") or "full_auto")
    except Exception:return "full_auto"
def effective_mode(ep):
    p=ep/REL
    if p.is_file():
        try:
            d=read_json(p)
            if d.get("active") is True and d.get("mode") in MODES:return d["mode"]
        except Exception:pass
    return request_mode(ep)
def set_mode(ep,mode,source="explicit"):
    if mode not in MODES:raise ValueError(f"invalid execution mode: {mode}")
    d={"schema_version":1,"active":True,"mode":mode,"source":source,"updated_at":now(),"runtime_request_unchanged":True}
    write_json(ep/REL,d);return d
def clear(ep):
    p=ep/REL
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
    print(json.dumps({"effective_mode":effective_mode(ep),"overlay":read_json(ep/REL) if (ep/REL).is_file() else None},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
