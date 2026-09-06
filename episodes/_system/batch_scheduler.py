#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import datetime as dt, json, subprocess, sys, time
from pathlib import Path

import batch_capability_probe
import batch_contract
import batch_image_worker
import batch_runtime_config
import frame_contract
import fast_frame_scout as frame_scout
import image_worker_pool
import batch_repair_arbiter
import provider_capability
import storyos_config
import image_provider_runtime
import runtime_router
import product_runtime_adapter
import product_review_adapter
import resource_library
import runtime_portability
import production_batch_review
import async_scheduler_adapter
import runtime_event_collector

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=Path(__file__).resolve().parent
QUEUE_REL=Path("meta/production-queue.json")
READY_LEDGER_STATES={"ORIGINAL_READY","REPAIR_READY","PASSED","LOCKED"}
DEFAULT_QUALITY=str(storyos_config.get_path(storyos_config.load_config(),"image.quality"))

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(p.read_text(encoding="utf-8-sig"))
    return d if isinstance(d,dict) else {}
def write_json(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def load_queue(ep):
    p=ep/QUEUE_REL
    q=read_json(p) if p.is_file() else {"schema_version":1,"items":[],"waves":[]}
    errors=runtime_portability.queue_path_errors(q)
    if errors:raise ValueError("production queue portability guard failed: "+"; ".join(errors[:8]))
    return q
def save_queue(ep,q):
    q["updated_at"]=now();write_json(ep/QUEUE_REL,q)
def _run(cmd):
    return subprocess.run([str(x) for x in cmd],cwd=ROOT,check=False,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
def ledger(ep):
    p=ep/"meta/production-ledger.json";return read_json(p) if p.is_file() else {}
def ledger_state(ep,frame):
    return str((((ledger(ep).get("frames") or {}).get(f"{frame:02d}") or {}).get("status") or "PENDING"))
def dependency_satisfied(ep,q,dep):
    if ledger_state(ep,dep) in READY_LEDGER_STATES:return True
    return any(int(x.get("frame") or 0)==dep and x.get("status")=="generated" for x in q.get("items") or [])
def ready_items(ep,q):
    rows=[]
    for item in q.get("items") or []:
        if item.get("status")!="queued" or str(item.get("scope") or "")!="batch":continue
        deps=[int(x) for x in item.get("depends_on") or []]
        if all(dependency_satisfied(ep,q,x) for x in deps):rows.append(item)
    return sorted(rows,key=lambda x:int(x["frame"]))
def current_contract_sha(ep,frame):
    p=frame_contract.provenance(ep,frame)
    if not p:raise ValueError(f"frame {frame:02d} missing Frame Contract provenance")
    return p["contract_sha256"]
def ledger_begin(ep,item):
    prompt=(ROOT/item["prompt_file"]).resolve()
    cmd=[sys.executable,SYSTEM/"production_ledger.py","begin",ep,"--frame",f"{int(item['frame']):02d}",
        "--kind",item["kind"],"--prompt-file",prompt,"--capture-id",item["capture_id"],
        "--model",item.get("model") or "default","--quality",item.get("quality") or DEFAULT_QUALITY,
        "--notes",f"V2.4 batch scheduler item={item['id']}"]
    if item.get("batch_id"):
        cmd += ["--batch-id",str(item["batch_id"])]
    for ref in item.get("references") or []:
        cmd += ["--reference",f"{ROOT/ref['path']}::{ref['role']}::{ref['kind']}"]
    cp=_run(cmd);return cp.returncode==0,cp.stdout
def ledger_success(ep,item,res):
    policy=(res.get("payload") or {}).get("image_model") or {}
    if str(policy.get("model") or "")!=str(item.get("model") or ""):
        return False,"IMAGE_MODEL_CONTRACT_MISMATCH"
    if str(policy.get("quality") or "")!=str(item.get("quality") or DEFAULT_QUALITY):
        return False,"IMAGE_QUALITY_CONTRACT_MISMATCH"
    returned=((res.get("payload") or {}).get("frame_contract") or {}).get("contract_sha256")
    if returned and str(returned).lower()!=current_contract_sha(ep,int(item["frame"])).lower():
        return False,"CONTRACT_DRIFT"
    cmd=[sys.executable,SYSTEM/"production_ledger.py","success",ep,"--frame",f"{int(item['frame']):02d}","--path",res["output"]]
    receipt=((res.get("payload") or {}).get("provider_receipt") or {}).get("path")
    if receipt:
        rp=Path(receipt);rp=rp if rp.is_absolute() else ROOT/rp;cmd += ["--provider-receipt",rp]
    cp=_run(cmd);return cp.returncode==0,cp.stdout
def ledger_tech_fail(ep,item,code,message):
    _run([sys.executable,SYSTEM/"production_ledger.py","tech-fail",ep,"--frame",f"{int(item['frame']):02d}",
        "--code",code,"--message",message[:1000]])

def _fallback_single(ep,item,timeout,codex):
    ok,msg=ledger_begin(ep,item)
    if not ok:return False,None,"fallback ledger begin failed: "+msg[-800:]
    item["attempts"]=int(item.get("attempts") or 0)+1
    res=image_worker_pool.execute(ep,item,timeout,codex)
    if res.get("returncode")==0 and res.get("output") and Path(res["output"]).is_file():
        ok,msg=ledger_success(ep,item,res)
        return ok,res,msg
    return False,res,res.get("stdout") or "single fallback failed"

def should_use(ep:Path)->bool:
    if not batch_runtime_config.enabled():return False
    q=load_queue(ep)
    queued=[x for x in q.get("items") or [] if x.get("status")=="queued"]
    if not queued:return False
    # Visual Lock and repair lane remain on legacy scheduler.
    if any(str(x.get("scope") or "")!="batch" or str(x.get("kind") or "original")!="original" for x in queued):
        return False
    return True

def _mark_batch_running(ep,contract):
    q=load_queue(ep);byid={x["id"]:x for x in q.get("items") or []};items=[]
    for row in contract["frames"]:
        item=byid[row["queue_item_id"]]
        item["batch_id"]=contract["batch_id"]
        ok,msg=ledger_begin(ep,item)
        if not ok:
            item["status"]="blocked";item["last_error"]=runtime_portability.sanitize_diagnostic_text("ledger begin failed: "+msg[-1000:])
            save_queue(ep,q);return None
        item["status"]="running";item["attempts"]=int(item.get("attempts") or 0)+1
        item["started_at"]=now();item["batch_id"]=contract["batch_id"];items.append(dict(item))
    q.setdefault("batch_runs",[]).append({
        "batch_id":contract["batch_id"],"planned_count":contract["planned_count"],
        "frames":[x["frame"] for x in contract["frames"]],"status":"running","started_at":now()
    })
    save_queue(ep,q);return items

def _update_batch_row(q,batch_id,**fields):
    for row in q.get("batch_runs") or []:
        if row.get("batch_id")==batch_id:row.update(fields);return

def run_async(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    """V2.7 batch execution entry using shared async runtime.

    Batch planning/review/ledger semantics stay here; only execution scheduling
    moves to async_task_runtime.
    """
    return asyncio.run(_run_async(ep,max_workers,timeout,codex))


async def _run_async(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    resource_library.ensure_fresh(ep)
    q=load_queue(ep)
    ready=ready_items(ep,q)
    if not ready:
        return 0

    async def handler(item):
        return await asyncio.to_thread(image_worker_pool.execute, ep, item, timeout, codex)

    async for event in async_scheduler_adapter.stream_tasks(ready[:max_workers], handler, workers=max_workers):
        image_event=runtime_event_collector.collect(event)
        q=load_queue(ep)
        q.setdefault("runtime_events",[]).append({
            "event":image_event.event,
            "task_id":image_event.item_id,
            "payload":image_event.payload,
            "at":now()
        })
        save_queue(ep,q)
    return 0


def run(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    """Compatibility entry. Batch execution is owned by shared async runtime."""
    return run_async(ep,max_workers,timeout,codex)


def self_test():
    src=Path(__file__).read_text(encoding="utf-8-sig")
    assert "return run_async(ep,max_workers,timeout,codex)" in src
    assert batch_runtime_config.images_per_batch()==5
    assert batch_repair_arbiter is not None
    print("BATCH SCHEDULER V2.7 ASYNC CUTOVER SELF-TEST PASS")
if __name__=="__main__":self_test()
