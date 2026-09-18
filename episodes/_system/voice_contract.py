#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Narrator Voice Contract + semantic subtitle review evidence.

The Voice Contract is Story authority for how the narrator speaks and what they
can know. Subtitle files remain final copy; they do not redefine the narrator.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import evidence_time
import story_json
import character_contract
import episode_contract_persistence

REL=Path("meta/voice-contract.json")
CONTRACT_TYPE="VOICE"
REVIEW_REL=Path("meta/subtitle-voice-review.json")
REQUIRED=("person","role","education_and_knowledge_boundary","recording_reason",
          "knows_now","does_not_know","stress_language","fear_language_change")
REVIEW_TESTS=("continuous_three_frame_test","read_aloud_test","delete_subtitle_test",
              "knowledge_boundary_test","clue_payoff_test")

def read_json(p:Path)->dict:
    return story_json.read_json(p)
def write_json(p:Path,d:dict):
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
def sha_file(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(ep:Path, force=False)->dict:
    ep=Path(ep).resolve()
    existing=load(ep)
    if isinstance(existing,dict) and not force:return existing
    cp=character_contract.load(ep) or {}
    pov=((cp.get("pov") or {}).get("character_id") or "P01")
    members=((cp.get("cast") or {}).get("members") or [])
    member=next((x for x in members if str(x.get("id"))==str(pov)), members[0] if members else {})
    data={
      "schema_version":1,"status":"DRAFT","authority":"Story Build Voice Contract",
      "voice_card":{
        "person":str(pov),
        "role":"普通年轻人/当事人",
        "age":member.get("age"),
        "education_and_knowledge_boundary":"",
        "recording_reason":"",
        "knows_now":"",
        "does_not_know":"",
        "stress_language":"",
        "fear_language_change":"",
        "ordinary_vocabulary":"",
        "forbidden_technical_terms":""
      },
      "subtitle_policy":{
        "max_visible_chars":48,
        "continuous_three_frame_test":True,
        "read_aloud_test":True,
        "delete_subtitle_test":True,
        "do_not_repeat_visible_anomaly":True,
        "allow_short_fragments_and_self_correction":True
      }
    }
    return save(ep,data)

def validate(ep:Path, require_locked=True)->list[str]:
    ep=Path(ep).resolve();d=load(ep)
    if not isinstance(d,dict): return ["meta/voice-contract.json missing"]
    errors=[]
    if d.get("schema_version")!=1: errors.append("voice contract schema_version must be 1")
    if require_locked and d.get("status")!="LOCKED": errors.append("voice contract status must be LOCKED")
    card=d.get("voice_card") or {}
    for k in REQUIRED:
        if not str(card.get(k) or "").strip(): errors.append(f"voice_card.{k} missing")
    policy=d.get("subtitle_policy") or {}
    if policy.get("continuous_three_frame_test") is not True: errors.append("continuous_three_frame_test must be true")
    if int(policy.get("max_visible_chars") or 0)!=48: errors.append("subtitle max_visible_chars must be 48")
    return errors

def validate_release_review(ep:Path)->list[str]:
    ep=Path(ep).resolve(); errors=validate(ep,True)
    p=ep/REVIEW_REL
    if not p.is_file(): return errors+["meta/subtitle-voice-review.json missing"]
    r=read_json(p)
    if r.get("schema_version")!=1: errors.append("subtitle voice review schema_version must be 1")
    errors.extend(evidence_time.validate_timestamp(
        r.get("reviewed_at"), field="subtitle_voice_review.reviewed_at", required=True))
    expected=authority_sha256(ep) or ""
    if str(r.get("voice_contract_sha256") or "").lower()!=expected.lower():
        errors.append("subtitle voice review voice_contract_sha256 stale")
    for k in REVIEW_TESTS:
        if str(r.get(k) or "").upper()!="PASS": errors.append(f"{k} must PASS")
    ta=ep/"meta/text-audit.json"
    if not ta.is_file(): errors.append("meta/text-audit.json missing")
    else:
        t=read_json(ta)
        if not ((t.get("summary") or {}).get("passed") is True):
            errors.append("text-audit hard errors must be zero")
        expected_caption=str(t.get("source_sha256") or "")
        if expected_caption and str(r.get("caption_source_sha256") or "").lower()!=expected_caption.lower():
            errors.append("subtitle voice review caption_source_sha256 stale")
    return errors

def self_test():
    assert len(REQUIRED)==8 and len(REVIEW_TESTS)==5
    print("VOICE CONTRACT SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("validate");p.add_argument("episode_dir");p.add_argument("--allow-draft",action="store_true")
    p=sub.add_parser("validate-release");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare": print(json.dumps(prepare(ep,a.force),ensure_ascii=False,indent=2)); return 0
    if a.cmd=="validate":
        e=validate(ep,not a.allow_draft)
    elif a.cmd=="validate-release":
        e=validate_release_review(ep)
    else:
        print(json.dumps(load(ep) or {},ensure_ascii=False,indent=2)); return 0
    if e:
        [print("FAIL:",x) for x in e]; return 2
    print("VOICE CONTRACT VERIFIED"); return 0
if __name__=="__main__": raise SystemExit(main())
