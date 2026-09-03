#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json
from pathlib import Path
import storyos_config
ROOT=Path(__file__).resolve().parents[2]
_CONFIG=storyos_config.load_config()
IDX=ROOT/str(storyos_config.get_path(_CONFIG,"visual.capture_profile_registry"))
DEFAULT_PROFILE_ID=str(storyos_config.get_path(_CONFIG,"visual.default_capture_profile_id"))
REQ={"dynamic_range","low_light","motion","focus","white_balance","compression","edge_behavior"}
def validate():
    d=json.loads(IDX.read_text(encoding="utf-8")); errors=[]; seen=set()
    for row in d.get("profiles",[]):
        pid=row.get("profile_id")
        if not pid or pid in seen: errors.append("duplicate/missing profile id"); continue
        seen.add(pid); p=IDX.parent/row["file"]
        if not p.is_file(): errors.append(f"{pid}: file missing"); continue
        x=json.loads(p.read_text(encoding="utf-8")); missing=REQ-set((x.get("physics") or {}).keys())
        if x.get("profile_id")!=pid: errors.append(f"{pid}: id mismatch")
        if missing: errors.append(f"{pid}: missing {sorted(missing)}")
    if DEFAULT_PROFILE_ID not in seen: errors.append("configured default missing")
    return errors
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True); sub.add_parser("validate"); sub.add_parser("list"); p=sub.add_parser("show"); p.add_argument("profile_id"); a=ap.parse_args()
    d=json.loads(IDX.read_text(encoding="utf-8"))
    if a.cmd=="list":
        [print(x["profile_id"],x["display_name"]) for x in d["profiles"]]; return 0
    if a.cmd=="show":
        x=next(v for v in d["profiles"] if v["profile_id"]==a.profile_id); print((IDX.parent/x["file"]).read_text(encoding="utf-8")); return 0
    e=validate()
    if e: [print("FAIL:",x) for x in e]; return 2
    print("CAPTURE PROFILE PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
