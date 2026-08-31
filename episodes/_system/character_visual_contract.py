#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Camera-friendly ordinary cast + split identity-spec / pixel-master contract."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/character-visual-contract.json")
PIXEL_MASTER_REL=Path("meta/character-pixel-master.json")
PRIMARY_ATTRACTIVENESS="moderately_above_average_but_real"
SECONDARY_ATTRACTIVENESS="ordinary_camera_friendly"
FEMALE_LEAD_BUILD="slim_proportionate_natural"
MALE_LEAD_BUILD="lean_proportionate_natural"

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def _primary_ids(cp):
    members=((cp.get("cast") or {}).get("members") or [])
    pov=str(((cp.get("pov") or {}).get("character_id")) or "")
    ids=[]
    if pov:ids.append(pov)
    pov_gender=next((m.get("gender") for m in members if str(m.get("id"))==pov),None)
    opposite=next((str(m.get("id")) for m in members if str(m.get("id"))!=pov and m.get("gender") and m.get("gender")!=pov_gender),None)
    if opposite:ids.append(opposite)
    return ids[:2]

def prepare(ep,force=False):
    ep=Path(ep).resolve(); target=ep/REL
    if target.is_file() and not force:return read_json(target)
    cp=read_json(ep/"meta/character-contract.json")
    members=((cp.get("cast") or {}).get("members") or [])
    primary=set(_primary_ids(cp)); rows={}
    for m in members:
        cid=str(m.get("id") or ""); g=str(m.get("gender") or ""); is_primary=cid in primary
        if g=="female" and is_primary:body=FEMALE_LEAD_BUILD
        elif g=="male" and is_primary:body=MALE_LEAD_BUILD
        else:body="ordinary_healthy_natural"
        rows[cid]={
          "visual_priority":"primary" if is_primary else "supporting",
          "attractiveness":PRIMARY_ATTRACTIVENESS if is_primary else SECONDARY_ATTRACTIVENESS,
          "body_build":body,"body_build_story_override_reason":"",
          "face_identity":{
            "original_character":True,"independently_distinct_face":True,
            "celebrity_likeness":False,"influencer_face":False,
            "fashion_model_styling":False,"reference_similarity_target":"low",
            "skin_texture":"natural_visible_texture","slight_asymmetry":True,
            "identity_spec_locked":False
          },
          "hair":{
            "haircut_anchor":"","hair_length_anchor":"",
            "allowed_state_variation":["wet","windblown","messy","hood_up","tied_or_untied_with_story_reason"],
            "exact_reference_hairstyle_copy":False
          },
          "presentation":{
            "heavy_makeup":False,"porcelain_skin":False,
            "excessive_face_symmetry":False,"ai_beauty_face":False,
            "camera_friendly_but_believable":True
          }
        }
    d={
      "schema_version":2,"status":"DRAFT","created_at":now(),
      "lock_model":"identity_spec_before_images__pixel_master_after_visual_lock",
      "primary_cast_ids":list(primary),"members":rows,
      "reference_policy":{
        "allowed_reference_roles":["age_vibe","attractiveness_range","realism","capture_style","clothing_direction","color_mood"],
        "must_not_copy":["exact_face_geometry","exact_eye_nose_mouth_combination","exact_hairstyle","distinctive_personal_markers","celebrity_identity"],
        "reference_is_not_identity_master":True,"real_person_exact_likeness_forbidden":True
      },
      "master_policy":{
        "preferred_identity_source":["character_pixel_master","ordinary_baseline_group_selfie","original_character_library_asset"],
        "preproduction_only_must_not_generate_master_images":True,
        "ordinary_baseline_can_become_group_identity_master":True,
        "pixel_master_artifact":PIXEL_MASTER_REL.as_posix(),
        "pixel_master_created_only_after_visual_lock_pass":True
      },
      "realism_priority":True,
      "note":"Story Lock 只锁人物规格；真实像素母版必须由通过 Visual Lock 的 ordinary_baseline 建立。"
    }
    write_json(target,d); return d

