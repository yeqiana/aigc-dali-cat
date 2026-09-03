#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
import image_provider_runtime

REL=Path("meta/batch-provider-capability.json")

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read(ep:Path)->dict:
    p=ep/REL
    if not p.is_file(): return {}
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    return data if isinstance(data,dict) else {}

def record(
    ep:Path,*,supported:bool,requested:int,returned:int,reason:str,batch_id:str|None=None,
    provider:str|None=None,transport:str|None=None,runtime_succeeded:bool|None=None,
    native_multi_image:bool|None=None,single_http_request:bool|None=None,
    provider_evidence:dict|None=None,
)->dict:
    snapshot=image_provider_runtime.capability_snapshot()
    data={
        "schema_version":2,
        "recorded_at":now(),
        "provider":provider,
        "transport":transport,
        "requested_images":int(requested),
        "returned_images":int(returned),
        "runtime_succeeded":bool(runtime_succeeded) if runtime_succeeded is not None else bool(returned==requested),
        "native_multi_image_supported":bool(supported),
        "native_multi_image":bool(native_multi_image),
        "single_http_request":bool(single_http_request),
        "deterministic_output_count":bool(int(requested)==int(returned)),
        "mapping_requires_per_frame_review":True,
        "batch_id":batch_id,
        "reason":reason,
        "provider_runtime_snapshot":snapshot,
        "provider_evidence":provider_evidence or {},
        "evidence_not_authority":True,
        "secrets_persisted":False,
    }
    p=ep/REL;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data

def supported(ep:Path)->bool|None:
    data=read(ep)
    if not data:return None
    if "native_multi_image_supported" in data:
        return bool(data.get("native_multi_image_supported"))
    return data.get("supported")

def self_test():
    assert REL.as_posix()=="meta/batch-provider-capability.json"
    print("BATCH CAPABILITY PROBE V2.4.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("show");p.add_argument("episode_dir",type=Path)
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    print(json.dumps(read(a.episode_dir.resolve()),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
