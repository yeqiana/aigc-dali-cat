#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact resume capsule: one cheap file to restore a Story OS run after context loss."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import runtime_capability_cache

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/resume-capsule.json")
SOURCE_RELS=["meta/episode-state.json","meta/production-ledger.json","meta/production-queue.json","meta/runtime-request.json","meta/story-gates.json","meta/runtime-checkpoint.json","meta/final-acceptance.json"]
STAGES=["IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED"]
STEP_BY_STATE={"IDEA_LOCKED":"CREATIVE_STORY","STORYBOARD_LOCKED":"VISUAL_LOCK","VISUAL_CALIBRATED":"PRODUCTION","PRODUCTION_PASSED":"RELEASE","PUBLISH_READY":"RELEASE","PUBLISHED":"RELEASE","DATA_REVIEWED":"RELEASE"}

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    p=Path(p)
    if not p.is_file():return None
    try:
        d=json.loads(p.read_text(encoding="utf-8-sig"));return d if isinstance(d,dict) else None
    except Exception:return None
def sha(p):
    p=Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def _ledger_summary(ledger):
    frames=(ledger or {}).get("frames") or {};status_counts={}; blocking=[];tech=[];ready=[]
    for k,row in frames.items():
        st=str((row or {}).get("status") or "PENDING");status_counts[st]=status_counts.get(st,0)+1
        if st in {"NEEDS_USER","CONTENT_FAILED"}:blocking.append(str(k).zfill(2))
        if st=="TECH_FAILED":tech.append(str(k).zfill(2))
        if st in {"ORIGINAL_READY","REPAIR_READY","PASSED","LOCKED"}:ready.append(str(k).zfill(2))
    return {"frame_count":len(frames),"status_counts":status_counts,"blocking_frames":sorted(blocking),"tech_retry_frames":sorted(tech),"ready_frames":sorted(ready)}
def _queue_summary(q):
    counts={}
    for row in (q or {}).get("items") or []:
        st=str(row.get("status") or "unknown");counts[st]=counts.get(st,0)+1
    return counts
def compile_capsule(ep,write=True):
    ep=Path(ep).resolve(); state=read_json(ep/"meta/episode-state.json") or {};cur=str(state.get("current_state") or "UNKNOWN")
    next_target=None
    if cur in STAGES and STAGES.index(cur)<len(STAGES)-1:next_target=STAGES[STAGES.index(cur)+1]
    sources=[{"path":rel,"sha256":sha(ep/rel)} for rel in SOURCE_RELS]
    led=read_json(ep/"meta/production-ledger.json") or {};q=read_json(ep/"meta/production-queue.json") or {}
    caps=runtime_capability_cache.ensure(ep);ls=_ledger_summary(led);qs=_queue_summary(q)
    actions=[]
    if ls["tech_retry_frames"]:actions.append("retry technical-failure frames only; do not regenerate successful siblings")
    if ls["blocking_frames"]:actions.append("resolve only blocking frames or use valid episode-local final acceptance; do not rescan whole repo")
    if not actions:
        if cur=="STORYBOARD_LOCKED":actions.append("continue Visual Lock from existing evidence")
        elif cur=="VISUAL_CALIBRATED":actions.append("continue Production/Review from current ledger")
        elif cur=="PRODUCTION_PASSED":actions.append("continue Text/Release/Final Snapshot")
        elif cur=="PUBLISH_READY":actions.append("complete; do not reopen production unless user requests changes")
        else:actions.append("continue only the next canonical stage")
    material=json.dumps(sources,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    data={"schema_version":1,"module_version":"2.5.1","generated_at":now(),"episode":ep.relative_to(ROOT).as_posix() if ep.is_relative_to(ROOT) else str(ep),"current_state":cur,"next_target":next_target,"runtime_step":STEP_BY_STATE.get(cur),"source_fingerprint":hashlib.sha256(material).hexdigest(),"source_files":sources,"ledger":ls,"queue_status_counts":qs,"runtime_capabilities":caps,"next_actions":actions,"read_policy":"Read this capsule first after context loss. Do not broad-rescan repository authority unless a listed SHA changed, a required detail is missing, or a gate reports drift.","authority_policy":"Derived cache only; source authority always wins."}
    if write:write_json(ep/REL,data)
    return data
def self_test():
    x=_ledger_summary({"frames":{"01":{"status":"PASSED"},"02":{"status":"TECH_FAILED"},"03":{"status":"NEEDS_USER"}}})
    assert x["tech_retry_frames"]==["02"] and x["blocking_frames"]==["03"]
    print("RUNTIME RESUME CAPSULE V2.5.1 SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("build");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve();d=compile_capsule(ep,write=a.cmd=="build") if a.cmd=="build" else (read_json(ep/REL) or compile_capsule(ep,False))
    print(json.dumps(d,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
