#!/usr/bin/env python3
from __future__ import annotations
import shutil, subprocess, tempfile, time
from pathlib import Path

from canvas_normalize import NormalizeError, normalize, read_canvas
import batch_prompt_compiler
import batch_result_mapper
import batch_runtime_config
import codex_subscription_image as single_backend
import codex_logical_batch_worker
import frame_contract
import image_model_policy
import image_provider_router
import openai_images_provider
import openai_batch_prompt_compiler
import provider_capability
import runtime_trace

ROOT=Path(__file__).resolve().parents[2]

class BatchBackendError(RuntimeError):
    pass

def _shared_refs(items:list[dict])->list[Path]:
    counts={}
    for item in items:
        for ref in item.get("references") or []:
            path=str(ref.get("path") or "")
            if path: counts[path]=counts.get(path,0)+1
    ordered=sorted(counts,key=lambda p:(-counts[p],p))[:2]
    out=[]
    for raw in ordered:
        p=(ROOT/raw).resolve()
        if single_backend.valid_image(p): out.append(p)
    return out

def _invoke_codex_once(ep:Path,contract:dict,prompt_text:str,refs:list[Path],timeout:int,codex_raw:str|None,log:Path)->tuple[list[dict],float]:
    codex=single_backend.resolve_codex(codex_raw)
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix="story-os-batch-image-") as raw_dir:
        workdir=Path(raw_dir)
        local_refs=[]
        for idx,source in enumerate(refs,1):
            ext=source.suffix.lower() if source.suffix.lower() in {".png",".jpg",".jpeg"} else ".png"
            target=workdir/f"reference-{idx:02d}{ext}"
            shutil.copy2(source,target); local_refs.append(target)
        cmd=single_backend.command_prefix(codex)+[
            "exec","--skip-git-repo-check","--ephemeral","--enable","image_generation",
            "-c",'model_reasoning_effort="low"','-s',"workspace-write","-C",str(workdir),"--json"
        ]
        for ref in local_refs: cmd.extend(["-i",str(ref)])
        cmd.append("-")
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open("w",encoding="utf-8",newline="\n") as h:
            try:
                done=subprocess.run(cmd,input=prompt_text,text=True,stdout=h,stderr=subprocess.STDOUT,
                    timeout=timeout,check=False)
            except subprocess.TimeoutExpired as exc:
                raise BatchBackendError(f"TIMEOUT: batch image worker timeout after {timeout}s; log={log}") from exc
        if done.returncode!=0:
            tail=log.read_text(encoding="utf-8",errors="replace")[-6000:] if log.is_file() else ""
            code=image_model_policy.classify_backend_error(tail)
            raise BatchBackendError(f"{code or 'BATCH_IMAGE_BACKEND_ERROR'}: rc={done.returncode}; log={log}")
        mapped=batch_result_mapper.map_outputs(workdir,contract)
        persisted=[]
        raw_root=ep/"media/raw";raw_root.mkdir(parents=True,exist_ok=True)
        stamp=int(time.time())
        for row in mapped:
            frame=int(row["frame"])
            dst=raw_root/f"{frame:02d}-{contract['batch_id'].lower()}-{stamp}.png"
            shutil.copy2(row["path"],dst)
            persisted.append({**row,"path":dst})
    return persisted,round(time.monotonic()-started,2)

def _invoke_openai_native_n(ep:Path,contract:dict,prompt_text:str,refs:list[Path],timeout:int,model:str,quality:str,width:int,height:int)->tuple[list[dict],float,dict]:
    started=time.monotonic()
    raw_root=ep/"media/raw";raw_root.mkdir(parents=True,exist_ok=True)
    stamp=int(time.time())
    raw_paths=[]
    for row in contract["frames"]:
        frame=int(row["frame"])
        raw_paths.append(raw_root/f"{frame:02d}-{contract['batch_id'].lower()}-{stamp}.png")
    evidence=openai_images_provider.generate_native_batch(
        prompt=prompt_text,references=refs,count=int(contract["planned_count"]),model=model,quality=quality,
        release_width=width,release_height=height,timeout=timeout,raw_paths=raw_paths)
    persisted=[]
    for row,path in zip(contract["frames"],raw_paths):
        persisted.append({
            "output_index":int(row["output_index"]),
            "frame":str(row["frame"]),
            "queue_item_id":row["queue_item_id"],
            "path":path,
            "frame_contract_sha256":row["frame_contract_sha256"],
        })
    return persisted,round(time.monotonic()-started,2),evidence

