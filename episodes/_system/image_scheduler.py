#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 6 bounded image scheduler.

Only the expensive image backend runs concurrently.
All Production Ledger mutations are committed sequentially by the scheduler main thread.
"""
from __future__ import annotations

import argparse
import asyncio
import concurrent.futures as cf
import datetime as dt
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import frame_contract
import environment_contract
import fast_frame_scout as frame_scout
import image_model_policy
import image_worker_pool
import rolling_frame_review
import asset_lineage
import character_visual_contract
import reference_arbitrator
import visual_lock_baseline_gate
import episode_performance
import raw_candidate_budget
import storyos_config
import scheduler_core
import batch_scheduler
import production_queue_store
import runtime_router
import product_runtime_adapter
import resource_library
import runtime_portability
import runtime_event_collector
import production_recovery
import production_ledger
import runtime_timeout_policy

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
QUEUE_REL = scheduler_core.QUEUE_REL
SCHEDULER_LOCK_REL = Path("meta/runtime-image-scheduler.lock")
_CONFIG = storyos_config.load_config()
MAX_SUPPORTED_WORKERS = int(storyos_config.get_path(_CONFIG, "production.max_inflight_images"))
DEFAULT_IMAGE_QUALITY = str(storyos_config.get_path(_CONFIG, "image.quality"))
TECH_RETRY_MAX = int(storyos_config.get_path(_CONFIG, "production.technical_retry.max_attempts_per_item"))
TECH_RETRY_BACKOFF = tuple(int(x) for x in storyos_config.get_path(_CONFIG, "production.technical_retry.backoff_seconds"))
RETRYABLE_TECH_CODES = {
    "NETWORK_ERROR", "NETWORK_CONNECT", "RATE_LIMIT_429", "BACKEND_5XX", "PROVIDER_CAPACITY", "TIMEOUT", "IMAGE_BACKEND_ERROR",
    "IMAGE_BACKEND_NO_OUTPUT",
    "LOCAL_WORKSPACE_PERMISSION",
    "PROVIDER_ARTIFACT_SAVE_COLLISION", "WORKER_FAILED", "WORKER_INTERRUPTED_FAILURE", "WORKER_PROCESS_LOST",
}
NON_REGENERATING_FAILURE_CODES = {
    "NORMALIZE_REVIEW", "ASPECT_RATIO_MISMATCH", "NORMALIZE_TECHNICAL_FAILURE",
    "NORMALIZE_INPUT_MISSING", "NORMALIZE_OUTPUT_EXISTS", "NORMALIZE_OUTPUT_FORMAT",
    "EPISODE_CANVAS_MISMATCH", "IMAGE_MODEL_CONTRACT_MISMATCH", "IMAGE_QUALITY_CONTRACT_MISMATCH",
    "RAW_CANDIDATE_BUDGET_EXHAUSTED",
    "EPISODE_IMAGE_LOOP_GUARD",
    "RUNTIME_CIRCUIT_OPEN",
    "CANDIDATE_COMMIT_FAILED",  # STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
    "PROMPT_SOURCE_DRIFT",
}

READY_LEDGER_STATES = production_ledger.READY_LEDGER_STATES


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    return story_json.read_json(path)


def write_json(path: Path,data:dict)->None:
    story_json.write_json(path, data)


def resolve_ep(raw:str)->Path:
    ep=Path(raw).resolve()
    if not ep.is_dir():raise SystemExit(f"episode directory not found: {ep}")
    try:ep.relative_to(ROOT.resolve())
    except ValueError:raise SystemExit("episode must be inside repository")
    return ep


def repo_file(raw:str)->Path:
    p=Path(raw)
    p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    try:p.relative_to(ROOT.resolve())
    except ValueError as exc:raise ValueError(f"path escapes repository: {raw}") from exc
    if not p.is_file():raise ValueError(f"file missing: {raw}")
    return p


def repo_rel(path:Path)->str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_queue(ep:Path)->dict:
    return scheduler_core.load_queue(ep, max_parallel=MAX_SUPPORTED_WORKERS)


def save_queue(ep:Path,q:dict)->None:
    scheduler_core.save_queue(ep,q)


QueueMutationBusy = scheduler_core.QueueMutationBusy


queue_transaction = scheduler_core.queue_transaction


def ledger(ep:Path)->dict:
    return scheduler_core.ledger(ep)


def ledger_state(ep:Path,frame:int)->str:
    return scheduler_core.ledger_state(ep,frame)


from frame_risk import risk_priority
import story_json


def directive_dependency(ep:Path,frame:int)->list[int]:
    # STORY_OS_V211_PERF_FINAL_R2: narrative escalation never implies PNG serialization.
    # Only an explicit generation_depends_on declares a true pixel prerequisite.
    d=frame_contract.compile_frame(ep,frame,write_cache=True)["hash_material"]["frame_directive"]
    raw=d.get("generation_depends_on")
    if raw in (None,"",[]):return []
    values=raw if isinstance(raw,list) else str(raw).replace(";",",").split(",")
    out=[]
    for value in values:
        try:n=int(value)
        except Exception:continue
        if 1<=n<frame and n not in out:out.append(n)
    return sorted(out)


def narrative_escalation_from(ep:Path,frame:int)->int|None:
    d=frame_contract.compile_frame(ep,frame,write_cache=True)["hash_material"]["frame_directive"]
    try:
        n=int(d.get("escalation_from"))
        return n if 1<=n<frame else None
    except Exception:return None


def contract_references(ep:Path,frame:int,scope:str="batch")->list[dict]:
    refs,_=reference_arbitrator.select(ep,frame,scope=scope)
    # Required reference anchors are execution contracts, not documentation only.
    gates_path=ep / "meta" / "story-gates.json"
    gates={}
    try:
        if gates_path.exists():
            gates=json.loads(gates_path.read_text(encoding="utf-8"))
    except Exception:
        gates={}
    check=reference_arbitrator.validate_required_anchor_execution(ep,frame,refs,gates)
    if not check.get("ok"):
        raise RuntimeError("REQUIRED_REFERENCE_ANCHOR_MISSING:" + ",".join(check.get("missing_anchors") or []))
    return refs


def init_queue(ep:Path,force:bool=False)->dict:
    with queue_transaction(ep):
        # In Redis hot-state mode the compatibility file is intentionally absent;
        # consult the authoritative projection before deciding to initialize.
        # Otherwise every prepare cycle recreates an empty queue and discards the
        # items already admitted in Redis.
        import hot_state_bridge
        hot = hot_state_bridge.read(ep, "QUEUE")
        if not force and isinstance(hot.get("value"), dict):
            return hot["value"]
        p=scheduler_core.queue_read_path(ep)
        if p.exists() and not force:return read_json(p)
        q={"schema_version":1,"created_at":now(),"updated_at":now(),"max_parallel":MAX_SUPPORTED_WORKERS,"adaptive_parallel":MAX_SUPPORTED_WORKERS,"stable_waves":0,"items":[],"waves":[]}
        save_queue(ep,q);return q


def add_item(ep:Path,*,frame:int,kind:str,prompt_file:Path,scope:str,references:list[dict],capture_id:str,model:str,depends_on:list[int],quality:str=DEFAULT_IMAGE_QUALITY,strict_model:bool=False,replace:bool=False)->dict:
    with queue_transaction(ep):
        q=load_queue(ep)
        key=f"{frame:02d}"
        active=[x for x in q.get("items") or [] if f"{int(x.get('frame')):02d}"==key and x.get("kind")==kind and x.get("status") in {"queued","running","generated","tech_failed"}]
        if active and not replace:
            return active[-1]
        if replace:
            replaceable=[x for x in q.get("items") or [] if f"{int(x.get('frame')):02d}"==key and x.get("kind")==kind and x.get("status") in {"queued","running","generated","tech_failed","blocked","scout_repair"}]
            for x in replaceable:x["status"]="superseded"
        contract=frame_contract.provenance(ep,frame)
        if frame_contract.required(ep):
            import prompt_package
            package=prompt_package.compile_frame(ep,frame,prompt_file)
            admission_snapshot={
                "package_sha256":package["package_sha256"],
                "scene_prompt_sha256":package["scene_prompt_sha256"],
                "frame_contract_sha256":package["frame_contract_sha256"],
            }
        else:
            admission_snapshot=None
        item={
            "id":uuid.uuid4().hex[:12],
            "frame":frame,
            "kind":kind,
            "scope":scope,
            "status":"queued",
            "prompt_file":repo_rel(prompt_file),
            "references":references,
            # W-17: persist the exact execution contract instead of only the declaration.
            "reference_execution_contract":{
                "selected_at_enqueue":now(),
                "selected_references":references,
                "selected_roles":[str(x.get("role") or "") for x in references if isinstance(x,dict)],
                "selected_kinds":[str(x.get("kind") or "") for x in references if isinstance(x,dict)],
            },
            "capture_id":capture_id,
            "model":model,
            "quality":quality,
            "strict_model":bool(strict_model),
            "depends_on":sorted(set(int(x) for x in depends_on if int(x)!=frame)),
            "narrative_escalation_from":narrative_escalation_from(ep,frame),
            "priority":risk_priority(ep,frame,scope),
            "frame_contract":contract,
            "prompt_package":admission_snapshot,
            "attempts":0,
            "output_path":None,
            "log_path":None,
            "last_error":None,
            "queued_at":now(),
        }
        q.setdefault("items",[]).append(item);save_queue(ep,q);return item


def parse_ref(raw:str)->dict:
    parts=raw.split("::")
    if len(parts)!=3:raise ValueError("reference must be PATH::ROLE::KIND")
    p=repo_file(parts[0].strip())
    return {"path":repo_rel(p),"role":parts[1].strip(),"kind":parts[2].strip()}


def import_visual_lock(ep:Path,prompt_dir:Path)->dict:
    plan_path=ep/"meta/visual-lock-plan.json"
    if not plan_path.is_file():raise ValueError("visual-lock-plan missing; run visual_lock_v21.py prepare")
    plan=read_json(plan_path)
    q=init_queue(ep)
    added=[]
    for row in plan.get("items") or []:
        frame=int(row["frame"]);prompt=prompt_dir/f"{frame:02d}.txt"
        if not prompt.is_file():raise ValueError(f"Visual Lock prompt missing: {prompt}")
        policy=image_model_policy.for_episode(ep)
        added.append(add_item(ep,frame=frame,kind="original",prompt_file=prompt,scope="visual_lock",references=contract_references(ep,frame,scope="visual_lock"),capture_id=f"visual-lock-{frame:02d}",model=policy["model"],quality=policy["quality"],strict_model=bool(policy.get("strict_model")),depends_on=[int(x) for x in row.get("depends_on") or []],replace=False))
    return {"added":[x["id"] for x in added]}


def refresh_queued_visual_lock_references(ep:Path)->dict:
    """Re-resolve queued Visual Lock lineage references after baseline PASS.

    Initial Visual Lock rows, bounded candidates, and repair rows can all be
    queued before a provisional Pixel Master exists. Once baseline PASS creates
    that master, refresh every still-queued Visual Lock lineage request; never
    mutate already-started/generated requests.
    """
    with queue_transaction(ep):
        q=load_queue(ep);updated=[]
        for item in q.get("items") or []:
            if item.get("status")!="queued" or item.get("scope") not in {"visual_lock","repair","baseline_candidate"}:
                continue
            frame=int(item.get("frame") or 0)
            ref_scope="visual_lock" if item.get("scope")=="visual_lock" else "repair"
            refs=contract_references(ep,frame,scope=ref_scope)
            item["references"]=refs
            item["reference_execution_contract"]={
                "selected_at_enqueue":now(),
                "selected_references":refs,
                "selected_roles":[str(x.get("role") or "") for x in refs if isinstance(x,dict)],
                "selected_kinds":[str(x.get("kind") or "") for x in refs if isinstance(x,dict)],
                "refresh_reason":"baseline_pixel_master_available",
            }
            updated.append(frame)
        save_queue(ep,q)
        return {"updated_frames":sorted(updated),"count":len(updated)}


def import_batch(ep:Path,prompt_dir:Path)->dict:
    total=frame_contract.frame_count(ep);q=init_queue(ep);added=[];skipped=[]
    existing={(int(x["frame"]),x.get("kind")) for x in q.get("items") or [] if x.get("status") not in {"superseded"}}
    for frame in range(1,total+1):
        if ledger_state(ep,frame) in READY_LEDGER_STATES:
            skipped.append(frame);continue
        if (frame,"original") in existing:
            skipped.append(frame);continue
        prompt=prompt_dir/f"{frame:02d}.txt"
        if not prompt.is_file():raise ValueError(f"batch prompt missing: {prompt}")
        policy=image_model_policy.for_episode(ep)
        added.append(add_item(ep,frame=frame,kind="original",prompt_file=prompt,scope="batch",references=contract_references(ep,frame,scope="batch"),capture_id=f"batch-{frame:02d}",model=policy["model"],quality=policy["quality"],strict_model=bool(policy.get("strict_model")),depends_on=directive_dependency(ep,frame),replace=False))
    return {"added":[x["frame"] for x in added],"skipped":skipped}


def dependency_satisfied(ep:Path,q:dict,dep:int,scope:str="batch")->bool:
    # Ordinary baseline is the identity bootstrap for every downstream lane,
    # including repair/baseline-candidate rows. Historical generated pixels must
    # not satisfy this dependency after a later review reopens the baseline.
    if visual_lock_baseline_gate.is_baseline_dependency(ep,dep):
        return visual_lock_baseline_gate.approved(ep)
    state=ledger_state(ep,dep)
    if state in READY_LEDGER_STATES:return True
    rows=[x for x in q.get("items") or [] if int(x.get("frame"))==dep and x.get("status")=="generated"]
    return bool(rows)


def ready_items(ep:Path,q:dict)->tuple[list[dict],list[dict]]:
    ready=[];blocked=[]
    for item in q.get("items") or []:
        if item.get("status")!="queued":continue
        deps=[int(x) for x in item.get("depends_on") or []]
        if all(dependency_satisfied(ep,q,x,str(item.get("scope") or "batch")) for x in deps):ready.append(item)
        else:blocked.append(item)
    ready.sort(key=lambda x:(-int(x.get("priority") or 0),int(x["frame"])))
    return ready,blocked


def current_contract_sha(ep:Path,frame:int)->str:
    return scheduler_core.current_contract_sha(ep,frame)


def ledger_begin(ep:Path,item:dict)->tuple[bool,str]:
    return scheduler_core.ledger_begin(
        ep,
        item,
        notes=f"phase6 scheduler item={item['id']} scope={item['scope']}",
    )


def backend_worker(ep:Path,item:dict,timeout:int,codex:str|None)->dict:
    # Warm Python pool: reuse scheduler/module state, never cross-frame Codex conversation state.
    return image_worker_pool.execute(ep,item,timeout,codex)


def ledger_success(ep:Path,item:dict,result:dict)->tuple[bool,str]:
    return scheduler_core.ledger_success(ep,item,result,
                                         default_quality=DEFAULT_IMAGE_QUALITY)


def ledger_tech_fail(ep:Path,item:dict,code:str,message:str)->None:
    scheduler_core.ledger_tech_fail(ep,item,code,message)


def classify_error(text:str)->str:
    for code in NON_REGENERATING_FAILURE_CODES:
        if code in text:return code
    if "IMAGE_BACKEND_NO_OUTPUT" in text:return "IMAGE_BACKEND_NO_OUTPUT"
    low=text.lower()
    # Prefer structured transport booleans before the broader model/backend
    # classifier.  Codex logs always print the timeout field name, including
    # when it is explicitly false; treating that token as a timeout produced
    # misleading W-98 evidence.
    if "error_is_timeout=false" in low and "error_is_connect=true" in low:
        return "NETWORK_CONNECT"
    if "error_is_timeout=true" in low:
        return "TIMEOUT"
    model_code=image_model_policy.classify_backend_error(text, source="image_backend")
    if model_code:return model_code
    if any(token in low for token in ("connection refused", "connect error", "connection error", "error sending request")):
        return "NETWORK_CONNECT"
    if "timeout" in low:return "TIMEOUT"
    if "500" in low or "502" in low or "503" in low or "5xx" in low:return "BACKEND_5XX"
    if "contract" in low and "drift" in low:return "CONTRACT_DRIFT"
    return "IMAGE_BACKEND_ERROR"


def _terminal_technical_status(item:dict,code:str)->str:
    """Choose tech_failed vs external_blocked at the failure that exhausts the epoch.

    Previously the third backend failure was persisted as TECH_FAILED and the
    resident Runner exited on rc=21 before a *later* retry-tech cycle could convert
    it to external_blocked. A restart then had to repair bookkeeping before it could
    even wait on the provider. Close the retry epoch at the point of failure instead.
    """
    used=_retry_epoch_attempts(item)
    if code in RETRYABLE_TECH_CODES and used>=TECH_RETRY_MAX:
        item["external_block"]={"at":now(),"reason":"technical_retry_exhausted","code":code,
                                "attempts":used,"max_attempts":TECH_RETRY_MAX}
        return "external_blocked"
    return "blocked" if code in NON_REGENERATING_FAILURE_CODES else "tech_failed"


async def async_backend_worker(ep:Path,item:dict,timeout:int,codex:str|None)->dict:
    """V2.7 async runtime bridge.

    A worker function returning normally is not necessarily an image success:
    image_worker_pool reports transport/backend failures as structured results.
    Convert those results into task failures so RuntimeImageEvent semantics stay
    truthful and the scheduler can close the active ledger attempt correctly.
    """
    result=await asyncio.to_thread(backend_worker,ep,item,timeout,codex)
    output=result.get("output")
    if result.get("returncode")!=0 or not output or not Path(output).is_file():
        message=str(result.get("stdout") or "image backend returned no committed output")
        raise RuntimeError(message)
    return result


def run_scheduler_async(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    """V2.7 async scheduler entry.

    Execution is event-driven; ledger commits remain in scheduler context.
    Image execution no longer depends on the legacy image ThreadPool path.
    Rolling review remains isolated on its own review executor.
    """
    try:
        with scheduler_core.queue_transaction(ep):
            return asyncio.run(_run_scheduler_async(ep,max_workers,timeout,codex))
    except QueueMutationBusy:
        return 21


async def _run_scheduler_async(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    resource_library.ensure_fresh(ep)
    q=load_queue(ep)
    production_recovery.reconcile_locked(ep,q)
    scheduler_core.terminalize_superseded_history(ep,q)
    save_queue(ep,q)
    ready,_=ready_items(ep,q)
    if not ready:
        statuses={x.get("status") for x in q.get("items") or []}
        return 22 if "blocked" in statuses else (22 if "interrupted_unknown" in statuses else (24 if "running" in statuses else (20 if "queued" in statuses else 0)))

    runtime,_=runtime_router.detect()
    image_runtime,_=runtime_router.image_execution_runtime()
    if runtime in {"WORK","WEB"} and image_runtime != "CODEX":
        request=product_runtime_adapter.build_image_request(ep,runtime=runtime,queue_items=ready[:max_workers],source="image_scheduler")
        product_runtime_adapter.print_request(request)
        return product_runtime_adapter.HOST_ACTION_REQUIRED_RC
    max_workers=max(1,min(MAX_SUPPORTED_WORKERS,max_workers))
    initial_workers=max_workers

    # STORY_OS_EP002_G2_REPAIR_CONCURRENCY (image lane only):
    # Repair items are independent, already-authorized one-shot content repairs.
    # They share the same first-completed lane as original items, bounded by
    # MAX_SUPPORTED_WORKERS (max_inflight_images).  Protections of the old
    # serial path are kept: a single ledger writer (event loop under the queue
    # OS lock), no duplicate dispatch (admission consumes queued rows), the raw
    # candidate budget claims in-flight inside each worker, per-item dependency
    # gating, and 3->2->1 degradation after technical failures in this run.
    has_block=False
    has_failure=False
    inflight=0
    worker_cap=initial_workers

    async def handler(item:dict)->dict:
        return await async_backend_worker(ep,item,timeout,codex)

    async def admit_more(limit:int)->list:
        """Admit up to `limit` newly ready items into this run.

        Called before the first wave and again after every completion so a
        freed worker slot is refilled first-completed instead of waiting for
        the rest of a wave. Returns only items admitted by this call.
        """
        nonlocal has_block,inflight
        if limit<=0:
            return []
        q=load_queue(ep)
        ready,_=ready_items(ep,q)
        admitted=[]
        busy_frames={int(x["frame"]) for x in q.get("items") or [] if x.get("status")=="running"}
        for item in ready:
            if len(admitted)>=limit:
                break
            if int(item["frame"]) in busy_frames:
                continue
            row=next((x for x in q.get("items") or [] if x["id"]==item["id"]),None)
            if row is None or row.get("status")!="queued":
                continue
            production_recovery.prepare_execution(ep,row)
            save_queue(ep,q)
            ok,msg=ledger_begin(ep,row)
            if not ok:
                has_block=True
                row["status"]="blocked"
                row["last_error"]=msg[-1000:]
                production_recovery.mark_terminal(ep,row,"BEGIN_REJECTED",reason=row["last_error"])
                save_queue(ep,q)
                continue
            row["status"]="running"
            row["attempts"]=int(row.get("attempts") or 0)+1
            row["started_at"]=now()
            production_recovery.mark_worker_pending(ep,row)
            inflight+=1
            admitted.append(row)
            busy_frames.add(int(row["frame"]))
            q.setdefault("waves",[]).append({
                "event":1,"mode":"continuous_first_completed","at":now(),
                "frame":int(row["frame"]),"status":"dispatched",
                "inflight_after":inflight,"next_parallel":worker_cap,
                "item_id":row["id"],
            })
            save_queue(ep,q)
        return admitted

    async def consume(event)->str:
        """Consume one TaskEvent; return the terminal queue status."""
        nonlocal has_block,has_failure
        image_event=runtime_event_collector.collect(event)
        q=load_queue(ep)
        item=next((x for x in q.get("items") or [] if x["id"]==image_event.item_id),None)
        if not item:
            return ""
        if image_event.event=="IMAGE_SUCCESS":
            result=image_event.payload.get("result") or image_event.payload
            msg=str(result.get("stdout") or result.get("error") or "")
            backend_ok=bool(
                result.get("returncode")==0
                and result.get("output")
                and Path(result["output"]).is_file()
            )
            ok=False
            if backend_ok:
                production_recovery.mark_terminal(ep,item,"SUCCESS_PREPARED")
                ok,msg=ledger_success(ep,item,result)
            if ok:
                item["status"]="generated"
                item["output_path"]=repo_rel(Path(result["output"]))
                if result.get("log"):
                    item["log_path"]=repo_rel(Path(result["log"]))
                item["completed_at"]=now()
                item["last_error"]=None
                item.pop("technical_failure_code",None)
                item.pop("external_block",None)
                item.pop("retry_exhausted",None)
                item["prompt_package"]=result.get("prompt_package")
                production_recovery.mark_terminal(ep,item,"COMMITTED")
                episode_performance.safe_record_queue_image_attempt(ep,item,status="generated")
            else:
                if not msg:
                    msg="image backend failed without terminal output"
                has_failure=True
                code="CANDIDATE_COMMIT_FAILED" if backend_ok else classify_error(msg)
                if not backend_ok: ledger_tech_fail(ep,item,code,msg)
                item["status"]=_terminal_technical_status(item,code)
                item["technical_failure_code"]=code
                item.setdefault("technical_failures",[]).append({"at":now(),"attempt":int(item.get("attempts") or 0),"code":code})
                has_block=has_block or item["status"]=="blocked"
                if result.get("output"): item["candidate_output_path"]=str(result["output"])
                item["completed_at"]=now()
                item["last_error"]=runtime_portability.sanitize_diagnostic_text(str(msg)[-1600:])
                production_recovery.mark_terminal(ep,item,"BLOCKED" if item["status"]=="blocked" else "TECH_FAILED", code=code)
                episode_performance.safe_record_queue_image_attempt(
                    ep,item,status=item["status"],error_code=code)
        elif image_event.event=="IMAGE_FAILED":
            has_failure=True
            msg=str(image_event.payload.get("error") or "async worker failed")
            code=classify_error(msg)
            ledger_tech_fail(ep,item,code,msg)
            item["status"]=_terminal_technical_status(item,code)
            item["technical_failure_code"]=code
            item.setdefault("technical_failures",[]).append({"at":now(),"attempt":int(item.get("attempts") or 0),"code":code})
            has_block=has_block or item["status"]=="blocked"
            item["completed_at"]=now()
            item["last_error"]=runtime_portability.sanitize_diagnostic_text(msg[-1600:])
            production_recovery.mark_terminal(ep,item,"BLOCKED" if item["status"]=="blocked" else "TECH_FAILED", code=code)
            episode_performance.safe_record_queue_image_attempt(
                ep,item,status=item["status"],error_code=code)
        q.setdefault("runtime_events",[]).append({"event":image_event.event,"task_id":image_event.item_id,"payload":runtime_event_collector.json_safe(image_event.payload),"at":now()})
        save_queue(ep,q)
        return str(item.get("status") or "")

    async def completed(event,status,active,cap):
        nonlocal inflight,worker_cap
        inflight,worker_cap=active,cap
        q=load_queue(ep)
        row=next((x for x in q.get("items") or [] if x["id"]==event.task_id),None)
        q.setdefault("waves",[]).append({
            "event":2,"mode":"continuous_first_completed","at":now(),
            "frame":int(row["frame"]) if row else None,
            "status":status or "unknown",
            "inflight_after":inflight,"next_parallel":worker_cap,
            "item_id":event.task_id,
        })
        save_queue(ep,q)

    await scheduler_core.run_execution_loop(
        [],handler,consume,workers=max_workers,admit=admit_more,completed=completed)

    final_q=load_queue(ep)
    rc=_scheduler_terminal_rc(final_q,has_block=has_block,has_failure=has_failure,ep=ep)
    try:
        import workflow_observability
        workflow_observability.collect(ep,write=True)
    except Exception:
        pass
    return rc


def _scheduler_terminal_rc(q:dict,*,has_block:bool,has_failure:bool,ep:Path|None=None)->int:
    final_statuses={str(x.get("status") or "") for x in q.get("items") or []}
    if has_block and ep is not None and not ready_items(ep,q)[0]:
        return 22
    if "tech_failed" in final_statuses:
        return 21
    external=[x for x in q.get("items") or [] if x.get("status")=="external_blocked"]
    # A provider/model is exhausted, but the system-default availability chain
    # still has another model. Keep the resident Driver in a retryable technical
    # state so the next cycle can apply the failover instead of exiting rc=24.
    if external and any(availability_fallback_model(x) for x in external):
        return 21
    if external:
        return 24
    return 21 if has_failure else 0


def run_scheduler_legacy_removed_path(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    """Legacy image execution path removed in V2.7.

    Production execution must use run_scheduler_async(). This guard remains
    only to provide a clear failure for stale callers.
    """
    raise RuntimeError("LEGACY_IMAGE_SCHEDULER_REMOVED_USE_ASYNC_RUNTIME")


def _technical_retry_code(item:dict)->str:
    error=str(item.get("last_error") or "")
    # W-107: old queue rows may already have collapsed a local Windows staging
    # ACL failure into PERMISSION_403. Reclassify that narrow signature from the
    # preserved error text so recovery can open a new bounded technical epoch.
    inferred=image_model_policy.classify_backend_error(error,source="image_backend")
    if inferred==image_model_policy.LOCAL_WORKSPACE_PERMISSION:
        return inferred
    code=str(item.get("technical_failure_code") or "").strip().upper()
    return code or inferred or classify_error(error)


def _retry_epoch_attempts(item:dict)->int:
    return max(0,int(item.get("attempts") or 0)-int(item.get("technical_retry_epoch_start_attempt") or 0))


def availability_fallback_model(item:dict,code:str|None=None)->str|None:
    code=str(code or _technical_retry_code(item)).strip().upper()
    if code not in {image_model_policy.PROVIDER_CAPACITY,image_model_policy.MODEL_UNAVAILABLE}:
        return None
    return image_model_policy.next_fallback_model(
        str(item.get("model") or ""),strict_model=bool(item.get("strict_model")))


def _apply_model_failover(item:dict,code:str)->str|None:
    """Advance one model after this model's bounded availability retries exhaust."""
    if code not in {image_model_policy.PROVIDER_CAPACITY,image_model_policy.MODEL_UNAVAILABLE}:
        return None
    if bool(item.get("strict_model")):
        return None
    current=str(item.get("model") or "").strip()
    target=availability_fallback_model(item,code)
    if not target:
        return None
    stamp=now()
    item.setdefault("model_failovers",[]).append({
        "at":stamp,"from":current,"to":target,"trigger_code":code,
        "attempts_before_failover":int(item.get("attempts") or 0),
    })
    item["model"]=target
    item["technical_retry_epoch_start_attempt"]=int(item.get("attempts") or 0)
    item.pop("external_block",None)
    item["last_error"]=None
    item["retry_pending"]=False
    item.pop("execution",None)
    item.pop("started_at",None)
    item.pop("completed_at",None)
    return target


