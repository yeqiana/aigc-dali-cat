#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as cf, datetime as dt, json, subprocess, sys, time
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
    p=ep/QUEUE_REL;return read_json(p) if p.is_file() else {"schema_version":1,"items":[],"waves":[]}
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
            item["status"]="blocked";item["last_error"]="ledger begin failed: "+msg[-1000:]
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

def run(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    capability=batch_capability_probe.supported(ep)
    pool_workers=batch_runtime_config.max_inflight_batches()
    cap=pool_workers if capability is True else batch_runtime_config.probe_initial_inflight()
    perf={"schema_version":1,"mode":"batch_image_runtime_v240","started_at":now(),"batches":[],"fallback_single_frames":0}
    inflight={}
    with cf.ThreadPoolExecutor(max_workers=pool_workers,thread_name_prefix="story-os-batch") as pool:
        while True:
            q=load_queue(ep);ready=ready_items(ep,q)
            if not ready and not inflight:break
            contracts=batch_contract.plan(ep,ready)
            while contracts and len(inflight)<cap:
                contract=contracts.pop(0)
                items=_mark_batch_running(ep,contract)
                if not items:continue
                fut=pool.submit(batch_image_worker.execute_batch,ep,contract,items,timeout,codex)
                inflight[fut]=(contract,items)
            if not inflight:
                break
            done,_=cf.wait(set(inflight),return_when=cf.FIRST_COMPLETED)
            for fut in done:
                contract,items=inflight.pop(fut)
                try:result=fut.result()
                except Exception as exc:result={"ok":False,"error":str(exc),"requested_count":len(items),"returned_count":0,"results":{}}
                supported=bool(result.get("ok") and int(result.get("returned_count") or 0)==int(contract["planned_count"]))
                batch_capability_probe.record(ep,supported=supported,requested=int(contract["planned_count"]),
                    returned=int(result.get("returned_count") or 0),reason="real_batch_success" if supported else str(result.get("error") or "batch_failed"),
                    batch_id=contract["batch_id"])
                if supported:
                    cap=pool_workers
                else:
                    cap=1
                q=load_queue(ep);byid={x["id"]:x for x in q.get("items") or []}
                if supported:
                    generated_rows=[]
                    for original in items:
                        item=byid[original["id"]];res=result["results"][item["id"]]
                        ok,msg=ledger_success(ep,item,res)
                        if ok:
                            item["status"]="generated";item["output_path"]=Path(res["output"]).resolve().relative_to(ROOT).as_posix()
                            item["completed_at"]=now();item["last_error"]=None;item["prompt_package"]=res.get("prompt_package")
                            generated_rows.append((item,res))
                        else:
                            item["status"]="blocked";item["last_error"]=msg[-1000:]
                    _update_batch_row(q,contract["batch_id"],status="generated",completed_at=now(),
                        returned_count=result.get("returned_count"),elapsed_seconds=result.get("elapsed_seconds"))
                    save_queue(ep,q)

                    # All original outputs in this request are now terminal, so the Batch Repair
                    # Barrier is open. Assess frames independently; High×High remains explicitly
                    # marked as EARLY_SINGLE_REPAIR by the gate, while ordinary failures only
                    # become actionable after this barrier.
                    decisions=[]
                    for item,res in generated_rows:
                        scout={}
                        if frame_scout.required(ep):
                            scout=frame_scout.evaluate_candidate(ep,int(item["frame"]),Path(res["output"]),
                                codex_raw=codex,timeout=min(240,max(60,timeout)))
                        assessment=batch_repair_arbiter.assess(
                            ep,int(item["frame"]),scout,batch_complete=True,batch_id=contract["batch_id"])
                        applied=batch_repair_arbiter.apply(ep,assessment)
                        decisions.append(applied)
                        qq=load_queue(ep);target={x["id"]:x for x in qq.get("items") or []}.get(item["id"])
                        if target:
                            target["scout"]={
                                "decision":scout.get("decision"),
                                "risk_level":scout.get("risk_level"),
                                "asset_sha256":scout.get("asset_sha256"),
                                "issue_codes":scout.get("issue_codes") or [],
                            } if scout else None
                            target["failure_assessment"]=applied
                            if applied.get("ledger_repair_authorized"):
                                target["status"]="scout_repair"
                            save_queue(ep,qq)
                    batch_repair_arbiter.write_batch_decision(ep,contract["batch_id"],decisions)
                else:
                    # Batch transport failure is technical. Record it, then immediately fall back
                    # to the already-proven single-frame worker without consuming content repair.
                    for original in items:
                        item=byid[original["id"]]
                        ledger_tech_fail(ep,item,"BATCH_TRANSPORT_FAILURE",str(result.get("error") or "batch failed"))
                        item["status"]="tech_failed";item["last_error"]=str(result.get("error") or "batch failed")[-1200:]
                    save_queue(ep,q)
                    for original in items:
                        q=load_queue(ep);item={x["id"]:x for x in q.get("items") or []}[original["id"]]
                        ok,res,msg=_fallback_single(ep,item,timeout,codex)
                        q=load_queue(ep);item={x["id"]:x for x in q.get("items") or []}[original["id"]]
                        if ok:
                            item["status"]="generated";item["output_path"]=Path(res["output"]).resolve().relative_to(ROOT).as_posix()
                            item["completed_at"]=now();item["last_error"]=None;item["batch_fallback"]="single"
                        else:
                            item["status"]="tech_failed";item["last_error"]=str(msg)[-1200:]
                        perf["fallback_single_frames"]+=1
                        save_queue(ep,q)
                    q=load_queue(ep);_update_batch_row(q,contract["batch_id"],status="fallback_single",completed_at=now(),
                        returned_count=result.get("returned_count"),error=str(result.get("error") or "batch failed")[-1000:])
                save_queue(ep,q)
                perf["batches"].append({
                    "batch_id":contract["batch_id"],"planned_count":contract["planned_count"],
                    "returned_count":result.get("returned_count"),"ok":supported,
                    "elapsed_seconds":result.get("elapsed_seconds"),"fallback":not supported
                })
    perf["completed_at"]=now();perf["batch_count"]=len(perf["batches"])
    write_json(ep/"meta/batch-runtime-performance.json",perf)
    q=load_queue(ep)
    failed=[x for x in q.get("items") or [] if x.get("status") in {"blocked","tech_failed"}]
    print(json.dumps(perf,ensure_ascii=False,indent=2))
    return 4 if failed else 0

def self_test():
    assert batch_runtime_config.images_per_batch()==5
    assert batch_repair_arbiter is not None
    print("BATCH SCHEDULER V2.4 PHASE3 SELF-TEST PASS")
if __name__=="__main__":self_test()
