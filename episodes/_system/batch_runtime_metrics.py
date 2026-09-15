#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import runtime_observability

def _read(path:Path)->dict:
    if not path.is_file():return {}
    try:
        d=json.loads(path.read_text(encoding="utf-8-sig"))
        return d if isinstance(d,dict) else {}
    except Exception:return {}

def collect(ep:Path)->dict:
    perf=_read(ep/runtime_observability.BATCH_RUNTIME_PERFORMANCE_REL)
    cap=_read(ep/"meta/batch-provider-capability.json")
    codex=_read(ep/"meta/codex-subscription-batch-capability.json")
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
    failure_codes={}
    empty_batches=0
    timeout_failures=0
    network_connect_failures=0
    logical_batches=0
    for row in batches:
        if isinstance(row,dict):
            name=str(row.get("provider") or "UNKNOWN")
            providers[name]=providers.get(name,0)+1
            if row.get("logical_batch"):
                logical_batches+=1
            if row.get("empty_result") is True or (int(row.get("planned_count") or 0)>0 and int(row.get("returned_count") or 0)==0):
                empty_batches+=1
            timeout_failures+=int(row.get("timeout_count") or 0)
            network_connect_failures+=int(row.get("network_connect_count") or 0)
            for code,count in (row.get("failure_code_counts") or {}).items():
                failure_codes[str(code)]=failure_codes.get(str(code),0)+int(count or 0)
    return {
        "enabled":bool(perf),
        "batch_count":len(batches),
        "logical_codex_batch_count":logical_batches,
        "images_requested":requested,
        "images_returned":returned,
        "fallback_single_frames":int(perf.get("fallback_single_frames") or 0),
        "provider_counts":providers,
        "failure_code_counts":failure_codes,
        "empty_batch_count":empty_batches,
        "timeout_failure_count":timeout_failures,
        "network_connect_failure_count":network_connect_failures,
        "native_multi_image_supported":cap.get("native_multi_image_supported",cap.get("supported")),
        "single_http_request":cap.get("single_http_request"),
        "provider":cap.get("provider"),
        "transport":cap.get("transport"),
        "provider_requested_images":cap.get("requested_images"),
        "provider_returned_images":cap.get("returned_images"),
        "codex_logical_batch":{
            "enabled":bool(codex),
            "provider":codex.get("provider"),
            "transport":codex.get("transport"),
            "logical_batch":codex.get("logical_batch"),
            "native_multi_image":codex.get("native_multi_image"),
            "requested_count":codex.get("requested_count"),
            "successful_count":codex.get("successful_count"),
            "failed_count":codex.get("failed_count"),
            "initial_max_inflight":codex.get("initial_max_inflight"),
            "recommended_concurrency":codex.get("recommended_concurrency"),
            "rounds":codex.get("rounds") or [],
            "elapsed_seconds":codex.get("elapsed_seconds"),
        },
        "early_high_high_repairs":early,
        "ordinary_repairs_after_barrier":ordinary,
        "wait_batch_decisions":waits,
    }

def self_test():
    import tempfile
    with tempfile.TemporaryDirectory(prefix="storyos-metrics-") as td:
        ep=Path(td); (ep/"meta").mkdir()
        assert collect(ep)["images_requested"]==0
        (ep/runtime_observability.BATCH_RUNTIME_PERFORMANCE_REL).write_text(json.dumps({"batches":[
            {"planned_count":5,"returned_count":4,"provider":"codex_subscription","logical_batch":True,
             "failure_code_counts":{"NETWORK_CONNECT":1},"network_connect_count":1},
            {"planned_count":1,"returned_count":0,"provider":"codex_subscription","logical_batch":True,
             "failure_code_counts":{"TIMEOUT":1},"timeout_count":1,"empty_result":True},
        ]}),encoding="utf-8")
        row=collect(ep)
        assert (row["images_requested"],row["images_returned"],row["logical_codex_batch_count"])==(6,4,2)
        assert row["failure_code_counts"]=={"NETWORK_CONNECT":1,"TIMEOUT":1}
        assert row["empty_batch_count"]==1
        assert row["timeout_failure_count"]==1
        assert row["network_connect_failure_count"]==1
    print("BATCH RUNTIME METRICS V2.4.2 SELF-TEST PASS")
if __name__=="__main__":self_test()
