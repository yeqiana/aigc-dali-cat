#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

from canvas_normalize import NormalizeError, normalize, read_canvas
import batch_prompt_compiler
import batch_result_mapper
import batch_runtime_config
import codex_subscription_image as single_backend
import frame_contract
import image_model_policy
import provider_capability
import runtime_trace

ROOT=Path(__file__).resolve().parents[2]

class BatchBackendError(RuntimeError):
    pass

def _shared_refs(items:list[dict])->list[Path]:
    # Prefer references shared by the most frames. Keep the same max-2 reference budget
    # as the current formal single-frame backend.
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

def _invoke_once(ep:Path,contract:dict,items:list[dict],prompt_text:str,refs:list[Path],timeout:int,codex_raw:str|None,log:Path)->tuple[list[dict],float]:
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
        # Copy mapped raw files out before TemporaryDirectory disappears.
        persisted=[]
        raw_root=ep/"media/raw";raw_root.mkdir(parents=True,exist_ok=True)
        stamp=int(time.time())
        for row in mapped:
            frame=int(row["frame"])
            dst=raw_root/f"{frame:02d}-{contract['batch_id'].lower()}-{stamp}.png"
            shutil.copy2(row["path"],dst)
            persisted.append({**row,"path":dst})
    return persisted,round(time.monotonic()-started,2)

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
    width,height,aspect=read_canvas(ep);size=single_backend.provider_size(width,height)
    refs=_shared_refs(items)
    compiled=batch_prompt_compiler.compile_batch(
        ep,contract,{x["id"]:x for x in items},model=model,quality=quality,size=size,
        reference_names=[p.name for p in refs]
    )
    log=ep/"meta/image-workers"/f"{contract['batch_id'].lower()}.jsonl"
    span=runtime_trace.start_span(ep,f"batch.generate.{contract['batch_id']}",category="batch_generation",
        attrs={"batch_id":contract["batch_id"],"planned_count":expected,"model":model,"quality":quality})
    t0=time.monotonic()
    try:
        raw_rows,elapsed=_invoke_once(ep,contract,items,compiled["text"],refs,timeout,codex,log)
        results={}
        packages={x["frame"]:x for x in compiled["packages"]}
        item_by_id={x["id"]:x for x in items}
        for row in raw_rows:
            frame=int(row["frame"]);item=item_by_id[row["queue_item_id"]]
            out=ep/"media/candidates/scheduled"/f"{frame:02d}-{item['id']}-a{max(1,int(item.get('attempts') or 1))}.png"
            out.parent.mkdir(parents=True,exist_ok=True)
            receipt=provider_capability.write_receipt(
                ep,frame,provider_capability.inspect(row["path"],width,height,model=model,route="codex_subscription_batch",frame=frame)
            )
            try:
                norm=normalize(row["path"],out,width,height)
            except NormalizeError as exc:
                raise BatchBackendError(f"{exc.code}: frame={frame:02d}; raw={row['path']}") from exc
            receipt_path=Path(receipt["path"])
            if not receipt_path.is_absolute(): receipt_path=ROOT/receipt_path
            receipt=provider_capability.finalize_receipt(receipt_path,norm,out)
            fc=frame_contract.provenance(ep,frame)
            results[item["id"]]={
                "returncode":0,
                "stdout":"",
                "output":out,
                "log":log,
                "payload":{
                    "ok":True,
                    "backend":"codex_subscription_batch",
                    "batch_id":contract["batch_id"],
                    "frame":f"{frame:02d}",
                    "raw_output":str(row["path"]),
                    "output":str(out),
                    "provider_size":size,
                    "target_size":[width,height],
                    "aspect_ratio":aspect,
                    "normalization":norm,
                    "provider_receipt":{k:v for k,v in receipt.items() if k!="receipt"},
                    "provider_capability":receipt.get("receipt"),
                    "frame_contract":{"contract_sha256":fc["contract_sha256"]} if fc else None,
                    "image_model":{
                        "model":model,"quality":quality,"strict_model":False,
                        "enforcement":"runtime_request_to_batch_worker_contract",
                        "provider_attestation":False,
                    },
                    "elapsed_seconds":elapsed,
                },
                "prompt_package":packages.get(f"{frame:02d}"),
            }
        runtime_trace.end_span(ep,span,name=f"batch.generate.{contract['batch_id']}",category="batch_generation",
            status="PASS",started_monotonic=t0,attrs={"returned_count":len(results),"batch_id":contract["batch_id"]})
        return {"ok":True,"batch_id":contract["batch_id"],"requested_count":expected,"returned_count":len(results),
            "elapsed_seconds":elapsed,"results":results,"log":log}
    except Exception as exc:
        runtime_trace.end_span(ep,span,name=f"batch.generate.{contract['batch_id']}",category="batch_generation",
            status="FAILED",started_monotonic=t0,attrs={"error":str(exc),"batch_id":contract["batch_id"]})
        return {"ok":False,"batch_id":contract["batch_id"],"requested_count":expected,"returned_count":0,
            "elapsed_seconds":round(time.monotonic()-t0,2),"results":{},"log":log,"error":str(exc)}

def self_test():
    assert batch_runtime_config.images_per_batch()==5
    print("BATCH IMAGE WORKER SELF-TEST PASS")
if __name__=="__main__": self_test()
