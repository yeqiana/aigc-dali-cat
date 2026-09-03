#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import storyos_config

ROOT=Path(__file__).resolve().parents[2]
_CFG=storyos_config.load_config()

def load()->dict:
    rel=storyos_config.get_path(_CFG,"agent_runtime.codex_subscription_batch.config")
    if not isinstance(rel,str) or not rel.strip():
        raise ValueError("agent_runtime.codex_subscription_batch.config missing")
    data=json.loads((ROOT/rel).read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict):
        raise ValueError("codex subscription batch config root must be object")
    return data

def enabled()->bool:
    return bool(load().get("enabled"))

def batch_size()->int:
    n=int(load().get("logical_batch_size") or 5)
    if n<2 or n>10:
        raise ValueError("logical_batch_size must be 2..10")
    return n

def max_inflight()->int:
    n=int(load().get("max_inflight_codex_images") or 5)
    if n<1 or n>10:
        raise ValueError("max_inflight_codex_images must be 1..10")
    return n

def adaptive_steps()->list[int]:
    raw=load().get("adaptive_concurrency_steps") or [5,3,1]
    values=[int(x) for x in raw]
    if not values or values[-1]!=1 or any(x<1 or x>10 for x in values):
        raise ValueError("adaptive_concurrency_steps invalid")
    if values!=sorted(values,reverse=True):
        raise ValueError("adaptive_concurrency_steps must be descending")
    return values

def self_test():
    assert enabled() is True
    assert batch_size()==5
    assert max_inflight()==5
    assert adaptive_steps()==[5,3,1]
    assert load()["api_key_required"] is False
    print("CODEX SUBSCRIPTION BATCH RUNTIME V2.4.2 SELF-TEST PASS")

if __name__=="__main__":
    self_test()
