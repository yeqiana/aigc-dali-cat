# STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hard runtime budget for pre-ledger raw candidate attempts.

V2.5.1.1:
- a content candidate consumes budget once
- the same queue-item token is idempotent across technical retries
- technical failures release() the reservation, so they do not consume budget
"""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/raw-candidate-budget.json")
CFG=ROOT/"runtimes/runtime-fast-path-v251.json"
KINDS={"original","repair","exception"}

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    return d if isinstance(d,dict) else {}

def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def limits():
    try:
        return read_json(CFG).get("raw_candidate_budget") or {"original":2,"repair":2,"exception":2}
    except Exception:
        return {"original":2,"repair":2,"exception":2}

def load(ep):
    p=Path(ep).resolve()/REL
    d=read_json(p) if p.is_file() else {"schema_version":2,"module_version":"2.5.1.1","updated_at":now(),"frames":{}}
    d["schema_version"]=2
    d["module_version"]="2.5.1.1"
    d.setdefault("frames",{})
    return d

def kind_for_queue_item(item):
    return "repair" if str((item or {}).get("kind") or "").lower()=="repair" else "original"

def _find_token(d,token):
    if not token:
        return None
    for frame,kinds in (d.get("frames") or {}).items():
        for kind,bucket in (kinds or {}).items():
            claims=(bucket or {}).get("claims") or {}
            if token in claims:
                return frame,kind,bucket,claims[token]
    return None

def claim(ep,frame,kind,reason="",token=None):
    if kind not in KINDS:
        raise ValueError(f"kind must be {sorted(KINDS)}")
    d=load(ep);key=f"{int(frame):02d}"
    token=str(token or "").strip() or None
    if token:
        found=_find_token(d,token)
        if found:
            f,k,bucket,row=found
            return True,{"frame":f,"kind":k,"used":int(bucket.get("used") or 0),"limit":int(limits().get(k,2)),"decision":"REUSE_CLAIM","token":token,"claimed_at":row.get("at")}
    bucket=d.setdefault("frames",{}).setdefault(key,{}).setdefault(kind,{"used":0,"attempts":[],"claims":{}})
    bucket.setdefault("attempts",[]);bucket.setdefault("claims",{})
    limit=int(limits().get(kind,2))
    if int(bucket.get("used") or 0)>=limit:
        return False,{"frame":key,"kind":kind,"used":int(bucket.get("used") or 0),"limit":limit,"decision":"STOP_IMAGE_LOOP","token":token}
    bucket["used"]=int(bucket.get("used") or 0)+1
    row={"at":now(),"reason":reason,"token":token}
    bucket["attempts"].append(row)
    if token:bucket["claims"][token]=row
    d["updated_at"]=now();write_json(Path(ep).resolve()/REL,d)
    return True,{"frame":key,"kind":kind,"used":bucket["used"],"limit":limit,"decision":"ALLOW","token":token}

def release(ep,token,reason="technical_failure"):
    token=str(token or "").strip()
    if not token:return False,{"decision":"NO_TOKEN"}
    d=load(ep);found=_find_token(d,token)
    if not found:return False,{"decision":"TOKEN_NOT_FOUND","token":token}
    frame,kind,bucket,_=found
    bucket["claims"].pop(token,None)
    bucket["attempts"]=[x for x in (bucket.get("attempts") or []) if str((x or {}).get("token") or "")!=token]
    bucket["used"]=max(0,int(bucket.get("used") or 0)-1)
    d["updated_at"]=now();d.setdefault("released",[]).append({"at":now(),"token":token,"frame":frame,"kind":kind,"reason":reason})
    write_json(Path(ep).resolve()/REL,d)
    return True,{"decision":"RELEASED","token":token,"frame":frame,"kind":kind,"used":bucket["used"]}

def self_test():
    assert int(limits()["repair"])>=1
    assert kind_for_queue_item({"kind":"repair"})=="repair"
    assert kind_for_queue_item({"kind":"original"})=="original"
    print("RAW CANDIDATE BUDGET V2.5.1.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("claim");p.add_argument("episode_dir");p.add_argument("--frame",required=True,type=int);p.add_argument("--kind",required=True,choices=sorted(KINDS));p.add_argument("--reason",default="");p.add_argument("--token")
    p=sub.add_parser("release");p.add_argument("episode_dir");p.add_argument("--token",required=True);p.add_argument("--reason",default="technical_failure")
    p=sub.add_parser("show");p.add_argument("episode_dir");sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="show":print(json.dumps(load(a.episode_dir),ensure_ascii=False,indent=2));return 0
    if a.cmd=="release":
        ok,row=release(a.episode_dir,a.token,a.reason);print(json.dumps(row,ensure_ascii=False));return 0 if ok else 2
    ok,row=claim(a.episode_dir,a.frame,a.kind,a.reason,a.token);print(json.dumps(row,ensure_ascii=False));return 0 if ok else 2

if __name__=="__main__":raise SystemExit(main())
