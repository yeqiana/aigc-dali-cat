#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS directing-quality policy aggregator.

Adds no Episode stage. New work enables the policy before CREATIVE_STORY;
legacy locked Episodes stay compatible until explicitly enabled.
"""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
import voice_contract, storyboard_density_gate, capture_event_contract, world_state, opening_social_anchor, character_visual_contract, shot_progression_gate, wardrobe_contract, temporal_continuity_gate

REL=Path("meta/directing-quality.json")
def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def enabled(ep):
    p=Path(ep).resolve()/REL
    return p.is_file() and (read_json(p).get("enabled") is True)

def _episode_state(ep):
    p=Path(ep).resolve()/"meta/episode-state.json"
    return str((read_json(p).get("current_state") if p.is_file() else "") or "")

def advanced_enabled(ep):
    p=Path(ep).resolve()/REL
    if not p.is_file():return False
    d=read_json(p)
    return int(d.get("profile_version") or 1)>=2 or d.get("director_upgrade_v2") is True

def enable(ep):
    ep=Path(ep).resolve();p=ep/REL
    if p.is_file():
        d=read_json(p)
        if advanced_enabled(ep):return d
        # Compatibility: only upgrade while pre-Story-Lock.
        if _episode_state(ep) in {"","IDEA_LOCKED"}:
            d["profile_version"]=2
            d["director_upgrade_v2"]=True
            req=d.setdefault("requirements",{})
            req["story"]=["voice_contract","storyboard_density_delete_test","opening_social_anchor","character_visual_contract","shot_progression_gate"]
            req["preimage"]=["capture_event_contract","persistent_world_state","temporal_continuity","scene_aware_wardrobe"]
            write_json(p,d)
        return d
    d={"schema_version":1,"profile_version":2,"director_upgrade_v2":True,
       "enabled":True,"enabled_at":now(),"not_episode_stage":True,"legacy_auto_migration":False,
       "requirements":{
         "story":["voice_contract","storyboard_density_delete_test","opening_social_anchor","character_visual_contract","shot_progression_gate"],
         "preimage":["capture_event_contract","persistent_world_state","temporal_continuity","scene_aware_wardrobe"],
         "production":["asset_version_lineage"],
         "release":["text_audit","semantic_voice_review"],
         "regression":["curated_golden_episode_registry"]
       }}
    write_json(p,d);return d

def verify_story(ep):
    if not enabled(ep):return []
    base=["VOICE:"+x for x in voice_contract.validate(ep,True)] + \
         ["DENSITY:"+x for x in storyboard_density_gate.validate(ep,True)] + \
         ["OPENING:"+x for x in opening_social_anchor.validate(ep,True)]
    if not advanced_enabled(ep):return base
    return base + \
           ["CAST_VISUAL:"+x for x in character_visual_contract.validate(ep,True)] + \
           ["SHOT_PROGRESS:"+x for x in shot_progression_gate.validate(ep,True)]
def verify_preimage(ep):
    if not enabled(ep):return []
    base=["CAPTURE:"+x for x in capture_event_contract.validate(ep,True)] + \
         ["WORLD:"+x for x in world_state.validate(ep,True)]
    if not advanced_enabled(ep):return base
    return base + \
           ["TEMPORAL:"+x for x in temporal_continuity_gate.validate(ep,True)] + \
           ["WARDROBE:"+x for x in wardrobe_contract.validate(ep,True)]
def verify_release(ep):
    if not enabled(ep):return []
    return ["VOICE_RELEASE:"+x for x in voice_contract.validate_release_review(ep)]

def before_step(ep,step):
    if step=="CREATIVE_STORY":enable(ep)
def after_step(ep,step):
    if step=="CREATIVE_STORY":return verify_story(ep)
    if step=="VISUAL_LOCK":return verify_preimage(ep)
    if step=="RELEASE":return verify_release(ep)
    return []

def self_test():
    assert REL.as_posix()=="meta/directing-quality.json"
    print("DIRECTING QUALITY AGGREGATOR SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    for c in ("enable","verify-story","verify-preimage","verify-release","show"):
        p=sub.add_parser(c);p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="enable":print(json.dumps(enable(ep),ensure_ascii=False,indent=2));return 0
    if a.cmd=="show":
        p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
    e={"verify-story":verify_story,"verify-preimage":verify_preimage,"verify-release":verify_release}[a.cmd](ep)
    if e:[print("FAIL:",x) for x in e];return 2
    print("DIRECTING QUALITY VERIFIED");return 0
if __name__=="__main__":raise SystemExit(main())