def resume_authorized_budget(ep:Path,frames:list[int]|None=None)->dict:
    """Requeue only budget-blocked items whose current bounded budget now fits.

    Capacity may come from an explicit user authorization or from a deterministic
    semantic/policy budget epoch already encoded by raw_candidate_budget. This
    step never raises a limit and never guesses approval.
    """
    ep=Path(ep).resolve();wanted={int(x) for x in (frames or [])}
    with queue_transaction(ep):
        q=load_queue(ep)
        blocked=[item for item in q.get("items") or []
                 if item.get("status")=="blocked"
                 and str(item.get("technical_failure_code") or "").upper() in raw_candidate_budget.BUDGET_BLOCK_CODES
                 and (not wanted or int(item.get("frame") or 0) in wanted)]
        context=raw_candidate_budget.blocked_queue_context(ep,blocked)
        allowed=set(int(x) for x in context.get("resumable_frames") or [])
        requeued=[]
        for item in blocked:
            frame=int(item.get("frame") or 0)
            if frame not in allowed:
                continue
            item.setdefault("budget_recovery",[]).append({"at":now(),"reason":"bounded_budget_capacity_available"})
            item["status"]="queued"
            item["last_error"]=None
            item.pop("technical_failure_code",None)
            item.pop("external_block",None)
            item.pop("retry_exhausted",None)
            item.pop("execution",None)
            item.pop("started_at",None)
            item.pop("completed_at",None)
            requeued.append(frame)
        save_queue(ep,q)
        return {"status":"PASS" if requeued else "BLOCKED","requeued_frames":sorted(set(requeued)),"budget":context}


