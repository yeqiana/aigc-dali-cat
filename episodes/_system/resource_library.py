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
RESOLVER_VERSION=3

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

def primary_place_for_episode(ep):
    cp=ep/"meta/character-contract.json"
    if not cp.is_file():return ""
    scene=(read_json(cp).get("scene") or {})
    return str(scene.get("primary_place") or "").strip()

def _norm(value):
    return "".join(str(value or "").strip().lower().split())

def _contains_cjk(value):
    return any("\u4e00" <= ch <= "\u9fff" for ch in str(value or ""))

def location_match_score(primary_place,resource_tags):
    place=_norm(primary_place)
    if not place:return 0
    best=0
    for raw in resource_tags:
        tag=_norm(raw)
        if not tag:continue
        if tag==place:best=max(best,4);continue
        # Location fuzziness is deliberately limited to human-readable place tags.
        # Generic taxonomy tags such as village_home must never override an explicit place.
        if _contains_cjk(tag) and len(tag)>=2 and (tag in place or place in tag):
            best=max(best,3)
    return best

def selection_source(ep):
    ep=Path(ep).resolve()
    tags=tags_for_episode(ep)
    return {
        "resolver_version":RESOLVER_VERSION,
        "catalog_sha":file_sha(CATALOG),
        "tags":sorted(tags),
        "primary_place":primary_place_for_episode(ep),
    }


def is_fresh(ep):
    ep=Path(ep).resolve(); p=ep/REL
    if not p.is_file():return False
    try:data=read_json(p)
    except Exception:return False
    expected=selection_source(ep)
    return all(data.get(k)==expected[k] for k in ("resolver_version","catalog_sha","primary_place")) and data.get("source_tags")==expected["tags"]


def ensure_fresh(ep):
    ep=Path(ep).resolve()
    if not is_fresh(ep):
        resolve(ep,write=True)
    if not is_fresh(ep):
        raise ValueError("RESOURCE_SELECTION_STALE: resolver/catalog/place binding did not converge")
    return read_json(ep/REL)


def resolve(ep,write=True):
    ep=Path(ep).resolve(); cat=read_json(CATALOG); source=selection_source(ep); tags=set(source["tags"]); primary_place=source["primary_place"]
    key=cache.sha_json(source)
    hit=cache.get("resource_selection",key)
    if hit and isinstance(hit,dict) and "data" in hit:
        data=hit["data"];data["cache_hit"]=True
    else:
        scored=[]
        for row in cat.get("resources") or []:
            rtags=set(str(x) for x in row.get("tags") or [])
            score=len(tags & rtags)
            if row.get("type")=="location_descriptor" and primary_place:
                specific=location_match_score(primary_place,rtags)
                if specific<=0:
                    continue
                score += specific
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
        data={"schema_version":1,"resolver_version":RESOLVER_VERSION,"catalog_sha":source["catalog_sha"],"primary_place":primary_place,"source_tags":sorted(tags),"selected":selected,"policy":{"reference_only":True,"reuse_final_episode_images":False},"cache_hit":False}
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
    assert RESOLVER_VERSION==3
    assert location_match_score("川西山谷小镇普通民宿",{"village_home","西北农村"})==0
    assert location_match_score("废弃游乐园",{"abandoned_place","游乐园"})>0
    assert location_match_score("西北农村老家",{"village_home","西北农村"})>0
    print("RESOURCE LIBRARY V2 SPECIFIC LOCATION SELF-TEST PASS")
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
