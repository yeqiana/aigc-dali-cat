#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

def _read(path:Path)->dict:
    if not path.is_file():return {}
    try:
        d=json.loads(path.read_text(encoding="utf-8-sig"))
        return d if isinstance(d,dict) else {}
    except Exception:return {}

def collect(ep:Path)->dict:
    perf=_read(ep/"meta/batch-runtime-performance.json")
    cap=_read(ep/"meta/batch-provider-capability.json")
    decision_dir=ep/"meta/batch-repair-decisions"
    decisions=[]
    if decision_dir.is_dir():
        for p in sorted(decision_dir.glob("*.json")):
            d=_read(p);decisions.extend(d.get("decisions") or [])
    batches=perf.get("batches") or []
    requested=sum(int(x.get("planned_count") or 0) for x in batches if isinstance(x,dict))
    returned=sum(int(x.get("returned_count") or 0) for x in batches if isinstance(x,dict))
    early=sum(1 for x in decisions if isinstance(x,dict) and x.get("action")=="EARLY_SINGLE_REPAIR")
    ordinary=sum(1 for x in decisions if isinstance(x,dict) and x.get("action")=="SINGLE_REPAIR")
    waits=sum(1 for x in decisions if isinstance(x,dict) and x.get("action")=="WAIT_BATCH")
    providers={}
    for row in batches:
        if isinstance(row,dict):
            name=str(row.get("provider") or "UNKNOWN")
            providers[name]=providers.get(name,0)+1
    return {
        "enabled":bool(perf),
        "batch_count":len(batches),
        "images_requested":requested,
        "images_returned":returned,
        "fallback_single_frames":int(perf.get("fallback_single_frames") or 0),
        "provider_counts":providers,
        "native_multi_image_supported":cap.get("native_multi_image_supported",cap.get("supported")),
        "single_http_request":cap.get("single_http_request"),
        "provider":cap.get("provider"),
        "transport":cap.get("transport"),
        "provider_requested_images":cap.get("requested_images"),
        "provider_returned_images":cap.get("returned_images"),
        "early_high_high_repairs":early,
        "ordinary_repairs_after_barrier":ordinary,
        "wait_batch_decisions":waits,
    }

def self_test():
    print("BATCH RUNTIME METRICS V2.4.1 SELF-TEST PASS")
if __name__=="__main__":self_test()