def _identity_spec_locked(face):
    if "identity_spec_locked" in face:return face.get("identity_spec_locked") is True
    # compatibility with first Director Profile V2 hotfix
    return face.get("master_identity_locked") is True

def validate(ep,require_locked=True):
    ep=Path(ep).resolve(); p=ep/REL
    if not p.is_file():return ["meta/character-visual-contract.json missing"]
    d=read_json(p); e=[]
    if int(d.get("schema_version") or 1) not in {1,2}:e.append("unsupported character visual schema_version")
    if require_locked and d.get("status")!="LOCKED":e.append("character visual contract must be LOCKED")
    rp=d.get("reference_policy") or {}
    if rp.get("real_person_exact_likeness_forbidden") is not True:e.append("exact real-person likeness must be forbidden")
    if rp.get("reference_is_not_identity_master") is not True:e.append("reference image must not become identity master")
    primary=set(str(x) for x in (d.get("primary_cast_ids") or [])); members=d.get("members") or {}
    if not members:e.append("character visual members missing")
    for cid,row in members.items():
        face=row.get("face_identity") or {}; hair=row.get("hair") or {}; pres=row.get("presentation") or {}
        if face.get("original_character") is not True:e.append(f"{cid} original_character must be true")
        if face.get("independently_distinct_face") is not True:e.append(f"{cid} independently_distinct_face must be true")
        if face.get("celebrity_likeness") is not False:e.append(f"{cid} celebrity_likeness must be false")
        if face.get("reference_similarity_target")!="low":e.append(f"{cid} reference_similarity_target must be low")
        if require_locked and not _identity_spec_locked(face):e.append(f"{cid} identity_spec_locked must be true")
        if not str(hair.get("haircut_anchor") or "").strip():e.append(f"{cid} haircut_anchor must be explicit")
        if not str(hair.get("hair_length_anchor") or "").strip():e.append(f"{cid} hair_length_anchor must be explicit")
        if hair.get("exact_reference_hairstyle_copy") is not False:e.append(f"{cid} exact reference hairstyle copy forbidden")
        if pres.get("porcelain_skin") is not False or pres.get("ai_beauty_face") is not False:e.append(f"{cid} over-beautified face forbidden")
        if cid in primary and row.get("attractiveness")!=PRIMARY_ATTRACTIVENESS:e.append(f"{cid} primary attractiveness must stay moderately-above-average but real")
        if row.get("body_build")=="story_specific" and not str(row.get("body_build_story_override_reason") or "").strip():
            e.append(f"{cid} story_specific body build requires override reason")
    return e

def pixel_master_required(ep):
    ep=Path(ep).resolve(); p=ep/"meta/opening-social-anchor.json"
    if not p.is_file():return False
    try:
        d=read_json(p)
        if d.get("applicable") is not True:return False
        for x in d.get("opening_frames") or []:
            if not isinstance(x,dict) or x.get("selfie") is not True:continue
            try:n=int(x.get("frame"))
            except Exception:continue
            if n in {1,2} and int(x.get("people_visible") or 0)>=2:return True
        return False
    except Exception:return False

def _repo_asset(raw):
    p=Path(str(raw)); p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    p.relative_to(ROOT.resolve())
    return p

