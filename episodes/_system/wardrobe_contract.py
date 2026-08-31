#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scene-aware wardrobe schedule with physical plausibility checks."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

REL=Path("meta/wardrobe-contract.json")
COLD={"cold","very_cold"}
COOL_COLD={"cool","cold","very_cold"}
OUTDOOR={"outdoor","roadside","scenic_checkin","hiking","mountain_stop"}
HIGH_ALT={"sichuan_tibet_route","high_altitude_road_trip","plateau_road_trip"}
WARM_OUTER=("冲锋衣","抓绒","羽绒","保暖外套","硬壳","软壳","防风外套","shell","fleece","down")
THICK_LEG=("厚裤袜","加绒裤袜","保暖打底","羊毛裤袜","thermal tights","fleece tights")
CAMISOLE=("吊带","背心","camisole","tank top")
SKIRT=("裙","skirt")

def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_count(ep):
    d=read_json(Path(ep)/"meta/release-manifest.json")
    return int(((d.get("release") or {}).get("body_frame_count")) or 0)
def _txt(outfit):
    parts=[]
    for k in ("garments","outer_layer","leg_layer","headwear","footwear"):
        v=outfit.get(k)
        if isinstance(v,list):parts.extend(str(x) for x in v)
        elif v:parts.append(str(v))
    return " ".join(parts).lower()
def _has(text,words):return any(w.lower() in text for w in words)

def prepare(ep,force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    cp=read_json(ep/"meta/character-contract.json")
    members=((cp.get("cast") or {}).get("members") or [])
    total=frame_count(ep);frames={}
    for n in range(1,total+1):
        outfits={}
        for m in members:
            cid=str(m.get("id"))
            outfits[cid]={"present":True,"look_id":"","garments":[],"outer_layer":"","leg_layer":"",
              "headwear":"","footwear":"","temperature_fit":"","weather_fit":"","activity_fit":"",
              "identity_consistent":True,"aesthetic_fit":"pretty_realistic","change_reason":""}
        frames[f"{n:02d}"]={"scene_context":"","location_type":"","temperature_band":"","weather":"","activity":"","outfits":outfits}
    temporal=ep/"meta/temporal-continuity.json"
    d={"schema_version":1,"status":"DRAFT","frame_count":total,
       "source_temporal_sha256":sha(temporal) if temporal.is_file() else None,
       "rules":{"wardrobe_changes_follow_scene_weather_temperature_activity":True,
         "female_lead_default_body":"slim_proportionate_natural",
         "pretty_clothes_allowed_when_physical_context_supports_them":True,
         "camisole_in_cold_outdoor_requires_warm_outer_layer":True,
         "skirt_in_cold_requires_thick_tights_and_warm_layer":True,
         "high_altitude_outdoor_requires_wind_or_insulation_layer":True,
         "outfit_change_requires_reason":True,"no_eroticized_framing_requirement":True},
       "frames":frames}
    write_json(target,d);return d

def validate(ep,require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/wardrobe-contract.json missing"]
    d=read_json(p);e=[];total=frame_count(ep)
    if d.get("schema_version")!=1:e.append("wardrobe schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("wardrobe contract must be LOCKED")
    temporal=ep/"meta/temporal-continuity.json"
    if not temporal.is_file():e.append("temporal continuity missing for wardrobe")
    elif str(d.get("source_temporal_sha256") or "").lower()!=sha(temporal).lower():e.append("wardrobe source_temporal_sha256 stale")
    frames=d.get("frames") or {}
    if len(frames)!=total:e.append(f"wardrobe frame count mismatch {len(frames)} != {total}")
    prev_looks={}
    for n in range(1,total+1):
        key=f"{n:02d}";row=frames.get(key)
        if not isinstance(row,dict):e.append(f"wardrobe frame {key} missing");continue
        scene=str(row.get("scene_context") or "");loc=str(row.get("location_type") or "");temp=str(row.get("temperature_band") or "")
        if temp not in {"hot","warm","mild","cool","cold","very_cold"}:e.append(f"frame {key} invalid temperature_band")
        if not scene:e.append(f"frame {key} scene_context missing")
        if not loc:e.append(f"frame {key} location_type missing")
        if not str(row.get("weather") or ""):e.append(f"frame {key} weather missing")
        if not str(row.get("activity") or ""):e.append(f"frame {key} activity missing")
        outfits=row.get("outfits") or {}
        if not outfits:e.append(f"frame {key} outfits missing")
        for cid,o in outfits.items():
            if o.get("present") is not True:continue
            look=str(o.get("look_id") or "")
            if not look:e.append(f"frame {key} {cid} look_id missing")
            if not isinstance(o.get("garments"),list) or not o.get("garments"):e.append(f"frame {key} {cid} garments missing")
            for fit in ("temperature_fit","weather_fit","activity_fit"):
                if str(o.get(fit) or "").upper()!="PASS":e.append(f"frame {key} {cid} {fit} must PASS")
            if o.get("identity_consistent") is not True:e.append(f"frame {key} {cid} identity_consistent must be true")
            text=_txt(o);is_outdoor=loc in OUTDOOR or "outdoor" in loc
            if temp in COLD and is_outdoor and _has(text,CAMISOLE) and not _has(text,WARM_OUTER):
                e.append(f"WARDROBE_PHYSICS_FAIL:{key}:{cid}:camisole cold outdoor requires warm outer layer")
            if temp in COLD and is_outdoor and _has(text,SKIRT):
                if not _has(text,THICK_LEG):e.append(f"WARDROBE_PHYSICS_FAIL:{key}:{cid}:cold skirt requires thick tights")
                if not _has(text,WARM_OUTER):e.append(f"WARDROBE_PHYSICS_FAIL:{key}:{cid}:cold skirt requires warm outer layer")
            if scene in HIGH_ALT and temp in COOL_COLD and is_outdoor and not _has(text,WARM_OUTER):
                e.append(f"WARDROBE_PHYSICS_FAIL:{key}:{cid}:high-altitude cool/cold outdoor requires shell/warm layer")
            prev=prev_looks.get(cid)
            if prev and look and look!=prev and not str(o.get("change_reason") or "").strip():
                e.append(f"WARDROBE_CHANGE_UNEXPLAINED:{key}:{cid}:{prev}->{look}")
            if look:prev_looks[cid]=look
    return e

def resolve_frame(ep,frame):
    ep=Path(ep).resolve();d=read_json(ep/REL);key=f"{int(frame):02d}"
    return {"frame":key,"wardrobe":(d.get("frames") or {}).get(key) or {}}

def self_test():
    sample={"garments":["漂亮裙子"],"leg_layer":"厚裤袜","outer_layer":"冲锋衣"}
    t=_txt(sample)
    assert _has(t,SKIRT) and _has(t,THICK_LEG) and _has(t,WARM_OUTER)
    print("WARDROBE CONTRACT SELF-TEST PASS")

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
        print("WARDROBE CONTRACT VERIFIED");return 0
    if a.cmd=="resolve-frame":print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
