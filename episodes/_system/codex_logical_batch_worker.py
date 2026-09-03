#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import json
import time
from pathlib import Path

import codex_subscription_batch_runtime as batch_cfg
import image_worker_pool
import runtime_trace

REL=Path("meta/codex-subscription-batch-capability.json")

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def _read(ep:Path)->dict:
    p=ep/REL
    if not p.is_file():
        return {}
    try:
        data=json.loads(p.read_text(encoding="utf-8-sig"))
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}

def _write(ep:Path,data:dict)->None:
    p=ep/REL
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def current_concurrency(ep:Path)->int:
    evidence=_read(ep)
    raw=evidence.get("recommended_concurrency")
    if isinstance(raw,int) and raw>=1:
        return min(raw,batch_cfg.max_inflight())
    return batch_cfg.max_inflight()

def _next_concurrency(current:int,successes:int,failures:int)->int:
    steps=batch_cfg.adaptive_steps()
    if current not in steps:
        current=min(steps,key=lambda x:abs(x-current))
    idx=steps.index(current)
    total=max(1,successes+failures)
    ratio=failures/total
    if ratio>=0.4 and idx<len(steps)-1:
        return steps[idx+1]
    if failures==0 and idx>0:
        return steps[idx-1]
    return current

def _round_items(items:list[dict],round_index:int)->list[dict]:
    # Technical retries get a different candidate filename without becoming a new content repair.
    rows=[]
    for item in items:
        clone=dict(item)
        clone["attempts"]=max(1,int(item.get("attempts") or 1))+round_index
        # Generation fan-out must not launch rolling Scout while the original 5-frame
        # batch is still in flight. Batch Scheduler performs review after the barrier.
        clone["_defer_scout"]=True
        rows.append(clone)
    return rows

def _run_round(ep:Path,items:list[dict],concurrency:int,timeout:int,codex:str|None,round_index:int)->tuple[dict,dict,list[str]]:
    successes={}
    failures={}
    order=[]
    work=_round_items(items,round_index)
    originals={x["id"]:x for x in items}
    with cf.ThreadPoolExecutor(
        max_workers=max(1,min(concurrency,len(work))),
        thread_name_prefix="story-os-codex-image",
    ) as pool:
        futures={
            pool.submit(image_worker_pool.execute,ep,item,timeout,codex):item
            for item in work
        }
        for fut in cf.as_completed(futures):
            item=futures[fut]
            frame=f"{int(item['frame']):02d}"
            try:
                result=fut.result()
            except Exception as exc:
                result={"returncode":99,"stdout":str(exc),"output":None,"payload":None}
            ok=(
                int(result.get("returncode") or 0)==0
                and result.get("output")
                and Path(result["output"]).is_file()
            )
            order.append(frame)
            if ok:
                successes[item["id"]]=result
            else:
                failures[item["id"]]={
                    "item":originals[item["id"]],
                    "frame":frame,
                    "error":str(result.get("stdout") or "CODEX_LOGICAL_BATCH_FRAME_FAILED")[-2000:],
                    "result":result,
                }
    return successes,failures,order

def execute(ep:Path,contract:dict,items:list[dict],timeout:int,codex:str|None)->dict:
    expected=int(contract["planned_count"])
    if expected!=len(items):
        raise ValueError("logical batch item count mismatch")

    initial=max(1,min(current_concurrency(ep),expected))
    steps=batch_cfg.adaptive_steps()
    if initial not in steps:
        initial=min(steps,key=lambda x:abs(x-initial))
    start_index=steps.index(initial)
    retry_steps=steps[start_index:]

    span=runtime_trace.start_span(
        ep,f"codex.logical_batch.{contract['batch_id']}",
        category="codex_subscription_batch",
        attrs={
            "batch_id":contract["batch_id"],
            "planned_count":expected,
            "initial_inflight_codex_images":initial,
            "native_multi_image":False,
            "logical_batch":True,
        })
    started=time.monotonic()
    successes={}
    pending=list(items)
    rounds=[]
    completion_order=[]
    first_round_failures=0

    for round_index,concurrency in enumerate(retry_steps):
        if not pending:
            break
        round_success,round_failures,order=_run_round(
            ep,pending,concurrency,timeout,codex,round_index)
        if round_index==0:
            first_round_failures=len(round_failures)
        successes.update(round_success)
        completion_order.extend([f"{x}@{concurrency}" for x in order])
        rounds.append({
            "round":round_index+1,
            "concurrency":concurrency,
            "requested":len(pending),
            "succeeded":len(round_success),
            "failed":len(round_failures),
        })
        pending=[row["item"] for row in round_failures.values()]

    final_failures={}
    if pending:
        # The final round at concurrency=1 has already been attempted. Preserve only the final failures.
        ids={x["id"] for x in pending}
        # Reconstruct compact failure evidence from the last round if available.
        for item in pending:
            final_failures[item["id"]]={
                "frame":f"{int(item['frame']):02d}",
                "error":"CODEX_LOGICAL_BATCH_TECHNICAL_RETRIES_EXHAUSTED",
            }

    elapsed=round(time.monotonic()-started,2)
    if final_failures:
        recommended=1
    elif first_round_failures:
        recommended=rounds[-1]["concurrency"]
    else:
        recommended=_next_concurrency(initial,expected,0)

    evidence={
        "schema_version":1,
        "recorded_at":now(),
        "provider":"codex_subscription",
        "transport":"codex_subscription_parallel_fanout",
        "logical_batch":True,
        "native_multi_image":False,
        "single_http_request":False,
        "api_key_required":False,
        "requested_count":expected,
        "successful_count":len(successes),
        "failed_count":len(final_failures),
        "initial_max_inflight":initial,
        "recommended_concurrency":recommended,
        "adaptive_steps":steps,
        "rounds":rounds,
        "completion_order":completion_order,
        "technical_retry_consumes_content_repair":False,
        "partial_success_preserved":True,
        "elapsed_seconds":elapsed,
        "evidence_not_authority":True,
    }
    _write(ep,evidence)
    status="PASS" if not final_failures else ("PARTIAL" if successes else "FAILED")
    runtime_trace.end_span(
        ep,span,name=f"codex.logical_batch.{contract['batch_id']}",
        category="codex_subscription_batch",status=status,
        started_monotonic=started,
        attrs={
            "successful_count":len(successes),
            "failed_count":len(final_failures),
            "initial_max_inflight":initial,
            "recommended_concurrency":recommended,
            "round_count":len(rounds),
        })
    return {
        "ok":len(final_failures)==0,
        "partial_success":bool(successes and final_failures),
        "logical_batch":True,
        "provider":"codex_subscription",
        "transport":"codex_subscription_parallel_fanout",
        "native_multi_image":False,
        "single_http_request":False,
        "requested_count":expected,
        "returned_count":len(successes),
        "results":successes,
        "failures":final_failures,
        "elapsed_seconds":elapsed,
        "logical_batch_evidence":evidence,
    }

def self_test():
    assert batch_cfg.batch_size()==5
    assert batch_cfg.max_inflight()==5
    assert _next_concurrency(5,3,2)==3
    assert _next_concurrency(3,3,0)==5
    assert _next_concurrency(1,1,0)==3
    assert [x["attempts"] for x in _round_items([{"id":"x","attempts":1}],2)]==[3]
    print("CODEX LOGICAL BATCH WORKER V2.4.2 SELF-TEST PASS")

if __name__=="__main__":
    self_test()
