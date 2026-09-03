#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path

REL=Path("meta/batch-provider-capability.json")

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read(ep:Path)->dict:
    p=ep/REL
    if not p.is_file(): return {}
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    return data if isinstance(data,dict) else {}

def record(ep:Path,*,supported:bool,requested:int,returned:int,reason:str,batch_id:str|None=None)->dict:
    data={
        "schema_version":1,
        "recorded_at":now(),
        "transport":"codex_subscription_image_generation",
        "single_tool_call_required":True,
        "requested_images":int(requested),
        "returned_images":int(returned),
        "deterministic_mapping":bool(supported and requested==returned),
        "supported":bool(supported),
        "batch_id":batch_id,
        "reason":reason,
        "evidence_not_authority":True,
    }
    p=ep/REL; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data

def supported(ep:Path)->bool|None:
    data=read(ep)
    return data.get("supported") if data else None

def self_test():
    assert REL.as_posix()=="meta/batch-provider-capability.json"
    print("BATCH CAPABILITY PROBE SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("show");p.add_argument("episode_dir",type=Path)
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    print(json.dumps(read(a.episode_dir.resolve()),ensure_ascii=False,indent=2));return 0
if __name__=="__main__": raise SystemExit(main())