def retry_tech(ep:Path,frame:int|None=None,*,reset_exhausted:bool=False,sleep_fn=time.sleep)->dict:
    ep=Path(ep).resolve()
    # Availability exhaustion can move a non-strict system-default item to the
    # next configured model without user intervention. Other technical failures
    # stay blocked until an explicit reset proves the same provider recovered.
    with queue_transaction(ep):
        q=load_queue(ep)
        for item in q.get("items") or []:
            if item.get("status")!="external_blocked" or (frame is not None and int(item.get("frame") or -1)!=int(frame)):
                continue
            code=_technical_retry_code(item)
            target=_apply_model_failover(item,code)
            if target:
                item["status"]="tech_failed"
                continue
            if reset_exhausted:
                item["status"]="tech_failed"
                item["technical_retry_epoch_start_attempt"]=int(item.get("attempts") or 0)
                item.pop("external_block",None)
        save_queue(ep,q)

    preview=load_queue(ep);delays=[]
    for item in preview.get("items") or []:
        if item.get("status")!="tech_failed" or (frame is not None and int(item.get("frame") or -1)!=int(frame)):
            continue
        code=_technical_retry_code(item);used=_retry_epoch_attempts(item)
        if code in RETRYABLE_TECH_CODES and used < TECH_RETRY_MAX and used>0:
            delays.append(TECH_RETRY_BACKOFF[min(used-1,len(TECH_RETRY_BACKOFF)-1)])
    delay=max(delays or [0])
    if delay>0:
        sleep_fn(delay)

    with queue_transaction(ep):
        q=load_queue(ep);count=0;exhausted=[];non_retryable=[]
        for item in q.get("items") or []:
            if item.get("status")!="tech_failed" or (frame is not None and int(item.get("frame") or -1)!=int(frame)):
                continue
            code=_technical_retry_code(item);used=_retry_epoch_attempts(item)
            if code not in RETRYABLE_TECH_CODES:
                item["status"]="external_blocked"
                item["external_block"]={"at":now(),"reason":"non_retryable_technical_failure","code":code,"attempts":used,"max_attempts":TECH_RETRY_MAX}
                non_retryable.append(int(item.get("frame") or 0));continue
            if used >= TECH_RETRY_MAX:
                item["status"]="external_blocked"
                item["external_block"]={"at":now(),"reason":"technical_retry_exhausted","code":code,"attempts":used,"max_attempts":TECH_RETRY_MAX}
                exhausted.append(int(item.get("frame") or 0));continue
            item["status"]="queued"
            item["last_error"]=None
            item["retry_pending"]=False
            item["retry_backoff_seconds"]=delay
            # A technical retry is a new backend execution transaction even
            # when it reuses the same queue item/content-repair/candidate round.
            item.pop("execution",None)
            item.pop("started_at",None)
            item.pop("completed_at",None)
            count+=1
        save_queue(ep,q)
        return {"requeued":count,"frame":frame,"backoff_seconds":delay,"exhausted_frames":sorted(set(exhausted)),"non_retryable_frames":sorted(set(non_retryable))}


