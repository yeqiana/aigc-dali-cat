#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scene-aware wardrobe schedule with physical plausibility checks."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import story_json
import character_contract
import episode_contract_persistence

REL=Path("meta/wardrobe-contract.json")
CONTRACT_TYPE="WARDROBE"
COLD={"cold","very_cold"}
COOL_COLD={"cool","cold","very_cold"}
OUTDOOR={"outdoor","roadside","scenic_checkin","hiking","mountain_stop"}
HIGH_ALT={"sichuan_tibet_route","high_altitude_road_trip","plateau_road_trip"}
WARM_OUTER=("冲锋衣","抓绒","羽绒","保暖外套","硬壳","软壳","防风外套","shell","fleece","down")
THICK_LEG=("厚裤袜","加绒裤袜","保暖打底","羊毛裤袜","thermal tights","fleece tights")
CAMISOLE=("吊带","背心","camisole","tank top")
SKIRT=("裙","skirt")

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
    if not isinstance(data,dict):return None
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
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

def prepare(ep,force=False,destructive_reset=False):
    ep=Path(ep).resolve()
    existing=load(ep)
    if isinstance(existing,dict):
        if not force:return existing
        if existing.get("status")=="LOCKED" and not destructive_reset:
            raise ValueError("refusing destructive wardrobe prepare --force on LOCKED authority; use rebind-source or --destructive-reset")
    cp=character_contract.load(ep) or {}
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
    return save(ep,d)

def validate(ep,require_locked=True,ignore_source_binding=False):
    ep=Path(ep).resolve();d=load(ep)
    if not isinstance(d,dict):return ["meta/wardrobe-contract.json missing"]
    e=[];total=frame_count(ep)
    if d.get("schema_version")!=1:e.append("wardrobe schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("wardrobe contract must be LOCKED")
    temporal=ep/"meta/temporal-continuity.json"
    if not temporal.is_file():e.append("temporal continuity missing for wardrobe")
    elif not ignore_source_binding and str(d.get("source_temporal_sha256") or "").lower()!=sha(temporal).lower():e.append("wardrobe source_temporal_sha256 stale")
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

def rebind_source(ep,reason):
    ep=Path(ep).resolve();temporal=ep/"meta/temporal-continuity.json"
    d=load(ep)
    if not isinstance(d,dict):raise ValueError("meta/wardrobe-contract.json missing")
    if not temporal.is_file():raise ValueError("temporal continuity missing for wardrobe")
    reason=str(reason or "").strip()
    if not reason:raise ValueError("rebind-source requires a non-empty reason")
    if d.get("status")!="LOCKED":raise ValueError("rebind-source requires LOCKED wardrobe authority")
    content_errors=validate(ep,True,ignore_source_binding=True)
    if content_errors:raise ValueError("wardrobe content invalid; refusing source rebind: "+"; ".join(content_errors[:8]))
    old=str(d.get("source_temporal_sha256") or "")
    new=sha(temporal)
    if old.lower()==new.lower():return d
    d["source_temporal_sha256"]=new
    d.setdefault("source_rebind_history",[]).append({"from":old,"to":new,"reason":reason})
    save(ep,d)
    errors=validate(ep,True)
    if errors:raise ValueError("wardrobe source rebind failed validation: "+"; ".join(errors[:8]))
    return d

def resolve_frame(ep,frame):
    ep=Path(ep).resolve();d=load(ep) or {};key=f"{int(frame):02d}"
    return {"frame":key,"wardrobe":(d.get("frames") or {}).get(key) or {}}

def self_test():
    sample={"garments":["漂亮裙子"],"leg_layer":"厚裤袜","outer_layer":"冲锋衣"}
    t=_txt(sample)
    assert _has(t,SKIRT) and _has(t,THICK_LEG) and _has(t,WARM_OUTER)
    print("WARDROBE CONTRACT SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("--force",action="store_true");p.add_argument("--destructive-reset",action="store_true")
    p=sub.add_parser("rebind-source");p.add_argument("episode_dir");p.add_argument("--reason",required=True)
    p=sub.add_parser("validate");p.add_argument("episode_dir");p.add_argument("--allow-draft",action="store_true")
    p=sub.add_parser("resolve-frame");p.add_argument("episode_dir");p.add_argument("frame",type=int)
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.force,a.destructive_reset),ensure_ascii=False,indent=2));return 0
    if a.cmd=="rebind-source":print(json.dumps(rebind_source(ep,a.reason),ensure_ascii=False,indent=2));return 0
    if a.cmd=="validate":
        e=validate(ep,not a.allow_draft)
        if e:[print("FAIL:",x) for x in e];return 2
        print("WARDROBE CONTRACT VERIFIED");return 0
    if a.cmd=="resolve-frame":print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
    print(json.dumps(load(ep) or {},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
