#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Time/weather/ambient-light continuity gate bound to World State."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

REL=Path("meta/temporal-continuity.json")
DAYPART={"dawn","morning","day","afternoon","dusk","night"}
LIGHT={"dawn_low","daylight","overcast_day","dusk_low","night_dark","artificial_night"}
DARK={"night_dark","artificial_night"}
BRIGHT={"daylight","overcast_day"}

def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_count(ep):
    d=read_json(Path(ep)/"meta/release-manifest.json")
    return int(((d.get("release") or {}).get("body_frame_count")) or 0)

def prepare(ep,force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    ws=ep/"meta/world-state.json";total=frame_count(ep)
    rows=[{"frame":f"{n:02d}","elapsed_minutes_from_prev":0 if n==1 else None,
           "daypart":"","weather":"","precipitation":"","ambient_light":"",
           "large_transition":False,"transition_reason":""} for n in range(1,total+1)]
    d={"schema_version":1,"status":"DRAFT","frame_count":total,
       "source_world_state_sha256":sha(ws) if ws.is_file() else None,
       "world_state_synced":False,"frames":rows}
    write_json(target,d);return d

def validate(ep,require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/temporal-continuity.json missing"]
    d=read_json(p);e=[];total=frame_count(ep)
    if d.get("schema_version")!=1:e.append("temporal schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("temporal continuity must be LOCKED")
    ws=ep/"meta/world-state.json"
    if not ws.is_file():e.append("world-state missing for temporal continuity")
    elif str(d.get("source_world_state_sha256") or "").lower()!=sha(ws).lower():e.append("temporal continuity source_world_state_sha256 stale")
    if d.get("world_state_synced") is not True:e.append("temporal continuity must confirm world_state_synced=true")
    rows=d.get("frames") or []
    if len(rows)!=total:e.append(f"temporal frame count mismatch {len(rows)} != {total}")
    prev=None
    for row in rows:
        try:n=int(row.get("frame"))
        except Exception:e.append("invalid temporal frame id");continue
        day=str(row.get("daypart") or "");light=str(row.get("ambient_light") or "")
        if day not in DAYPART:e.append(f"frame {n:02d} invalid daypart")
        if light not in LIGHT:e.append(f"frame {n:02d} invalid ambient_light")
        if not str(row.get("weather") or "").strip():e.append(f"frame {n:02d} weather missing")
        if not str(row.get("precipitation") or "").strip():e.append(f"frame {n:02d} precipitation missing")
        elapsed=row.get("elapsed_minutes_from_prev")
        if not isinstance(elapsed,(int,float)) or isinstance(elapsed,bool) or elapsed<0:
            e.append(f"frame {n:02d} elapsed_minutes_from_prev invalid");elapsed=0
        if prev:
            changed=(day!=prev["daypart"] or light!=prev["ambient_light"] or str(row.get("weather"))!=str(prev["weather"]) or str(row.get("precipitation"))!=str(prev["precipitation"]))
            if changed and (elapsed<=0 or not str(row.get("transition_reason") or "").strip()):e.append(f"TEMPORAL_TRANSITION_UNEXPLAINED:{n:02d}")
            major=(prev["ambient_light"] in DARK and light in BRIGHT) or (prev["ambient_light"] in BRIGHT and light in DARK)
            if major:
                if row.get("large_transition") is not True:e.append(f"frame {n:02d} major light transition must set large_transition=true")
                if elapsed<20:e.append(f"frame {n:02d} major night/day transition needs elapsed time >=20m")
        prev={"daypart":day,"ambient_light":light,"weather":row.get("weather"),"precipitation":row.get("precipitation")}
    return e

def resolve_frame(ep,frame):
    d=read_json(Path(ep).resolve()/REL);key=f"{int(frame):02d}"
    row=next((x for x in (d.get("frames") or []) if str(x.get("frame")).zfill(2)==key),None)
    return {"frame":key,"temporal_state":row or {}}

def self_test():
    assert DARK.isdisjoint(BRIGHT)
    print("TEMPORAL CONTINUITY GATE SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("validate");p.add_argument("episode_dir");p.add_argument("--allow-draft",action="store_true")
    p=sub.add_parser("resolve-frame");p.add_argument("episode_dir");p.add_argument("frame",type=int)
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.force),ensure_ascii=False,indent=2));return 0
    if a.cmd=="validate":
        e=validate(ep,not a.allow_draft)
        if e:[print("FAIL:",x) for x in e];return 2
        print("TEMPORAL CONTINUITY VERIFIED");return 0
    if a.cmd=="resolve-frame":print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
