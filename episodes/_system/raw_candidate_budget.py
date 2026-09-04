#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Budget pre-ledger raw candidate attempts so one frame cannot consume an unbounded image loop.

This is an operator/runtime contract. Technical retries must not call claim().
"""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=Path("meta/runtime/raw-candidate-budget.json");CFG=ROOT/"runtimes/runtime-fast-path-v251.json";KINDS={"original","repair","exception"}
def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"));return d if isinstance(d,dict) else {}
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def limits():
    try:return read_json(CFG).get("raw_candidate_budget") or {"original":2,"repair":2,"exception":2}
    except Exception:return {"original":2,"repair":2,"exception":2}
def load(ep):
    p=Path(ep).resolve()/REL
    return read_json(p) if p.is_file() else {"schema_version":1,"module_version":"2.5.1","updated_at":now(),"frames":{}}
def claim(ep,frame,kind,reason=""):
    if kind not in KINDS:raise ValueError(f"kind must be {sorted(KINDS)}")
    d=load(ep);key=f"{int(frame):02d}";bucket=d.setdefault("frames",{}).setdefault(key,{}).setdefault(kind,{"used":0,"attempts":[]});limit=int(limits().get(kind,2))
    if int(bucket.get("used") or 0)>=limit:return False,{"frame":key,"kind":kind,"used":bucket.get("used"),"limit":limit,"decision":"STOP_IMAGE_LOOP"}
    bucket["used"]=int(bucket.get("used") or 0)+1;bucket.setdefault("attempts",[]).append({"at":now(),"reason":reason});d["updated_at"]=now();write_json(Path(ep).resolve()/REL,d)
    return True,{"frame":key,"kind":kind,"used":bucket["used"],"limit":limit,"decision":"ALLOW"}
def self_test():
    assert int(limits()["repair"])>=1;print("RAW CANDIDATE BUDGET V2.5.1 SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("claim");p.add_argument("episode_dir");p.add_argument("--frame",required=True,type=int);p.add_argument("--kind",required=True,choices=sorted(KINDS));p.add_argument("--reason",default="")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="show":print(json.dumps(load(a.episode_dir),ensure_ascii=False,indent=2));return 0
    ok,row=claim(a.episode_dir,a.frame,a.kind,a.reason);print(json.dumps(row,ensure_ascii=False));return 0 if ok else 2
if __name__=="__main__":raise SystemExit(main())
