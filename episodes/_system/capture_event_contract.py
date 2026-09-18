#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-frame Capture Event Contract: why this exact frame could realistically exist."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import story_json
import character_contract
import episode_contract_persistence

REL=Path("meta/capture-event-contract.json")
CONTRACT_TYPE="CAPTURE_EVENT"
AWARENESS={"aware","unaware","partial","not_applicable"}
REQUIRED=("photographer_id","capture_device","why_capture_now","device_position",
          "subject_awareness","operator_state","framing_constraint","retained_reason")

def read_json(p):
    return story_json.read_json(p)
def write_json(p,d):
    story_json.write_json(p, d)



def load(ep):
    ep=Path(ep).resolve()
    return episode_contract_persistence.load_latest(
        ep, CONTRACT_TYPE, legacy_path=ep/REL
    )


def exists(ep):
    return isinstance(load(ep),dict)


def save(ep,data):
    ep=Path(ep).resolve()
    episode_contract_persistence.save(
        ep, CONTRACT_TYPE, REL, data,
        status=str(data.get("status") or "ACTIVE"),
    )
    return data


def authority_sha256(ep):
    data=load(ep)
    return sha_json(data) if isinstance(data,dict) else None
def sha_json(d):
    raw=json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
def frame_count(ep):
    d=read_json(Path(ep)/"meta/release-manifest.json")
    return int(((d.get("release") or {}).get("body_frame_count")) or 0)

def prepare(ep, force=False):
    ep=Path(ep).resolve()
    existing=load(ep)
    if isinstance(existing,dict) and not force:return existing
    cp=character_contract.load(ep) or {}
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
    return save(ep,d)

def validate(ep, require_locked=True):
    ep=Path(ep).resolve();d=load(ep)
    if not isinstance(d,dict):return ["meta/capture-event-contract.json missing"]
    e=[];total=frame_count(ep)
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
    ep=Path(ep).resolve();d=load(ep) or {};key=f"{int(frame):02d}"
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
    print(json.dumps(load(ep) or {},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
