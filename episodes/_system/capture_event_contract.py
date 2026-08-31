#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-frame Capture Event Contract: why this exact frame could realistically exist."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

REL=Path("meta/capture-event-contract.json")
AWARENESS={"aware","unaware","partial","not_applicable"}
REQUIRED=("photographer_id","capture_device","why_capture_now","device_position",
          "subject_awareness","operator_state","framing_constraint","retained_reason")

def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha_json(d):
    raw=json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
def frame_count(ep):
    d=read_json(Path(ep)/"meta/release-manifest.json")
    return int(((d.get("release") or {}).get("body_frame_count")) or 0)

def prepare(ep, force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    cp=read_json(ep/"meta/character-contract.json") if (ep/"meta/character-contract.json").is_file() else {}
    pov=str(((cp.get("pov") or {}).get("character_id")) or "P01")
    members=((cp.get("cast") or {}).get("members") or [])
    m=next((x for x in members if str(x.get("id"))==pov),members[0] if members else {})
    dev=str(m.get("device_anchor") or "")
    total=frame_count(ep)
    frames={}
    for n in range(1,total+1):
        frames[f"{n:02d}"]={"photographer_id":pov,"capture_device":dev,
          "why_capture_now":"","device_position":"","subject_awareness":"not_applicable",
          "operator_state":"","framing_constraint":"","retained_reason":"",
          "causal_defects":[]}
    d={"schema_version":1,"status":"DRAFT","frame_count":total,
       "principle":"A frame must first be a credible capture event, then a narrative image.",
       "max_causal_defects_per_frame":2,"frames":frames}
    write_json(target,d);return d

def validate(ep, require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/capture-event-contract.json missing"]
    d=read_json(p);e=[];total=frame_count(ep)
    if d.get("schema_version")!=1:e.append("capture event schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("capture event contract must be LOCKED")
    frames=d.get("frames") or {}
    if len(frames)!=total:e.append(f"capture event frame count mismatch {len(frames)} != {total}")
    for n in range(1,total+1):
        key=f"{n:02d}";row=frames.get(key)
        if not isinstance(row,dict):e.append(f"capture event frame {key} missing");continue
        for k in REQUIRED:
            if not str(row.get(k) or "").strip():e.append(f"frame {key} capture_event.{k} missing")
        if str(row.get("subject_awareness") or "") not in AWARENESS:
            e.append(f"frame {key} invalid subject_awareness")
        defects=row.get("causal_defects")
        if not isinstance(defects,list):e.append(f"frame {key} causal_defects must be list")
        elif len(defects)>2:e.append(f"frame {key} causal_defects > 2; defects must stay causal, not filter stacking")
    return e

def resolve_frame(ep, frame):
    ep=Path(ep).resolve();d=read_json(ep/REL);key=f"{int(frame):02d}"
    row=(d.get("frames") or {}).get(key)
    if not isinstance(row,dict):raise ValueError(f"capture event frame {key} missing")
    return {"frame":key,"capture_event":row,"capture_event_sha256":sha_json(row)}

def self_test():
    assert len(AWARENESS)==4
    print("CAPTURE EVENT CONTRACT SELF-TEST PASS")

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
        print("CAPTURE EVENT CONTRACT VERIFIED");return 0
    if a.cmd=="resolve-frame":print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
