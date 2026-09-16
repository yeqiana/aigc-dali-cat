#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact resume capsule: one cheap file to restore a Story OS run after context loss."""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
import production_ledger
import production_queue_store
import runtime_capability_cache
import story_json
import derived_freshness
import runtime_checkpoint

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/resume-capsule.json")
SOURCE_RELS=["meta/episode-state.json","meta/production-ledger.json",production_queue_store.REL.as_posix(),"meta/runtime-request.json","meta/story-gates.json","meta/runtime-checkpoint.json","meta/final-acceptance.json"]
STAGES=["IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED"]
STEP_BY_STATE={"IDEA_LOCKED":"CREATIVE_STORY","STORYBOARD_LOCKED":"VISUAL_LOCK","VISUAL_CALIBRATED":"PRODUCTION","PRODUCTION_PASSED":"RELEASE","PUBLISH_READY":"RELEASE","PUBLISHED":"RELEASE","DATA_REVIEWED":"RELEASE"}

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    return story_json.read_json(p, default=None)
def sha(p):
    p=Path(p)
    return derived_freshness.sha256_file(p)
def write_json(p,d):
    story_json.write_json(p, d)
def source_snapshot(ep):
    ep=Path(ep).resolve();rows=[]
    for rel in SOURCE_RELS:
        logical=str(rel).replace("\\","/")
        if logical==runtime_checkpoint.REL.as_posix():path=runtime_checkpoint.read_path(ep)
        elif logical==production_queue_store.REL.as_posix():path=production_queue_store.read_path(ep)
        else:path=ep/rel
        rows.append({"path":logical,"sha256":derived_freshness.sha256_file(path)})
    return rows,derived_freshness.fingerprint(rows)
def sources_fresh(ep,data):
    if not isinstance(data,dict) or not data.get("source_fingerprint"):return False
    _rows,current=source_snapshot(ep)
    return str(data.get("source_fingerprint") or "").lower()==current.lower()
def _ledger_summary(ledger):
    frames=(ledger or {}).get("frames") or {};status_counts={}; blocking=[];tech=[];ready=[]
    for k,row in frames.items():
        st=str((row or {}).get("status") or "PENDING");status_counts[st]=status_counts.get(st,0)+1
        if st in {"NEEDS_USER","CONTENT_FAILED"}:blocking.append(str(k).zfill(2))
        if st=="TECH_FAILED":tech.append(str(k).zfill(2))
        if st in production_ledger.READY_LEDGER_STATES:ready.append(str(k).zfill(2))
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
    sources, source_fingerprint = source_snapshot(ep)
    led=read_json(ep/"meta/production-ledger.json") or {};q=read_json(production_queue_store.read_path(ep)) or {}
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
    data={"schema_version":1,"module_version":"2.5.1","generated_at":now(),"episode":ep.relative_to(ROOT).as_posix() if ep.is_relative_to(ROOT) else str(ep),"current_state":cur,"next_target":next_target,"runtime_step":STEP_BY_STATE.get(cur),"source_fingerprint":source_fingerprint,"source_files":sources,"ledger":ls,"queue_status_counts":qs,"runtime_capabilities":caps,"next_actions":actions,"read_policy":"Read this capsule first after context loss. Rebuild on source_fingerprint drift; source authority always wins.","authority_policy":"Derived cache only; source authority always wins."}
    if write:write_json(ep/REL,data)
    return data
def load_fresh(ep,write=True):
    ep=Path(ep).resolve(); existing=read_json(ep/REL) or {}
    return existing if sources_fresh(ep,existing) else compile_capsule(ep,write)
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
    ep=Path(a.episode_dir).resolve();d=compile_capsule(ep,write=True) if a.cmd=="build" else load_fresh(ep,write=True)
    print(json.dumps(d,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
