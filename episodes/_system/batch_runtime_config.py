#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import storyos_config

ROOT=Path(__file__).resolve().parents[2]
_CONFIG=storyos_config.load_config()

def load()->dict:
    rel=storyos_config.get_path(_CONFIG,"agent_runtime.batch.config")
    if not isinstance(rel,str) or not rel.strip():
        raise ValueError("agent_runtime.batch.config missing")
    p=ROOT/rel
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict): raise ValueError("batch config root must be object")
    gate=data.get("repair_gate") or {}
    for key,expected in {"requires_both_high":True,"non_high_high_action_before_batch_complete":"WAIT_BATCH",
        "automatic_whole_batch_content_regeneration":False,"max_inflight_single_repairs":1}.items():
        if gate.get(key)!=expected: raise ValueError(f"unsupported repair policy: {key} must be {expected!r}")
    technical=data.get("technical_failure") or {}
    for key,expected in {"consumes_content_repair":False,"batch_retry_limit":0,"fallback_to_single_frame":True}.items():
        if technical.get(key)!=expected: raise ValueError(f"unsupported technical policy: {key} must be {expected!r}")
    return data

def enabled()->bool:
    return bool(load().get("enabled"))

def integer(data:dict,key:str,minimum:int,maximum:int)->int:
    value=data.get(key)
    if type(value) is not int or not minimum<=value<=maximum:
        raise ValueError(f"{key} must be an integer in {minimum}..{maximum}; got {value!r}")
    return value

def images_per_batch()->int:
    return integer(load(),"images_per_batch",2,10)

def max_inflight_batches()->int:
    return integer(load(),"max_inflight_batches",1,2)

def probe_initial_inflight()->int:
    return integer(load(),"initial_inflight_until_probe",1,max_inflight_batches())

def repair_thresholds()->tuple[int,int]:
    gate=load().get("repair_gate")
    if not isinstance(gate,dict): raise ValueError("repair_gate must be object")
    return integer(gate,"deviation_high_min",0,100),integer(gate,"criticality_high_min",0,100)

def self_test():
    cfg=load()
    assert cfg["visual_lock_batch_enabled"] is False
    assert images_per_batch() == 5
    assert cfg["provider_probe"]["single_image_generation_call_required"] is True
    assert repair_thresholds() == (80,80)
    print("BATCH RUNTIME CONFIG SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",choices=["show","self-test"]); a=ap.parse_args()
    if a.command=="self-test": self_test(); return 0
    print(json.dumps(load(),ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
