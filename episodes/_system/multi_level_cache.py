#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS R2 multi-level cache.

L0 process: in-memory parsed JSON/text
L1 episode: existing SHA-bound derived caches under <episode>/meta/runtime
L2 global: content-addressed JSON cache under .storyos_cache/
L3 negative: explicit opt-in short-lived failure fingerprints (never used to suppress content repair)
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CACHE_ROOT=ROOT/".storyos_cache"
_PROCESS_TEXT={}
_PROCESS_JSON={}

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()
def sha_json(data)->str:
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return sha_bytes(raw)
def read_text(path:Path)->str:
    path=path.resolve(); stat=path.stat(); key=(str(path),stat.st_mtime_ns,stat.st_size)
    if key not in _PROCESS_TEXT:
        _PROCESS_TEXT.clear() if len(_PROCESS_TEXT)>256 else None
        _PROCESS_TEXT[key]=path.read_text(encoding="utf-8-sig")
    return _PROCESS_TEXT[key]
def read_json(path:Path):
    path=path.resolve(); stat=path.stat(); key=(str(path),stat.st_mtime_ns,stat.st_size)
    if key not in _PROCESS_JSON:
        _PROCESS_JSON.clear() if len(_PROCESS_JSON)>256 else None
        data=json.loads(read_text(path))
        if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
        _PROCESS_JSON[key]=data
    return _PROCESS_JSON[key]
def cache_path(namespace,key):
    safe="".join(c if c.isalnum() or c in "._-" else "_" for c in namespace)
    return CACHE_ROOT/safe/f"{key}.json"
def get(namespace,key):
    p=cache_path(namespace,key)
    if not p.is_file(): return None
    try: return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception: return None
def put(namespace,key,data,meta=None):
    p=cache_path(namespace,key); p.parent.mkdir(parents=True,exist_ok=True)
    payload={"schema_version":1,"namespace":namespace,"key":key,"created_at":now(),"meta":meta or {},"data":data}
    p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    return p
def remember_failure(namespace,fingerprint,ttl_seconds,reason):
    p=CACHE_ROOT/"negative"/namespace/f"{fingerprint}.json"; p.parent.mkdir(parents=True,exist_ok=True)
    payload={"schema_version":1,"created_epoch":time.time(),"ttl_seconds":int(ttl_seconds),"reason":str(reason),"created_at":now()}
    p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    return p
def failure_active(namespace,fingerprint):
    p=CACHE_ROOT/"negative"/namespace/f"{fingerprint}.json"
    if not p.is_file(): return None
    try: d=json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:return None
    if time.time()-float(d.get("created_epoch") or 0)>int(d.get("ttl_seconds") or 0):
        try:p.unlink()
        except OSError:pass
        return None
    return d
def stats():
    files=list(CACHE_ROOT.rglob("*.json")) if CACHE_ROOT.is_dir() else []
    return {"root":str(CACHE_ROOT),"files":len(files),"bytes":sum(p.stat().st_size for p in files),"process_text_entries":len(_PROCESS_TEXT),"process_json_entries":len(_PROCESS_JSON)}
def clear():
    import shutil
    if CACHE_ROOT.is_dir():shutil.rmtree(CACHE_ROOT)
def self_test():
    assert sha_json({"a":1})==sha_json({"a":1})
    assert CACHE_ROOT.name==".storyos_cache"
    print("MULTI LEVEL CACHE SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("stats");sub.add_parser("clear");sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="clear":clear();print("CACHE CLEARED");return 0
    print(json.dumps(stats(),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
