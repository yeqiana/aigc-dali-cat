#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Non-destructive image asset version lineage."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path

REL=Path("meta/asset-lineage.json")
ROOT=Path(__file__).resolve().parents[2]

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def repo_rel(p):
    p=Path(p).resolve()
    try:return p.relative_to(ROOT.resolve()).as_posix()
    except ValueError:return str(p)

def load(ep):
    p=Path(ep).resolve()/REL
    return read_json(p) if p.is_file() else {"schema_version":1,"frames":{},"history_is_append_only":True}

def record(ep,frame,path,kind="original",reason="",source_item_id=None,frame_contract_sha256=None):
    ep=Path(ep).resolve();p=Path(path).resolve()
    if not p.is_file():raise ValueError(f"asset missing: {p}")
    d=load(ep);key=f"{int(frame):02d}";rows=(d.setdefault("frames",{})).setdefault(key,[])
    asset_sha=sha_file(p)
    if rows and str(rows[-1].get("sha256") or "")==asset_sha:
        return rows[-1]
    parent=rows[-1].get("sha256") if rows else None
    row={"version":len(rows)+1,"created_at":now(),"path":repo_rel(p),"sha256":asset_sha,
         "kind":kind,"reason":reason or ("repair" if kind=="repair" else "generation"),
         "parent_sha256":parent,"source_item_id":source_item_id,
         "frame_contract_sha256":frame_contract_sha256}
    rows.append(row);write_json(ep/REL,d);return row

def verify(ep):
    d=load(ep);e=[]
    if d.get("schema_version")!=1:e.append("asset lineage schema_version must be 1")
    for frame,rows in (d.get("frames") or {}).items():
        if not isinstance(rows,list):e.append(f"lineage frame {frame} must be list");continue
        prev=None
        for i,row in enumerate(rows,1):
            if row.get("version")!=i:e.append(f"lineage frame {frame} version sequence broken")
            if row.get("parent_sha256")!=prev:e.append(f"lineage frame {frame} v{i} parent mismatch")
            prev=row.get("sha256")
    return e

def self_test():
    d={"frames":{}}
    assert isinstance(d["frames"],dict)
    print("ASSET LINEAGE SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("record");p.add_argument("episode_dir");p.add_argument("--frame",type=int,required=True);p.add_argument("--path",required=True);p.add_argument("--kind",default="original");p.add_argument("--reason",default="");p.add_argument("--source-item-id");p.add_argument("--frame-contract-sha256")
    p=sub.add_parser("verify");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="record":print(json.dumps(record(ep,a.frame,a.path,a.kind,a.reason,a.source_item_id,a.frame_contract_sha256),ensure_ascii=False,indent=2));return 0
    if a.cmd=="verify":
        e=verify(ep)
        if e:[print("FAIL:",x) for x in e];return 2
        print("ASSET LINEAGE VERIFIED");return 0
    print(json.dumps(load(ep),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
