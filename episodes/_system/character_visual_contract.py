#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Camera-friendly ordinary cast + original-character anti-likeness contract."""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path

REL=Path("meta/character-visual-contract.json")
PRIMARY_ATTRACTIVENESS="moderately_above_average_but_real"
SECONDARY_ATTRACTIVENESS="ordinary_camera_friendly"
FEMALE_LEAD_BUILD="slim_proportionate_natural"
MALE_LEAD_BUILD="lean_proportionate_natural"

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict): raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def _primary_ids(cp):
    members=((cp.get("cast") or {}).get("members") or [])
    pov=str(((cp.get("pov") or {}).get("character_id")) or "")
    ids=[]
    if pov: ids.append(pov)
    pov_gender=next((m.get("gender") for m in members if str(m.get("id"))==pov),None)
    opposite=next((str(m.get("id")) for m in members if str(m.get("id"))!=pov and m.get("gender") and m.get("gender")!=pov_gender),None)
    if opposite: ids.append(opposite)
    return ids[:2]

def prepare(ep,force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    cp=read_json(ep/"meta/character-contract.json")
    members=((cp.get("cast") or {}).get("members") or [])
    primary=set(_primary_ids(cp))
    rows={}
    for m in members:
        cid=str(m.get("id") or "");g=str(m.get("gender") or "");is_primary=cid in primary
        if g=="female" and is_primary:body=FEMALE_LEAD_BUILD
        elif g=="male" and is_primary:body=MALE_LEAD_BUILD
        else:body="ordinary_healthy_natural"
        rows[cid]={
          "visual_priority":"primary" if is_primary else "supporting",
          "attractiveness":PRIMARY_ATTRACTIVENESS if is_primary else SECONDARY_ATTRACTIVENESS,
          "body_build":body,
          "body_build_story_override_reason":"",
          "face_identity":{
            "original_character":True,
            "independently_distinct_face":True,
            "celebrity_likeness":False,
            "influencer_face":False,
            "fashion_model_styling":False,
            "reference_similarity_target":"low",
            "skin_texture":"natural_visible_texture",
            "slight_asymmetry":True,
            "master_identity_locked":False
          },
          "hair":{
            "haircut_anchor":"",
            "hair_length_anchor":"",
            "allowed_state_variation":["wet","windblown","messy","hood_up","tied_or_untied_with_story_reason"],
            "exact_reference_hairstyle_copy":False
          },
          "presentation":{
            "heavy_makeup":False,
            "porcelain_skin":False,
            "excessive_face_symmetry":False,
            "ai_beauty_face":False,
            "camera_friendly_but_believable":True
          }
        }
    d={
      "schema_version":1,"status":"DRAFT","created_at":now(),
      "primary_cast_ids":list(primary),"members":rows,
      "reference_policy":{
        "allowed_reference_roles":["age_vibe","attractiveness_range","realism","capture_style","clothing_direction","color_mood"],
        "must_not_copy":["exact_face_geometry","exact_eye_nose_mouth_combination","exact_hairstyle","distinctive_personal_markers","celebrity_identity"],
        "reference_is_not_identity_master":True,
        "real_person_exact_likeness_forbidden":True
      },
      "master_policy":{
        "preferred_identity_source":["approved_original_character_master","ordinary_baseline_group_selfie","original_character_library_asset"],
        "preproduction_only_must_not_generate_master_images":True,
        "ordinary_baseline_can_become_group_identity_master":True
      },
      "realism_priority":True,
      "note":"核心角色可以略高于普通路人颜值，但必须像现实中真实存在的二十来岁普通年轻人。"
    }
    write_json(target,d);return d

def validate(ep,require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/character-visual-contract.json missing"]
    d=read_json(p);e=[]
    if d.get("schema_version")!=1:e.append("character visual schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED":e.append("character visual contract must be LOCKED")
    rp=d.get("reference_policy") or {}
    if rp.get("real_person_exact_likeness_forbidden") is not True:e.append("exact real-person likeness must be forbidden")
    if rp.get("reference_is_not_identity_master") is not True:e.append("reference image must not become identity master")
    primary=set(str(x) for x in (d.get("primary_cast_ids") or []))
    members=d.get("members") or {}
    if not members:e.append("character visual members missing")
    for cid,row in members.items():
        face=row.get("face_identity") or {};hair=row.get("hair") or {};pres=row.get("presentation") or {}
        if face.get("original_character") is not True:e.append(f"{cid} original_character must be true")
        if face.get("independently_distinct_face") is not True:e.append(f"{cid} independently_distinct_face must be true")
        if face.get("celebrity_likeness") is not False:e.append(f"{cid} celebrity_likeness must be false")
        if face.get("reference_similarity_target")!="low":e.append(f"{cid} reference_similarity_target must be low")
        if require_locked and face.get("master_identity_locked") is not True:e.append(f"{cid} master_identity_locked must be true")
        if not str(hair.get("haircut_anchor") or "").strip():e.append(f"{cid} haircut_anchor must be explicit")
        if not str(hair.get("hair_length_anchor") or "").strip():e.append(f"{cid} hair_length_anchor must be explicit")
        if hair.get("exact_reference_hairstyle_copy") is not False:e.append(f"{cid} exact reference hairstyle copy forbidden")
        if pres.get("porcelain_skin") is not False or pres.get("ai_beauty_face") is not False:e.append(f"{cid} over-beautified face forbidden")
        if cid in primary and row.get("attractiveness")!=PRIMARY_ATTRACTIVENESS:e.append(f"{cid} primary attractiveness must stay moderately-above-average but real")
        if row.get("body_build")=="story_specific" and not str(row.get("body_build_story_override_reason") or "").strip():
            e.append(f"{cid} story_specific body build requires override reason")
    return e

def self_test():
    assert FEMALE_LEAD_BUILD=="slim_proportionate_natural"
    assert PRIMARY_ATTRACTIVENESS=="moderately_above_average_but_real"
    print("CHARACTER VISUAL CONTRACT SELF-TEST PASS")

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
        print("CHARACTER VISUAL CONTRACT VERIFIED");return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