def execute_batch(ep:Path,contract:dict,items:list[dict],timeout:int,codex:str|None)->dict:
    if not items: raise BatchBackendError("empty batch")
    expected=int(contract["planned_count"])
    if expected!=len(items): raise BatchBackendError("batch contract/item count mismatch")
    if expected>batch_runtime_config.images_per_batch(): raise BatchBackendError("batch exceeds configured images_per_batch")
    models={str(x.get("model") or image_model_policy.for_episode(ep)["model"]) for x in items}
    qualities={str(x.get("quality") or image_model_policy.for_episode(ep)["quality"]) for x in items}
    if len(models)!=1 or len(qualities)!=1:
        raise BatchBackendError("batch frames must share image model and quality")
    model=next(iter(models));quality=next(iter(qualities))
    width,height,aspect=read_canvas(ep)
    refs=_shared_refs(items)
    route=image_provider_router.select_for_batch(expected,has_references=bool(refs))
    if route["provider"]=="codex_subscription" and route.get("logical_batch"):
        logical=codex_logical_batch_worker.execute(ep,contract,items,timeout,codex)
        logical["batch_id"]=contract["batch_id"]
        logical["provider_evidence"]=logical.get("logical_batch_evidence") or {}
        for result in (logical.get("results") or {}).values():
            payload=result.get("payload")
            if isinstance(payload,dict):
                payload["batch_id"]=contract["batch_id"]
                payload["provider_runtime"]={
                    "provider":"codex_subscription",
                    "transport":"codex_subscription_parallel_fanout",
                    "logical_batch":True,
                    "native_multi_image":False,
                    "single_http_request":False,
                    "requested_count":expected,
                    "returned_count":int(logical.get("returned_count") or 0),
                    "max_inflight_used":(logical.get("logical_batch_evidence") or {}).get("max_inflight_used"),
                    "api_key_required":False,
                }
        return logical

    compiler = openai_batch_prompt_compiler if route["provider"]=="openai_images_api" else batch_prompt_compiler
    compiled=compiler.compile_batch(
        ep,contract,{x["id"]:x for x in items},model=model,quality=quality,size=f"{width}x{height}",
        reference_names=[p.name for p in refs])
    log=ep/"meta/image-workers"/f"{contract['batch_id'].lower()}.jsonl"
    span=runtime_trace.start_span(ep,f"batch.generate.{contract['batch_id']}",category="batch_generation",
        attrs={"batch_id":contract["batch_id"],"planned_count":expected,"model":model,"quality":quality,
               "provider":route["provider"],"execution_mode":route["execution_mode"]})
    t0=time.monotonic()
    provider_evidence={}
    try:
        if route["provider"]=="openai_images_api":
            raw_rows,elapsed,provider_evidence=_invoke_openai_native_n(
                ep,contract,compiled["text"],refs,timeout,model,quality,width,height)
            backend_name="openai_images_api_native_n"
        else:
            raw_rows,elapsed=_invoke_codex_once(ep,contract,compiled["text"],refs,timeout,codex,log)
            backend_name="codex_subscription_batch"
            provider_evidence={
                "provider":"codex_subscription",
                "transport":"codex_subscription_batch",
                "native_multi_image":True,
                "single_http_request":False,
                "requested_count":expected,
                "returned_count":len(raw_rows),
            }
        results={}
        packages={x["frame"]:x for x in compiled["packages"]}
        item_by_id={x["id"]:x for x in items}
        for row in raw_rows:
            frame=int(row["frame"]);item=item_by_id[row["queue_item_id"]]
            out=ep/"media/candidates/scheduled"/f"{frame:02d}-{item['id']}-a{max(1,int(item.get('attempts') or 1))}.png"
            out.parent.mkdir(parents=True,exist_ok=True)
            route_name=backend_name
            receipt_data=provider_capability.inspect(
                row["path"],width,height,model=model,route=route_name,frame=frame)
            receipt_data["provider_request"]={
                "batch_id":contract["batch_id"],
                "provider":provider_evidence.get("provider") or route["provider"],
                "transport":provider_evidence.get("transport") or backend_name,
                "request_id":provider_evidence.get("request_id"),
                "single_http_request":bool(provider_evidence.get("single_http_request")),
                "native_multi_image":bool(provider_evidence.get("native_multi_image")),
                "requested_count":int(provider_evidence.get("requested_count") or expected),
                "returned_count":int(provider_evidence.get("returned_count") or len(raw_rows)),
                "provider_request_size":provider_evidence.get("provider_request_size"),
                "secrets_persisted":False,
            }
            receipt=provider_capability.write_receipt(ep,frame,receipt_data)
            try:
                norm=normalize(row["path"],out,width,height)
            except NormalizeError as exc:
                raise BatchBackendError(f"{exc.code}: frame={frame:02d}; raw={row['path']}") from exc
            receipt_path=Path(receipt["path"])
            if not receipt_path.is_absolute(): receipt_path=ROOT/receipt_path
            receipt=provider_capability.finalize_receipt(receipt_path,norm,out)
            fc=frame_contract.provenance(ep,frame)
            results[item["id"]]={
                "returncode":0,"stdout":"","output":out,"log":log,
                "payload":{
                    "ok":True,"backend":backend_name,"batch_id":contract["batch_id"],"frame":f"{frame:02d}",
                    "raw_output":str(row["path"]),"output":str(out),
                    "provider_size":provider_evidence.get("provider_request_size") or [width,height],
                    "target_size":[width,height],"aspect_ratio":aspect,"normalization":norm,
                    "provider_receipt":{k:v for k,v in receipt.items() if k!="receipt"},
                    "provider_capability":receipt.get("receipt"),
                    "frame_contract":{"contract_sha256":fc["contract_sha256"]} if fc else None,
                    "image_model":{"model":model,"quality":quality,"strict_model":False,
                        "enforcement":"runtime_request_to_provider_adapter_contract",
                        "provider_attestation":bool(provider_evidence.get("request_id"))},
                    "provider_runtime":provider_evidence,
                    "elapsed_seconds":elapsed,
                },
                "prompt_package":packages.get(f"{frame:02d}"),
            }
        runtime_trace.end_span(ep,span,name=f"batch.generate.{contract['batch_id']}",category="batch_generation",
            status="PASS",started_monotonic=t0,
            attrs={"returned_count":len(results),"batch_id":contract["batch_id"],"provider":route["provider"]})
        return {
            "ok":True,"batch_id":contract["batch_id"],"requested_count":expected,"returned_count":len(results),
            "elapsed_seconds":elapsed,"results":results,"log":log,"provider":route["provider"],
            "transport":provider_evidence.get("transport") or backend_name,
            "native_multi_image":bool(provider_evidence.get("native_multi_image")),
            "single_http_request":bool(provider_evidence.get("single_http_request")),
            "provider_evidence":provider_evidence,
        }
    except Exception as exc:
        runtime_trace.end_span(ep,span,name=f"batch.generate.{contract['batch_id']}",category="batch_generation",
            status="FAILED",started_monotonic=t0,
            attrs={"error":str(exc),"batch_id":contract["batch_id"],"provider":route["provider"]})
        return {
            "ok":False,"batch_id":contract["batch_id"],"requested_count":expected,"returned_count":0,
            "elapsed_seconds":round(time.monotonic()-t0,2),"results":{},"log":log,"error":str(exc),
            "provider":route["provider"],"transport":route["execution_mode"],
            "native_multi_image":bool(route.get("native_multi_image")),"single_http_request":False,
        }

def self_test():
    assert batch_runtime_config.images_per_batch()==5
    assert codex_logical_batch_worker is not None
    print("BATCH IMAGE WORKER V2.4.2 CODEX LOGICAL BATCH SELF-TEST PASS")

if __name__=="__main__": self_test()