def self_test()->None:
    assert MAX_SUPPORTED_WORKERS == int(storyos_config.get_path(_CONFIG, "production.max_inflight_images"))
    assert classify_error("429 Too Many Requests")=="RATE_LIMIT_429"
    assert classify_error("worker timeout")=="TIMEOUT"
    assert classify_error("unknown model")=="MODEL_UNAVAILABLE"
    assert classify_error("Selected model is at capacity. Please try a different model.")=="PROVIDER_CAPACITY"
    assert classify_error("image generation failed: network error: error sending request")=="NETWORK_ERROR"
    assert TECH_RETRY_MAX == 3 and TECH_RETRY_BACKOFF == (15,45)
    assert classify_error("ASPECT_RATIO_MISMATCH: inspect Generation Request")=="ASPECT_RATIO_MISMATCH"
    assert image_worker_pool.CODEX_SESSION_REUSE is False
    assert rolling_frame_review.VALID == {"PASS_PREVIEW","REPAIR_NOW","UNCERTAIN"}
    assert runtime_router.image_execution_runtime()[0] in {"CODEX","PRODUCT_RUNTIME","AUTO"}
    src=Path(__file__).read_text(encoding="utf-8-sig")
    assert "LEGACY_IMAGE_SCHEDULER_REMOVED_USE_ASYNC_RUNTIME" in src
    assert "story-os-image" not in src[src.index("def run_scheduler_async"):src.index("def run_scheduler", src.index("def run_scheduler_async"))]
    body=src[src.index("def directive_dependency"):src.index("def narrative_escalation_from")]
    assert "generation_depends_on" in body and "escalation_from" not in body
    print("IMAGE SCHEDULER V2.1 PHASE6 + R2 DEPENDENCY SELF-TEST PASS")


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("add");p.add_argument("episode_dir");p.add_argument("--frame",type=int,required=True);p.add_argument("--kind",choices=["original","repair","baseline_candidate"],default="original");p.add_argument("--scope",choices=["visual_lock","batch","repair","baseline_candidate"],default="batch");p.add_argument("--prompt-file",required=True);p.add_argument("--reference",action="append",default=[]);p.add_argument("--capture-id");p.add_argument("--model");p.add_argument("--quality",choices=["high"]);p.add_argument("--depends-on",action="append",default=[]);p.add_argument("--replace",action="store_true")
    p=sub.add_parser("import-visual-lock");p.add_argument("episode_dir");p.add_argument("--prompt-dir",required=True)
    p=sub.add_parser("import-batch");p.add_argument("episode_dir");p.add_argument("--prompt-dir",required=True)
    p=sub.add_parser("plan");p.add_argument("episode_dir")
    p=sub.add_parser("run");p.add_argument("episode_dir");p.add_argument("--max-workers",type=int,default=MAX_SUPPORTED_WORKERS);p.add_argument("--timeout",type=int,default=None);p.add_argument("--codex")
    p=sub.add_parser("retry-tech");p.add_argument("episode_dir");p.add_argument("--frame",type=int);p.add_argument("--reset-exhausted",action="store_true",help="start a new bounded technical-retry epoch after the external provider has recovered")
    p=sub.add_parser("reconcile");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=resolve_ep(a.episode_dir)
    try:
        if a.cmd=="init":print(json.dumps(init_queue(ep,a.force),ensure_ascii=False,indent=2));return 0
        if a.cmd=="add":
            refs=[parse_ref(x) for x in a.reference];deps=[]
            for raw in a.depends_on:
                deps.extend(int(x) for x in str(raw).split(",") if x.strip())
            prompt=repo_file(a.prompt_file)
            policy=image_model_policy.for_episode(ep)
            row=add_item(ep,frame=a.frame,kind=a.kind,prompt_file=prompt,scope=a.scope,references=refs,capture_id=a.capture_id or f"scheduler-{a.frame:02d}",model=a.model or policy["model"],quality=a.quality or policy["quality"],strict_model=True if a.model else bool(policy.get("strict_model")),depends_on=deps,replace=a.replace)
            print(json.dumps(row,ensure_ascii=False,indent=2));return 0
        if a.cmd=="reconcile":
            with queue_transaction(ep):
                q=load_queue(ep)
                report=production_recovery.reconcile_locked(ep,q)
                save_queue(ep,q)
            print(json.dumps(report,ensure_ascii=False,indent=2));return 0
        if a.cmd=="import-visual-lock":print(json.dumps(import_visual_lock(ep,Path(a.prompt_dir).resolve()),ensure_ascii=False,indent=2));return 0
        if a.cmd=="import-batch":print(json.dumps(import_batch(ep,Path(a.prompt_dir).resolve()),ensure_ascii=False,indent=2));return 0
        if a.cmd=="plan":
            q=load_queue(ep);ready,blocked=ready_items(ep,q)
            print(json.dumps({"ready":[{"frame":x["frame"],"priority":x["priority"],"scope":x["scope"]} for x in ready],"blocked":[{"frame":x["frame"],"depends_on":x["depends_on"]} for x in blocked],"progress":scheduler_core.progress(ep,q)},ensure_ascii=False,indent=2));return 0
        if a.cmd=="run":
            run_timeout=runtime_timeout_policy.resolve("image_lane_run", a.timeout)
            if batch_scheduler.should_use(ep):
                return batch_scheduler.run(ep,a.max_workers,run_timeout,a.codex)
            return run_scheduler_async(ep,a.max_workers,run_timeout,a.codex)
        if a.cmd=="retry-tech":print(json.dumps(retry_tech(ep,a.frame,reset_exhausted=a.reset_exhausted),ensure_ascii=False,indent=2));return 0
        print(json.dumps(load_queue(ep),ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print("IMAGE SCHEDULER ERROR:",exc);return 3


if __name__=="__main__":raise SystemExit(main())

# STORY_OS_V211_RUNTIME_CLOSURE_R31

# STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE
