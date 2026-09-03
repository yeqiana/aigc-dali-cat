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
    return data

def enabled()->bool:
    return bool(load().get("enabled"))

def images_per_batch()->int:
    n=int(load().get("images_per_batch") or 5)
    if n<2 or n>10: raise ValueError("images_per_batch must be 2..10")
    return n

def max_inflight_batches()->int:
    n=int(load().get("max_inflight_batches") or 1)
    if n<1 or n>2: raise ValueError("max_inflight_batches must be 1..2")
    return n

def probe_initial_inflight()->int:
    return max(1,min(max_inflight_batches(),int(load().get("initial_inflight_until_probe") or 1)))

def repair_thresholds()->tuple[int,int]:
    gate=load().get("repair_gate") or {}
    return int(gate.get("deviation_high_min") or 80),int(gate.get("criticality_high_min") or 80)

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
