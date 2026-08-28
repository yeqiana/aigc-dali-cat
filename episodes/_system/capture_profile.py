#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REG=ROOT/"standards"/"capture_profiles"
IDX=REG/"index.json"
REQ={"dynamic_range","low_light","motion","focus","white_balance","compression","edge_behavior"}
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def validate():
    if not IDX.exists(): return ["missing index"]
    d=load(IDX); e=[]; seen=set()
    for x in d.get("profiles",[]):
        pid=x.get("profile_id")
        if not pid or pid in seen: e.append("duplicate profile "+str(pid)); continue
        seen.add(pid); p=REG/x["file"]
        if not p.exists(): e.append(pid+" missing file"); continue
        q=load(p); miss=REQ-set((q.get("physics") or {}).keys())
        if q.get("profile_id")!=pid: e.append(pid+" id mismatch")
        if miss: e.append(pid+" missing "+str(sorted(miss)))
    if d.get("default_profile_id") not in seen:e.append("default missing")
    return e
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("validate"); sub.add_parser("list"); p=sub.add_parser("show"); p.add_argument("id")
    a=ap.parse_args(); d=load(IDX)
    if a.cmd=="list":
        for x in d["profiles"]: print(x["profile_id"],x["display_name"]); return 0
    if a.cmd=="show":
        x=next((x for x in d["profiles"] if x["profile_id"]==a.id),None)
        if not x: return 2
        print((REG/x["file"]).read_text(encoding="utf-8")); return 0
    e=validate()
    if e:
        [print("FAIL:",x) for x in e]; return 2
    print("CAPTURE PROFILE PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
