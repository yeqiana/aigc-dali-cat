#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import uuid
import datetime as dt, json, time
from pathlib import Path

import batch_capability_probe
import batch_contract
import batch_image_worker
import batch_runtime_config
import frame_contract
import fast_frame_scout as frame_scout
import image_worker_pool
import batch_repair_arbiter
import scheduler_core
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
import production_recovery
import production_ledger
import runtime_observability
import runtime_timeout_policy
CAPABILITY_WAIT=24

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=Path(__file__).resolve().parent
QUEUE_REL=Path("meta/production-queue.json")

READY_LEDGER_STATES=production_ledger.READY_LEDGER_STATES

# Runtime result semantics. Keep technical recovery separate from host action.
SUCCESS=0
RECOVERABLE_FAILURE=21
HUMAN_REQUIRED=22
HARD_STOP=23
DEFAULT_QUALITY=str(storyos_config.get_path(storyos_config.load_config(),"image.quality"))

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def ensure_image_capability(ep:Path, batch_id:str|None=None, requested:int=0)->bool:
    """Guard image lane before consuming worker slots.

    Capability failure is a technical wait, not a content failure. The batch
    must not start multiple workers when the image tool is unavailable.
    """
    snapshot=image_provider_runtime.capability_snapshot()
    # A configured route permits one real probe; it is never proof of capability.
    codex=snapshot.get("codex_subscription") or {}
    product=snapshot.get("product_runtime_image") or {}
    api=snapshot.get("openai_images_api") or {}
    available=bool(snapshot.get("available") or snapshot.get("image_generation")
        or (codex.get("configured") and codex.get("runtime_eligible"))
        or (product.get("configured") and product.get("runtime_eligible"))
        or (snapshot.get("image_execution_runtime")=="AUTO" and api.get("configured") and api.get("credential_available")))
    return available


def verified_image_lane(ep:Path)->bool:
    evidence=batch_capability_probe.read(ep)
    return bool(evidence.get("runtime_succeeded") and int(evidence.get("returned_images") or 0)>0
        and evidence.get("provider_runtime_snapshot")==image_provider_runtime.capability_snapshot())

def read_json(p):
    import story_json
    d=story_json.read_json(p,require_object=False)
    return d if isinstance(d,dict) else {}
def write_json(p,d):
    import story_json
    story_json.write_json(p,d)
def load_queue(ep):
    return scheduler_core.load_queue(ep)
def save_queue(ep,q):
    scheduler_core.save_queue(ep,q)
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
    return scheduler_core.current_contract_sha(ep,frame)
def ledger_begin(ep,item):
    return scheduler_core.ledger_begin(
        ep,
        item,
        notes=f"V2.4 batch scheduler item={item['id']}",
        batch_id=str(item["batch_id"]) if item.get("batch_id") else None,
    )
def ledger_success(ep,item,res):
    return scheduler_core.ledger_success(ep,item,res,default_quality=DEFAULT_QUALITY)
def ledger_tech_fail(ep,item,code,message):
    scheduler_core.ledger_tech_fail(ep,item,code,message)

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
    import runner_state_store
    lock_rel=Path("meta/runtime-image-scheduler.lock")
    if not runner_state_store.acquire_lock(ep,lock_rel=lock_rel):
        return 21
    try:
        return asyncio.run(_run_async(ep,max_workers,timeout,codex))
    finally:
        runner_state_store.release_lock(ep,lock_rel=lock_rel)


