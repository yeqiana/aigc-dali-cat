#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CASES=ROOT/"standards"/"story_regressions"/"cases.json"
def eval_case(d,p):
    if d=="location_reality": return "fail" if p.get("rural_village") and p.get("public_bus_visible") and not p.get("transport_pre_registered") else "pass"
    if d=="viewpoint_physics": return "fail" if p.get("first_person_device_fully_visible") and not p.get("second_source_explained") else "pass"
    if d=="minimal_edit": return "fail" if p.get("edit_mode")=="subtitle_only" and p.get("locked_base_hash_changed") else "pass"
    if d=="caption_voice": return "warning" if int(p.get("consecutive_i_found",0))>=3 else "pass"
    if d=="payoff": return "fail" if p.get("major_final_anomaly") and not p.get("setup_exists") else "pass"
    if d=="homogeneity": return "fail" if all(p.get(k) for k in ("same_core_mechanism","same_middle_escalation","same_climax_form")) else "pass"
    return "unknown"
def run():
    d=json.loads(CASES.read_text(encoding="utf-8")); e=[]
    for c in d["cases"]:
        got=eval_case(c["dimension"],c["input"])
        if got!=c["expected"]: e.append(c["id"]+":"+got)
    return e
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("cmd",choices=["run","show"]); a=ap.parse_args()
    if a.cmd=="show": print(CASES.read_text(encoding="utf-8")); return 0
    e=run()
    if e:[print("FAIL:",x) for x in e]; return 2
    print("STORY REGRESSION PASS"); return 0
if __name__=="__main__":raise SystemExit(main())
