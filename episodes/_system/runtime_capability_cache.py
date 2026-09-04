#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cheap, episode-local Runtime capability cache for Story OS V2.5.1.

This module deliberately does NOT launch expensive model probes. It remembers already
verified capabilities so context restores do not rediscover the same runtime repeatedly.
Unknown vision capability is treated as unverified; rolling review must defer to Final Review.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/runtime-capabilities.json")
CFG=ROOT/"runtimes/runtime-fast-path-v251.json"
VALID_VISION={"verified","unverified","unavailable"}

def now_dt(): return dt.datetime.now(dt.timezone.utc).astimezone()
def now(): return now_dt().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict): raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def ttl_seconds():
    try:return int(read_json(CFG).get("capability_cache_ttl_seconds") or 21600)
    except Exception:return 21600

def auto_detect(ep):
    ep=Path(ep).resolve(); codex=shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    raw=os.environ.get("STORY_OS_ROLLING_VISION_VERIFIED")
    if raw is None: vision="unverified"
    elif raw.strip().lower() in {"1","true","yes","verified"}: vision="verified"
    else: vision="unavailable"
    manual=bool(os.environ.get("STORY_OS_MANUAL_RAW_DIR"))
    data={
      "schema_version":1,"module_version":"2.5.1","generated_at":now(),"expires_after_seconds":ttl_seconds(),
      "platform":os.name,"codex_path":codex,"text_worker":"available" if codex else "unavailable",
      "vision_review":vision,
      "image_generation_route":"manual_raw_desktop" if manual else "unknown",
      "sandbox_risk":"windows_1385_possible" if os.name=="nt" else "default",
      "source":"cheap_auto_detect_no_model_probe",
      "note":"Set/record vision_review=verified only after a real pixel-vision probe succeeds."
    }
    write_json(ep/REL,data); return data

def load(ep,create=False):
    p=Path(ep).resolve()/REL
    if p.is_file():
        try:return read_json(p)
        except Exception:return None
    return auto_detect(ep) if create else None

def is_fresh(data):
    if not isinstance(data,dict): return False
    try:
        at=dt.datetime.fromisoformat(str(data.get("generated_at")))
        if at.tzinfo is None: at=at.replace(tzinfo=dt.timezone.utc)
        return (now_dt()-at).total_seconds() <= int(data.get("expires_after_seconds") or ttl_seconds())
    except Exception:return False

def ensure(ep):
    d=load(ep,False)
    return d if is_fresh(d) else auto_detect(ep)
def vision_verified(data): return isinstance(data,dict) and data.get("vision_review")=="verified"
def record(ep,*,vision=None,image_route=None,text_worker=None,sandbox_risk=None,note=None):
    ep=Path(ep).resolve(); d=ensure(ep)
    if vision is not None:
        if vision not in VALID_VISION: raise ValueError(f"vision must be one of {sorted(VALID_VISION)}")
        d["vision_review"]=vision
    if image_route is not None:d["image_generation_route"]=image_route
    if text_worker is not None:d["text_worker"]=text_worker
    if sandbox_risk is not None:d["sandbox_risk"]=sandbox_risk
    if note is not None:d["note"]=note
    d["generated_at"]=now(); d["source"]="explicit_runtime_record"
    write_json(ep/REL,d); return d
def invalidate(ep):
    p=Path(ep).resolve()/REL
    if p.exists(): p.unlink()
def self_test():
    assert not vision_verified({"vision_review":"unverified"})
    assert vision_verified({"vision_review":"verified"})
    assert ttl_seconds()>0
    print("RUNTIME CAPABILITY CACHE V2.5.1 SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("show");p.add_argument("episode_dir")
    p=sub.add_parser("ensure");p.add_argument("episode_dir")
    p=sub.add_parser("record");p.add_argument("episode_dir");p.add_argument("--vision",choices=sorted(VALID_VISION));p.add_argument("--image-route");p.add_argument("--text-worker");p.add_argument("--sandbox-risk");p.add_argument("--note")
    p=sub.add_parser("invalidate");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="invalidate":invalidate(a.episode_dir);print("INVALIDATED");return 0
    if a.cmd=="record":d=record(a.episode_dir,vision=a.vision,image_route=a.image_route,text_worker=a.text_worker,sandbox_risk=a.sandbox_risk,note=a.note)
    elif a.cmd=="ensure":d=ensure(a.episode_dir)
    else:d=load(a.episode_dir,False) or {}
    print(json.dumps(d,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
