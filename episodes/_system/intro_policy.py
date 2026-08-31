#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve intro opener family and lightweight title policy."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import multi_level_cache as cache

ROOT=Path(__file__).resolve().parents[2]
POOL=ROOT/"library/copy/intro-openers.json"
REL=Path("meta/intro-policy.json")

def read_json(p):return cache.read_json(p)
def write_json(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def recent_families(ep):
    out=[]
    episodes=ep.parent
    for p in sorted(episodes.glob("*/meta/intro-policy.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        if p.parent.parent.resolve()==ep.resolve():continue
        try:
            d=read_json(p); fam=d.get("selected_family")
            if fam:out.append(fam)
        except Exception:pass
        if len(out)>=5:break
    return out
def resolve(ep,write=True):
    ep=Path(ep).resolve(); pool=read_json(POOL)
    cp=read_json(ep/"meta/character-contract.json") if (ep/"meta/character-contract.json").is_file() else {}
    era=(cp.get("era") or {}).get("bucket");entry=(cp.get("entry") or {}).get("type")
    recent=recent_families(ep); rows=[]
    for fam in pool["families"]:
        score=0
        best=set(fam.get("best_for") or [])
        if era in best:score+=3
        if entry in best:score+=3
        if fam["id"] in recent[:2]:score-=2
        rows.append((score,fam["id"],fam))
    rows.sort(key=lambda x:(-x[0],x[1]))
    chosen=rows[0][2]
    data={"schema_version":1,"selected_family":chosen["id"],"reference":chosen["reference"],"variants":chosen.get("variants") or [],"rule":chosen["rule"],"recent5_families":recent,"title_policy":pool["title_policy"],"final_text_must_be_natural":True,"template_is_reference_not_literal_output":True}
    if write:write_json(ep/REL,data)
    return data
def self_test():
    p=read_json(POOL);assert p["title_policy"]["required_for_publish_ready"] is False;assert len(p["families"])==4
    print("INTRO POLICY SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("resolve");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="resolve":print(json.dumps(resolve(ep,True),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
