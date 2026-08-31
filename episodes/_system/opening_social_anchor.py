#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Opening Social Anchor contract for Story OS V2.1.

For multi-person travel / return-home / outing stories, strongly prefer Frame
01-02 to establish the group through a realistic vehicle selfie or destination
check-in selfie. Conditional rule; not a new Episode stage.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

REL=Path("meta/opening-social-anchor.json")
MODES={"vehicle_selfie","destination_checkin_selfie","mixed_selfie","not_applicable"}
ANOMALY={"none","micro_background_only"}
MIN_PEOPLE=2

def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict): raise ValueError(f"JSON root must be object: {p}")
    return d

def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def prepare(ep,force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    data={
      "schema_version":1,"status":"DRAFT","applicable":True,"mode":"vehicle_selfie",
      "reason":"多人同行故事默认优先用前1-2张自拍合照建立人物关系与正常世界。",
      "exception_reason":"",
      "opening_frames":[{
        "frame":"01","selfie":True,"location_type":"vehicle","people_visible":2,
        "relationship_anchor":True,"clothing_anchor_visible":True,
        "natural_unpolished_capture":True,"anomaly_level":"none",
        "notes":"优先车上出发/途中自拍；也可改为 destination_checkin。"
      }],
      "rules":{
        "preferred_frame_range":[1,2],
        "preferred_contexts":["vehicle","destination_checkin"],
        "selfie_required_when_applicable":True,
        "minimum_people_visible":2,
        "establish_relationship_before_anomaly":True,
        "strong_anomaly_forbidden_in_opening_anchor":True,
        "commercial_or_staged_group_photo_forbidden":True,
        "allow_exception_with_reason":True
      }}
    write_json(target,data);return data

def validate(ep,require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/opening-social-anchor.json missing"]
    d=read_json(p);e=[]
    if d.get("schema_version")!=1:e.append("opening social anchor schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("opening social anchor status must be LOCKED")
    applicable=d.get("applicable") is True
    mode=str(d.get("mode") or "")
    if mode not in MODES:e.append(f"invalid opening social anchor mode: {mode}")
    if not applicable:
        if mode!="not_applicable":e.append("non-applicable opening anchor must use mode=not_applicable")
        if not str(d.get("exception_reason") or "").strip():e.append("non-applicable opening anchor requires exception_reason")
        return e
    if mode=="not_applicable":e.append("applicable opening anchor cannot use mode=not_applicable")
    frames=d.get("opening_frames") or []
    if not frames:
        e.append("applicable opening anchor requires at least one opening frame");return e
    if len(frames)>2:e.append("opening social anchor may occupy at most first 2 frames")
    has_selfie=False
    for row in frames:
        try:n=int(row.get("frame"))
        except Exception:
            e.append("opening anchor frame id invalid");continue
        if n not in {1,2}:e.append(f"opening anchor frame must be 01 or 02, got {n:02d}")
        if row.get("selfie") is True:has_selfie=True
        if int(row.get("people_visible") or 0)<MIN_PEOPLE:e.append(f"frame {n:02d} needs >=2 visible people")
        if row.get("relationship_anchor") is not True:e.append(f"frame {n:02d} must establish group relationship")
        if row.get("natural_unpolished_capture") is not True:e.append(f"frame {n:02d} must be natural unpolished selfie")
        if str(row.get("anomaly_level") or "") not in ANOMALY:e.append(f"frame {n:02d} opening anomaly must be none or micro_background_only")
        if str(row.get("location_type") or "") not in {"vehicle","destination_checkin"}:e.append(f"frame {n:02d} location_type invalid")
    if not has_selfie:e.append("at least one of frame 01-02 must be selfie when applicable")
    return e

def self_test():
    assert "vehicle_selfie" in MODES
    assert "destination_checkin_selfie" in MODES
    assert "micro_background_only" in ANOMALY
    print("OPENING SOCIAL ANCHOR SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("validate");p.add_argument("episode_dir");p.add_argument("--allow-draft",action="store_true")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.force),ensure_ascii=False,indent=2));return 0
    if a.cmd=="validate":
        e=validate(ep,not a.allow_draft)
        if e:[print("FAIL:",x) for x in e];return 2
        print("OPENING SOCIAL ANCHOR VERIFIED");return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0

if __name__=="__main__":raise SystemExit(main())
