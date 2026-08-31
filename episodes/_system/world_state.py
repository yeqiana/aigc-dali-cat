#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persistent per-episode World State with legal frame deltas.

The state is authored pre-image and becomes stable authority. Resolved Frame
Contracts consume the effective state for their frame. No new Episode stage.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

REL=Path("meta/world-state.json")
IDENTITY_FIELDS={"clothing_anchor","device_anchor","hair","build","injury","status"}

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

def _merge(base,delta):
    if isinstance(delta,dict) and delta.get("__delete__") is True and len(delta)==1:
        return None
    if isinstance(base,dict) and isinstance(delta,dict):
        out=copy.deepcopy(base)
        for k,v in delta.items():
            if isinstance(v,dict) and v.get("__delete__") is True and len(v)==1:
                out.pop(k,None);continue
            out[k]=_merge(out.get(k),v) if k in out else copy.deepcopy(v)
        return out
    return copy.deepcopy(delta)

def prepare(ep, force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    cp=read_json(ep/"meta/character-contract.json") if (ep/"meta/character-contract.json").is_file() else {}
    members=((cp.get("cast") or {}).get("members") or [])
    chars={}
    for m in members:
        cid=str(m.get("id") or "")
        if not cid:continue
        chars[cid]={k:m.get(k) for k in ("gender","age","build","hair","clothing_anchor","device_anchor") if m.get(k) is not None}
        chars[cid]["status"]="present"
    pov=str(((cp.get("pov") or {}).get("character_id")) or "P01")
    dev=((chars.get(pov) or {}).get("device_anchor"))
    total=frame_count(ep)
    d={"schema_version":1,"status":"DRAFT","frame_count":total,
       "initial_state":{"time":"","location":"","weather":"","characters":chars,
                        "recorder":{"photographer_id":pov,"active_device":dev},
                        "props":{},"anomaly":{"phase":"ordinary"}},
       "frames":{f"{n:02d}":{"delta":{},"story_event":""} for n in range(1,total+1)}}
    write_json(target,d);return d

def _sensitive_changes(before,after):
    out=[]
    bchars=(before.get("characters") or {}) if isinstance(before,dict) else {}
    achars=(after.get("characters") or {}) if isinstance(after,dict) else {}
    for cid in set(bchars)|set(achars):
        if cid not in bchars or cid not in achars:
            out.append(f"characters.{cid}.presence");continue
        for k in IDENTITY_FIELDS:
            if (bchars[cid] or {}).get(k)!=(achars[cid] or {}).get(k):
                out.append(f"characters.{cid}.{k}")
    br=(before.get("recorder") or {}) if isinstance(before,dict) else {}
    ar=(after.get("recorder") or {}) if isinstance(after,dict) else {}
    for k in ("photographer_id","active_device"):
        if br.get(k)!=ar.get(k):out.append(f"recorder.{k}")
    return out

def validate(ep, require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/world-state.json missing"]
    d=read_json(p);e=[];total=frame_count(ep)
    if d.get("schema_version")!=1:e.append("world state schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("world state must be LOCKED")
    if not isinstance(d.get("initial_state"),dict):e.append("world state initial_state missing");return e
    frames=d.get("frames") or {}
    if len(frames)!=total:e.append(f"world state frame count mismatch {len(frames)} != {total}")
    cur=copy.deepcopy(d.get("initial_state") or {})
    for n in range(1,total+1):
        key=f"{n:02d}";row=frames.get(key)
        if not isinstance(row,dict):e.append(f"world state frame {key} missing");continue
        delta=row.get("delta")
        if not isinstance(delta,dict):e.append(f"world state frame {key} delta must be object");continue
        nxt=_merge(cur,delta)
        sensitive=_sensitive_changes(cur,nxt)
        if sensitive and not str(row.get("story_event") or "").strip():
            e.append(f"frame {key} sensitive world-state change requires story_event: {','.join(sensitive)}")
        cur=nxt
    return e

def resolve_frame(ep,frame):
    ep=Path(ep).resolve();d=read_json(ep/REL);n=int(frame)
    cur=copy.deepcopy(d.get("initial_state") or {})
    for i in range(1,n+1):
        row=(d.get("frames") or {}).get(f"{i:02d}") or {}
        cur=_merge(cur,row.get("delta") or {})
    return {"frame":f"{n:02d}","world_state":cur,"world_state_sha256":sha_json(cur)}

def self_test():
    assert _merge({"a":1},{"a":2})["a"]==2
    assert "status" in IDENTITY_FIELDS
    print("WORLD STATE SELF-TEST PASS")

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
        print("WORLD STATE VERIFIED");return 0
    if a.cmd=="resolve-frame":print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
