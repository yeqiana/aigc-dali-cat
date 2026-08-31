#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve/register shared Story OS resources without reusing final episode images."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import multi_level_cache as cache

ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/"library"
CATALOG=LIB/"catalog.json"
REL=Path("meta/resource-selection.json")

def read_json(p): return cache.read_json(p)
def write_json(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def file_sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def tags_for_episode(ep):
    tags=set()
    cp=ep/"meta/character-contract.json"
    if cp.is_file():
        d=read_json(cp); era=d.get("era") or {}; entry=d.get("entry") or {}; scene=d.get("scene") or {}
        for x in (era.get("bucket"),entry.get("type"),scene.get("primary_category"),scene.get("primary_place")):
            if x:tags.add(str(x))
        cast=d.get("cast") or {}
        if int(cast.get("size") or 0)>=4:tags.add("friend_group")
    sg=ep/"meta/story-gates.json"
    if sg.is_file():
        d=read_json(sg); raw=json.dumps(((d.get("visual") or {}).get("environment_contract") or {}),ensure_ascii=False)
        for key in ("炎热","夏天","下雨","雨天","雪","雾","夜"):
            if key in raw:tags.add(key)
    return tags
def resolve(ep,write=True):
    ep=Path(ep).resolve(); cat=read_json(CATALOG); tags=tags_for_episode(ep)
    source={"catalog_sha":file_sha(CATALOG),"tags":sorted(tags)}
    key=cache.sha_json(source)
    hit=cache.get("resource_selection",key)
    if hit and isinstance(hit,dict) and "data" in hit:
        data=hit["data"];data["cache_hit"]=True
    else:
        scored=[]
        for row in cat.get("resources") or []:
            rtags=set(str(x) for x in row.get("tags") or [])
            score=len(tags & rtags)
            if score:
                scored.append((score,float(row.get("quality_score") or 0),row))
        scored.sort(key=lambda x:(-x[0],-x[1],x[2].get("id","")))
        selected=[]
        seen_types=set()
        for score,q,row in scored:
            typ=row.get("type")
            if typ in seen_types:continue
            copy=dict(row);copy["match_score"]=score;selected.append(copy);seen_types.add(typ)
            if len(selected)>=8:break
        data={"schema_version":1,"source_tags":sorted(tags),"selected":selected,"policy":{"reference_only":True,"reuse_final_episode_images":False},"cache_hit":False}
        cache.put("resource_selection",key,data,meta=source)
    if write:write_json(ep/REL,data)
    return data
def register(resource_id,typ,path,tags,quality):
    p=(ROOT/path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    try: rel=p.relative_to(ROOT).as_posix()
    except ValueError: raise ValueError("resource path must be inside repository")
    if not p.is_file():raise ValueError(f"resource missing: {p}")
    cat=read_json(CATALOG); rows=cat.setdefault("resources",[])
    if any(x.get("id")==resource_id for x in rows):raise ValueError(f"duplicate resource id: {resource_id}")
    rows.append({"id":resource_id,"type":typ,"path":rel,"tags":tags,"reuse_scope":"reference_only","quality_score":float(quality),"sha256":file_sha(p)})
    write_json(CATALOG,cat);return rows[-1]
def self_test():
    c=read_json(CATALOG);assert c["policy"]["reuse_final_episode_images"] is False
    print("RESOURCE LIBRARY SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("resolve");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    p=sub.add_parser("register");p.add_argument("--id",required=True);p.add_argument("--type",required=True);p.add_argument("--path",required=True);p.add_argument("--tags",default="");p.add_argument("--quality",type=float,default=9.0)
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="register":
        print(json.dumps(register(a.id,a.type,a.path,[x.strip() for x in a.tags.split(",") if x.strip()],a.quality),ensure_ascii=False,indent=2));return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="resolve":print(json.dumps(resolve(ep,True),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