def lock_pixel_master(ep,*,frame,asset_path,asset_sha256,frame_contract_sha256,source_role="ordinary_baseline"):
    ep=Path(ep).resolve()
    spec_errors=validate(ep,True)
    if spec_errors:raise ValueError("character visual spec invalid: "+"; ".join(spec_errors[:8]))
    asset=_repo_asset(asset_path)
    if not asset.is_file():raise ValueError(f"pixel master asset missing: {asset_path}")
    actual=sha_file(asset)
    if actual.lower()!=str(asset_sha256 or "").lower():raise ValueError("pixel master asset sha mismatch")
    data={
      "schema_version":1,"status":"LOCKED","created_at":now(),
      "source_role":source_role,"frame":f"{int(frame):02d}",
      "asset_path":asset.resolve().relative_to(ROOT.resolve()).as_posix(),
      "sha256":actual,"frame_contract_sha256":str(frame_contract_sha256 or ""),
      "character_visual_contract_path":REL.as_posix(),
      "character_visual_contract_sha256":sha_file(ep/REL),
      "immutable_identity_evidence":True
    }
    write_json(ep/PIXEL_MASTER_REL,data); return data

def validate_pixel_master(ep,expected=None):
    ep=Path(ep).resolve(); p=ep/PIXEL_MASTER_REL
    if not p.is_file():return ["character pixel master missing"]
    d=read_json(p); e=[]
    if d.get("schema_version")!=1:e.append("character pixel master schema_version must be 1")
    if d.get("status")!="LOCKED":e.append("character pixel master must be LOCKED")
    spec=ep/REL
    if not spec.is_file():e.append("character visual spec missing")
    elif str(d.get("character_visual_contract_sha256") or "").lower()!=sha_file(spec).lower():e.append("character pixel master spec sha stale")
    try:
        asset=_repo_asset(d.get("asset_path"))
        if not asset.is_file():e.append("character pixel master asset missing")
        elif sha_file(asset).lower()!=str(d.get("sha256") or "").lower():e.append("character pixel master asset sha mismatch")
    except Exception:e.append("character pixel master asset path invalid")
    if d.get("source_role")!="ordinary_baseline":e.append("character pixel master must come from ordinary_baseline")
    if expected:
        for key in ("asset_path","sha256","frame_contract_sha256"):
            if str(d.get(key) or "").lower()!=str(expected.get(key) or "").lower():e.append(f"character pixel master {key} mismatch")
        if str(d.get("frame") or "").zfill(2)!=str(expected.get("frame") or "").zfill(2):e.append("character pixel master frame mismatch")
    return e

def pixel_master_reference(ep):
    ep=Path(ep).resolve(); p=ep/PIXEL_MASTER_REL
    if not p.is_file():return None
    errors=validate_pixel_master(ep)
    if errors:raise ValueError("invalid character pixel master: "+"; ".join(errors[:8]))
    d=read_json(p)
    return {"path":d["asset_path"],"role":"character_pixel_master","kind":"identity","sha256":d["sha256"]}

def self_test():
    assert PIXEL_MASTER_REL.as_posix()=="meta/character-pixel-master.json"
    assert _identity_spec_locked({"identity_spec_locked":True})
    assert _identity_spec_locked({"master_identity_locked":True})
    print("CHARACTER VISUAL CONTRACT CLOSURE SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare"); p.add_argument("episode_dir"); p.add_argument("--force",action="store_true")
    p=sub.add_parser("validate"); p.add_argument("episode_dir"); p.add_argument("--allow-draft",action="store_true")
    p=sub.add_parser("verify-pixel-master"); p.add_argument("episode_dir")
    p=sub.add_parser("show"); p.add_argument("episode_dir")
    p=sub.add_parser("show-pixel-master"); p.add_argument("episode_dir")
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.force),ensure_ascii=False,indent=2));return 0
    if a.cmd=="validate":
        e=validate(ep,not a.allow_draft)
        if e:[print("FAIL:",x) for x in e];return 2
        print("CHARACTER VISUAL SPEC VERIFIED");return 0
    if a.cmd=="verify-pixel-master":
        e=validate_pixel_master(ep)
        if e:[print("FAIL:",x) for x in e];return 2
        print("CHARACTER PIXEL MASTER VERIFIED");return 0
    p=ep/(PIXEL_MASTER_REL if a.cmd=="show-pixel-master" else REL)
    print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0

if __name__=="__main__":raise SystemExit(main())