async def _run_async(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    resource_library.ensure_fresh(ep)
    q=load_queue(ep)
    production_recovery.reconcile_locked(ep,q)
    save_queue(ep,q)
    ready=ready_items(ep,q)
    if not ready:
        return SUCCESS

    # V2.7 async runtime only executes workers. Scheduler still owns the
    # queue/ledger state transition. Never leave a successful worker event as
    # trace-only data.
    max_workers = min(max(1, max_workers), int(storyos_config.get_path(storyos_config.load_config(), "production.max_inflight_images")))
    runtime,_=runtime_router.detect()
    image_runtime,_=runtime_router.image_execution_runtime()
    provider=image_provider_runtime.select_batch_provider(batch_runtime_config.images_per_batch())
    if provider["provider"]=="product_runtime_image":
        request=product_runtime_adapter.build_image_request(ep,runtime=runtime,queue_items=ready[:batch_runtime_config.images_per_batch()],source="batch_scheduler")
        product_runtime_adapter.print_request(request)
        return product_runtime_adapter.HOST_ACTION_REQUIRED_RC
    if provider["provider"]=="codex_subscription" and not verified_image_lane(ep):
        max_workers=1
    max_workers=min(max_workers,int(q.get("adaptive_parallel") or max_workers))
    batch_items = ready[:batch_runtime_config.images_per_batch()] if provider["provider"]!="codex_subscription" or verified_image_lane(ep) else ready[:1]
    if provider["provider"]=="openai_images_api":
        planned=batch_contract.build(ep,batch_items)
        planned_ids={x["queue_item_id"] for x in planned["frames"]}
        batch_items=[x for x in batch_items if x["id"] in planned_ids]
    batch_id="BATCH_"+uuid.uuid4().hex[:12]
    if not ensure_image_capability(ep, requested=len(batch_items)):
        q["image_lane"] = {"status": "CAPABILITY_WAIT", "reason": "IMAGE_TOOL_UNAVAILABLE", "at": now()}
        save_queue(ep,q)
        return CAPABILITY_WAIT
    q.pop("image_lane", None)
    q_by_id={x["id"]:x for x in q.get("items") or []}
    started=[]
    has_human_block=False
    for item in batch_items:
        row=q_by_id.get(item["id"])
        if not row:
            continue
        production_recovery.prepare_execution(ep,row)
        save_queue(ep,q)
        ok,msg=ledger_begin(ep,row)
        if not ok:
            row["status"]="blocked"
            row["last_error"]="ledger begin failed: "+msg[-500:]
            production_recovery.mark_terminal(ep,row,"BEGIN_REJECTED",reason=row["last_error"])
            has_human_block=True
            continue
        row["status"]="running"
        row["attempts"]=int(row.get("attempts") or 0)+1
        row["started_at"]=now()
        row["batch_id"]=batch_id
        row["_defer_scout"]=True
        production_recovery.mark_worker_pending(ep,row)
        started.append(row)
    save_queue(ep,q)

    native_task=None
    native_fallback_used=False
    async def handler(item):
        nonlocal native_task, native_fallback_used
        if provider["provider"]=="openai_images_api":
            if native_task is None:
                contract=batch_contract.build(ep,started)
                if contract["planned_count"]!=len(started):
                    return {"returncode":99,"error":"BATCH_CONTINUITY_MISMATCH","output":None}
                native_task=asyncio.create_task(asyncio.to_thread(batch_image_worker.execute_batch,ep,contract,started,timeout,codex))
            native=await asyncio.shield(native_task)
            if item["id"] in (native.get("results") or {}): return native["results"][item["id"]]
            if runtime=="CODEX" and batch_runtime_config.load()["technical_failure"]["fallback_to_single_frame"]:
                native_fallback_used=True
                return await asyncio.to_thread(image_worker_pool.execute,ep,item,timeout,codex)
            return {"returncode":99,"error":native.get("error") or "native batch failed","output":None}
        return await asyncio.to_thread(image_worker_pool.execute, ep, item, timeout, codex)

    has_technical_failure=False
    successful_results=0

    async def consume(event):
        nonlocal has_human_block, has_technical_failure, successful_results
        image_event=runtime_event_collector.collect(event)
        q=load_queue(ep)
        item=next((x for x in q.get("items") or [] if x.get("id")==image_event.item_id),None)
        payload=runtime_event_collector.json_safe(image_event.payload)
        if item:
            if image_event.event == "IMAGE_SUCCESS":
                result=payload.get("result") or payload
                if result.get("returncode")==0 and result.get("output") and Path(result["output"]).is_file():
                    production_recovery.mark_terminal(ep,item,"SUCCESS_PREPARED")
                    ok,msg=ledger_success(ep,item,result)
                    if ok:
                        item["status"]="generated"
                        item["completed_at"]=now()
                        item["output_path"]=Path(result["output"]).resolve().relative_to(ROOT.resolve()).as_posix()
                        item["log_path"]=Path(result["log"]).resolve().relative_to(ROOT.resolve()).as_posix() if result.get("log") else None
                        item["prompt_package"]=result.get("prompt_package")
                        item["last_error"]=None
                        successful_results+=1
                        production_recovery.mark_terminal(ep,item,"COMMITTED")
                    else:
                        # The backend already produced pixels; keep the open
                        # attempt/candidate for reconciliation, never regenerate.
                        item["status"]="blocked"
                        item["candidate_output_path"]=str(result["output"])
                        item["last_error"]="CANDIDATE_COMMIT_FAILED: "+msg
                        production_recovery.mark_terminal(ep,item,"BLOCKED",reason=item["last_error"])
                        has_human_block=True
                else:
                    err=str(result.get("stdout") or result.get("error") or "worker returned success without output")
                    from image_scheduler import classify_error, NON_REGENERATING_FAILURE_CODES
                    code=classify_error(err)
                    ledger_tech_fail(ep,item,code,err)
                    item["status"]="blocked" if code in NON_REGENERATING_FAILURE_CODES else "tech_failed"
                    if result.get("output"):
                        item["candidate_output_path"]=str(result["output"])
                    has_human_block=has_human_block or item["status"]=="blocked"
                    item["last_error"]=err[-1000:]
                    production_recovery.mark_terminal(ep,item,"BLOCKED" if item["status"]=="blocked" else "TECH_FAILED",code=code)
                    has_technical_failure=True
            elif image_event.event == "IMAGE_FAILED":
                err=str(payload.get("error") or payload.get("result") or "worker failed")
                ledger_tech_fail(ep,item,"WORKER_FAILED",err)
                item["status"]="tech_failed"
                item["last_error"]=err[:1000]
                production_recovery.mark_terminal(ep,item,"TECH_FAILED",code="WORKER_FAILED")
                has_technical_failure=True

        q.setdefault("runtime_events",[]).append({
            "event":image_event.event,
            "task_id":image_event.item_id,
            "payload":payload,
            "at":now()
        })
        save_queue(ep,q)

    await scheduler_core.run_execution_loop(
        started, handler, consume, workers=max_workers,
        stream=async_scheduler_adapter.stream_tasks)

    # A logical Codex batch is concurrent single-image work.  Do not let its
    # successful frames claim native multi-image/provider-request capability.
    # Conversely, record a native API batch only after every planned frame has
    # been committed to the ledger; a partial result is useful evidence but not
    # a capability proof.
    native_requested=provider["provider"]=="openai_images_api" and bool(provider.get("native_multi_image"))
    native_completed=(native_requested and bool(started) and successful_results==len(started)
                      and not native_fallback_used)
    if successful_results:
        batch_capability_probe.record(
            ep,
            supported=native_completed,
            requested=len(started) if native_requested else 1,
            returned=successful_results if native_requested else 1,
            reason="NATIVE_BATCH_SUCCEEDED" if native_completed else (
                "NATIVE_BATCH_PARTIAL" if native_requested else "REAL_FRAME_SUCCEEDED"),
            batch_id=batch_id,
            provider=provider["provider"],
            transport=provider.get("execution_mode"),
            runtime_succeeded=successful_results==len(started),
            native_multi_image=native_completed,
            single_http_request=native_completed,
        )

    # Scout starts only after every submitted original is terminal. It cannot
    # grant final PASS, and its own technical failure does not stop sibling work.
    q=load_queue(ep)
    submitted={x["id"] for x in started}
    for item in q.get("items") or []:
        if item.get("id") not in submitted or item.get("status")!="generated": continue
        if frame_scout.required(ep):
            try:
                scout=await asyncio.to_thread(frame_scout.evaluate_candidate,ep,int(item["frame"]),
                    ROOT/item["output_path"],codex_raw=codex,timeout=runtime_timeout_policy.cap("fast_scout",timeout))
                item["scout"]=scout
                decision=batch_repair_arbiter.assess(ep,int(item["frame"]),scout,
                    batch_complete=True,batch_id=str(item.get("batch_id") or "ASYNC"))
                if decision["action"] in {"SINGLE_REPAIR","EARLY_SINGLE_REPAIR"}:
                    applied=batch_repair_arbiter.apply(ep,decision)
                    item["repair_assessment"]=applied
                    if applied["ledger_repair_authorized"]: item["status"]="scout_repair"
            except Exception as exc:
                item["scout"]={"decision":"DEFER_TO_FINAL","notes":str(exc),"final_critic_still_required":True}
        item.pop("_defer_scout",None)
    save_queue(ep,q)
    perf_path=ep/runtime_observability.BATCH_RUNTIME_PERFORMANCE_REL
    perf=read_json(perf_path) if perf_path.is_file() else {"schema_version":1,"batches":[]}
    completed=[x for x in q.get("items") or [] if x.get("id") in submitted and x.get("output_path")]
    perf.setdefault("kind","batch_runtime_performance")
    perf.setdefault("schema_version",1)
    perf.setdefault("generated_at",now())
    perf.setdefault("batches",[]).append({"batch_id":batch_id,"planned_count":len(started),
        "returned_count":len(completed),"provider":provider["provider"],
        "logical_batch":provider["provider"]=="codex_subscription",
        "native_multi_image":native_completed,"single_http_request":native_completed,
        "execution_mode":provider.get("execution_mode"),"max_workers":max_workers,
        "evidence_not_authority":True,"finished_at":now()})
    write_json(perf_path,perf)
    if has_human_block and not ready_items(ep,load_queue(ep)):
        return HUMAN_REQUIRED
    if has_technical_failure:
        q=load_queue(ep)
        q["adaptive_parallel"]=max(1,max_workers-1)
        save_queue(ep,q)
        return RECOVERABLE_FAILURE
    return SUCCESS


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
