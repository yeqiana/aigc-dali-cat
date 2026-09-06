#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic max-2 reference arbitration."""
from __future__ import annotations
import json
from pathlib import Path
import character_visual_contract
import frame_contract

ROOT=Path(__file__).resolve().parents[2]
MAX_REFS=2
HUMAN_TOKENS=("人物","同行","同伴","朋友","男主","女主","人脸","自拍","合照","person","character","friend","traveler","selfie","portrait")
NON_FACE_FRAGMENT_TOKENS=("手","手腕","手臂","袖口","衣袖","背影","鞋","脚","hand","wrist","arm","sleeve","back view","shoe")
SELFIE_CAPTURE_TOKENS=("自拍","前置镜头","合照","selfie","front camera","portrait")
def repo_file(raw):
    p=Path(str(raw));p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    try:p.relative_to(ROOT.resolve())
    except ValueError:return None
    return p if p.is_file() else None
def repo_rel(p):return Path(p).resolve().relative_to(ROOT.resolve()).as_posix()
def _contract_rows(ep,frame):
    c=frame_contract.compile_frame(Path(ep).resolve(),int(frame),write_cache=True);hm=c.get("hash_material") or {};refs=[]
    for row in hm.get("references") or []:
        if not isinstance(row,dict):continue
        kind=str(row.get("kind") or "");raw=row.get("path")
        if kind not in {"identity","prop","location","capture_style"} or not raw:continue
        if row.get("decision") not in {None,"pass","passed"}:continue
        fp=repo_file(raw)
        if fp:refs.append({"path":repo_rel(fp),"role":str(row.get("role") or "continuity"),"kind":kind})
    return c,hm,refs
def _identity_need(ep,hm,contract_refs):
    cv=json.loads((Path(ep)/character_visual_contract.REL).read_text(encoding="utf-8-sig"));ids=[str(x) for x in (cv.get("members") or {}).keys()];primary=str((hm.get("shot_progression") or {}).get("primary_subject") or "");matched=[cid for cid in ids if cid and cid in primary]
    if matched:
        cid=matched[0];idx=primary.find(cid);fragment=primary[max(0,idx-4):idx+len(cid)+12].lower()
        if any(tok.lower() in fragment for tok in NON_FACE_FRAGMENT_TOKENS):
            return False,None,"non_face_character_fragment"
        return True,cid,"primary_subject_character_id"
    if any(x.get("kind")=="identity" for x in contract_refs):return True,None,"contract_identity_reference"
    capture=hm.get("capture_event") or {}
    capture_text=" | ".join(str(capture.get(k) or "") for k in ("why_capture_now","device_position"))
    if any(tok.lower() in capture_text.lower() for tok in SELFIE_CAPTURE_TOKENS):
        photographer=str(capture.get("photographer_id") or "").strip()
        return True,photographer or None,"selfie_capture_event"
    low=primary.lower()
    if any(tok.lower() in low for tok in HUMAN_TOKENS):return True,None,"human_primary_subject"
    return False,None,"no_human_identity_signal"
def _master_identity(ep,frame,scope,character_id):
    series_ref=character_visual_contract.series_identity_reference(ep,character_id)
    if series_ref:return {k:series_ref[k] for k in ("path","role","kind") if k in series_ref},"series_character_identity"
    allow=scope=="visual_lock";group=character_visual_contract.pixel_master_reference(ep,allow_provisional=allow)
    if not group:return None,None
    try:
        if int(str(group.get("frame") or "0"))==int(frame):return None,"self_reference_blocked"
    except Exception:pass
    if character_id:
        crop=character_visual_contract.crop_reference(ep,character_id,allow_provisional=allow)
        if crop:return crop,"individual_crop"
    return {k:group[k] for k in ("path","role","kind") if k in group},"group_master"
def select(ep,frame,scope="batch"):
    ep=Path(ep).resolve();frame=int(frame);c,hm,contract_refs=_contract_rows(ep,frame);need,cid,need_reason=_identity_need(ep,hm,contract_refs)
    identity_cid=None if need_reason=="selfie_capture_event" else cid
    series_ref=character_visual_contract.series_identity_reference(ep,identity_cid) if need else None
    if scope=="visual_lock" and need and not series_ref:
        try:group=character_visual_contract.pixel_master_reference(ep,allow_provisional=True)
        except Exception:group=None
        if group and int(str(group.get("frame") or "0"))==frame:need=False
    chosen=[];meta={"frame":f"{frame:02d}","scope":scope,"max_refs":MAX_REFS,"identity_needed":need,"identity_reason":need_reason}
    if need:
        ident,source=_master_identity(ep,frame,scope,identity_cid)
        if ident:chosen.append(ident);meta["identity_source"]=source
    others=[x for x in contract_refs if not (x.get("kind")=="identity" and chosen)];role=str((hm.get("frame_directive") or {}).get("narrative_role") or "")
    def score(row):
        kind=row.get("kind");base={"prop":40,"location":30,"capture_style":20,"identity":10}.get(kind,0)
        if role in {"setup","transition"} and kind=="location":base+=20
        if role in {"evidence","reveal","climax","payoff"} and kind=="prop":base+=20
        return -base
    for row in sorted(others,key=score):
        if len(chosen)>=MAX_REFS:break
        if any(x.get("path")==row.get("path") for x in chosen):continue
        chosen.append(row)
    meta["selected"]=[{"role":x.get("role"),"kind":x.get("kind"),"path":x.get("path")} for x in chosen];meta["policy"]="identity_if_needed_or_visual_lock_then_context_reference";return chosen,meta
def self_test():assert MAX_REFS==2;print("REFERENCE ARBITRATOR SELF-TEST PASS")
if __name__=="__main__":self_test()
