#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 6 bounded image scheduler.

Only the expensive image backend runs concurrently.
All Production Ledger mutations are committed sequentially by the scheduler main thread.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import subprocess
import sys
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

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
QUEUE_REL = Path("meta/production-queue.json")
MAX_SUPPORTED_WORKERS = 3
READY_LEDGER_STATES = {"ORIGINAL_READY","REPAIR_READY","PASSED","LOCKED"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict):raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path,data:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")


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


def run(cmd:list[object])->subprocess.CompletedProcess[str]:
    return subprocess.run([str(x) for x in cmd],cwd=ROOT,check=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")


def load_queue(ep:Path)->dict:
    p=ep/QUEUE_REL
    if not p.is_file():
        return {"schema_version":1,"created_at":now(),"updated_at":now(),"max_parallel":3,"items":[],"waves":[]}
    return read_json(p)


def save_queue(ep:Path,q:dict)->None:
    q["updated_at"]=now()
    write_json(ep/QUEUE_REL,q)


def ledger(ep:Path)->dict:
    p=ep/"meta/production-ledger.json"
    return read_json(p) if p.is_file() else {}


def ledger_state(ep:Path,frame:int)->str:
    return str((((ledger(ep).get("frames") or {}).get(f"{frame:02d}") or {}).get("status") or "PENDING"))


def risk_priority(ep:Path,frame:int,scope:str)->int:
    c=frame_contract.compile_frame(ep,frame,write_cache=True)
    d=c["hash_material"]["frame_directive"]
    mode=str(d.get("frame_mode") or "")
    role=str(d.get("narrative_role") or "")
    impact=int(d.get("impact_level") or 0)
    base=impact*20
    mode_bonus={"climax_impact":40,"anomaly_amplified":35,"anomaly_reveal":25,"payoff":20,"normal_record":0}.get(mode,10)
    role_bonus={"climax":30,"payoff":22,"reveal":18,"escalation":15,"evidence":8,"setup":0,"transition":0,"residue":5}.get(role,0)
    scope_bonus=50 if scope=="visual_lock" else 0
    return base+mode_bonus+role_bonus+scope_bonus


def directive_dependency(ep:Path,frame:int)->list[int]:
    d=frame_contract.compile_frame(ep,frame,write_cache=True)["hash_material"]["frame_directive"]
    raw=d.get("escalation_from")
    try:
        n=int(raw)
        return [n] if 1<=n<frame else []
    except Exception:
        return []


def contract_references(ep:Path,frame:int)->list[dict]:
    c=frame_contract.compile_frame(ep,frame,write_cache=True)
    out=[]
    master=character_visual_contract.pixel_master_reference(ep)
    if master:out.append({"path":master["path"],"role":master["role"],"kind":"identity"})
    for row in c["hash_material"].get("references") or []:
        if not isinstance(row,dict):
            continue
        raw=row.get("path");kind=row.get("kind");role=row.get("role") or "continuity"
        if not raw or kind not in {"identity","prop","location","capture_style"}:
            continue
        if row.get("decision") not in {None,"pass","passed"}:
            continue
        try:
            p=repo_file(str(raw))
        except Exception:
            continue
        candidate={"path":repo_rel(p),"role":str(role),"kind":str(kind)}
        if not any(x.get("path")==candidate["path"] for x in out):out.append(candidate)
        if len(out)>=2:
            break
    return out


def init_queue(ep:Path,force:bool=False)->dict:
    p=ep/QUEUE_REL
    if p.exists() and not force:return read_json(p)
    q={"schema_version":1,"created_at":now(),"updated_at":now(),"max_parallel":3,"adaptive_parallel":3,"stable_waves":0,"items":[],"waves":[]}
    save_queue(ep,q);return q


def add_item(ep:Path,*,frame:int,kind:str,prompt_file:Path,scope:str,references:list[dict],capture_id:str,model:str,depends_on:list[int],replace:bool=False)->dict:
    q=load_queue(ep)
    key=f"{frame:02d}"
    active=[x for x in q.get("items") or [] if f"{int(x.get('frame')):02d}"==key and x.get("kind")==kind and x.get("status") in {"queued","running","generated","tech_failed"}]
    if active and not replace:
        return active[-1]
    if replace:
        for x in active:x["status"]="superseded"
    contract=frame_contract.provenance(ep,frame)
    item={
        "id":uuid.uuid4().hex[:12],
        "frame":frame,
        "kind":kind,
        "scope":scope,
        "status":"queued",
        "prompt_file":repo_rel(prompt_file),
        "references":references,
        "capture_id":capture_id,
        "model":model,
        "depends_on":sorted(set(int(x) for x in depends_on if int(x)!=frame)),
        "priority":risk_priority(ep,frame,scope),
        "frame_contract":contract,
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
        added.append(add_item(ep,frame=frame,kind="original",prompt_file=prompt,scope="visual_lock",references=contract_references(ep,frame),capture_id=f"visual-lock-{frame:02d}",model=image_model_policy.for_episode(ep)["model"],depends_on=[int(x) for x in row.get("depends_on") or []],replace=False))
    return {"added":[x["id"] for x in added]}


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
        added.append(add_item(ep,frame=frame,kind="original",prompt_file=prompt,scope="batch",references=contract_references(ep,frame),capture_id=f"batch-{frame:02d}",model=image_model_policy.for_episode(ep)["model"],depends_on=directive_dependency(ep,frame),replace=False))
    return {"added":[x["frame"] for x in added],"skipped":skipped}


def dependency_satisfied(ep:Path,q:dict,dep:int)->bool:
    state=ledger_state(ep,dep)
    if state in READY_LEDGER_STATES:return True
    rows=[x for x in q.get("items") or [] if int(x.get("frame"))==dep and x.get("status")=="generated"]
    return bool(rows)


def ready_items(ep:Path,q:dict)->tuple[list[dict],list[dict]]:
    ready=[];blocked=[]
    for item in q.get("items") or []:
        if item.get("status")!="queued":continue
        deps=[int(x) for x in item.get("depends_on") or []]
        if all(dependency_satisfied(ep,q,x) for x in deps):ready.append(item)
        else:blocked.append(item)
    ready.sort(key=lambda x:(-int(x.get("priority") or 0),int(x["frame"])))
    return ready,blocked


def current_contract_sha(ep:Path,frame:int)->str:
    p=frame_contract.provenance(ep,frame)
    if not p:raise ValueError(f"frame {frame:02d} missing Frame Contract provenance")
    return p["contract_sha256"]


def ledger_begin(ep:Path,item:dict)->tuple[bool,str]:
    prompt=repo_file(item["prompt_file"])
    cmd=[sys.executable,SYSTEM/"production_ledger.py","begin",ep,"--frame",f"{int(item['frame']):02d}","--kind",item["kind"],"--prompt-file",prompt,"--capture-id",item["capture_id"],"--model",item.get("model") or "default","--notes",f"phase6 scheduler item={item['id']} scope={item['scope']}"]
    for ref in item.get("references") or []:
        cmd += ["--reference",f"{ROOT/ref['path']}::{ref['role']}::{ref['kind']}"]
    cp=run(cmd)
    return cp.returncode==0,cp.stdout


def backend_worker(ep:Path,item:dict,timeout:int,codex:str|None)->dict:
    # Warm Python pool: reuse scheduler/module state, never cross-frame Codex conversation state.
    return image_worker_pool.execute(ep,item,timeout,codex)


def ledger_success(ep:Path,item:dict,result:dict)->tuple[bool,str]:
    returned=((result.get("payload") or {}).get("frame_contract") or {}).get("contract_sha256")
    current=current_contract_sha(ep,int(item["frame"]))
    if returned and str(returned).lower()!=current.lower():
        return False,f"backend frame contract drift returned={returned} current={current}"
    cp=run([sys.executable,SYSTEM/"production_ledger.py","success",ep,"--frame",f"{int(item['frame']):02d}","--path",result["output"]])
    return cp.returncode==0,cp.stdout


def ledger_tech_fail(ep:Path,item:dict,code:str,message:str)->None:
    run([sys.executable,SYSTEM/"production_ledger.py","tech-fail",ep,"--frame",f"{int(item['frame']):02d}","--code",code,"--message",message[:1000]])


def classify_error(text:str)->str:
    model_code=image_model_policy.classify_backend_error(text)
    if model_code:return model_code
    low=text.lower()
    if "429" in low:return "RATE_LIMIT_429"
    if "timeout" in low:return "TIMEOUT"
    if "500" in low or "502" in low or "503" in low or "5xx" in low:return "BACKEND_5XX"
    if "contract" in low and "drift" in low:return "CONTRACT_DRIFT"
    return "IMAGE_BACKEND_ERROR"


def run_scheduler(ep:Path,max_workers:int,timeout:int,codex:str|None)->int:
    requested=max(1,min(MAX_SUPPORTED_WORKERS,int(max_workers)))
    q=load_queue(ep)
    cap=max(1,min(requested,int(q.get("adaptive_parallel") or requested)))
    stable=int(q.get("stable_waves") or 0)
    event_no=len(q.get("waves") or [])
    inflight={}
    review_futures={}
    review_pool=cf.ThreadPoolExecutor(max_workers=1,thread_name_prefix="story-os-rolling-review")

    def commit_review(fut,item_id):
        try:
            review=fut.result()
        except Exception as exc:
            review={"decision":"UNCERTAIN","reason":str(exc)}
        qq=load_queue(ep)
        byid={x["id"]:x for x in qq.get("items") or []}
        item=byid.get(item_id)
        if not item:
            return
        item["rolling_review"]=review
        if review.get("decision")=="REPAIR_NOW" and item.get("status")=="generated":
            cp=run([sys.executable,SYSTEM/"production_ledger.py","review",ep,"--frame",f"{int(item['frame']):02d}","--decision","repair","--notes","rolling pre-final obvious defect"])
            if cp.returncode==0:
                item["status"]="scout_repair"
            else:
                item["last_error"]="rolling review repair handoff failed: "+cp.stdout[-1000:]
        save_queue(ep,qq)

    with cf.ThreadPoolExecutor(max_workers=requested,thread_name_prefix="story-os-image") as pool:
        while True:
            for fut,item_id in list(review_futures.items()):
                if fut.done():
                    commit_review(fut,item_id)
                    review_futures.pop(fut,None)

            q=load_queue(ep)
            ready,blocked=ready_items(ep,q)
            running_ids={x["id"] for x in inflight.values()}
            ready=[x for x in ready if x["id"] not in running_ids]

            while ready and len(inflight)<cap:
                item=ready.pop(0)
                ok,msg=ledger_begin(ep,item)
                q=load_queue(ep)
                byid={x["id"]:x for x in q.get("items") or []}
                current=byid[item["id"]]
                if not ok:
                    current["status"]="blocked"
                    current["last_error"]="ledger begin failed: "+msg[-1200:]
                    save_queue(ep,q)
                    continue
                current["status"]="running"
                current["attempts"]=int(current.get("attempts") or 0)+1
                current["started_at"]=now()
                save_queue(ep,q)
                fut=pool.submit(backend_worker,ep,current,timeout,codex)
                inflight[fut]=current
                q=load_queue(ep)
                ready,_=ready_items(ep,q)
                ready=[x for x in ready if x["id"] not in {y["id"] for y in inflight.values()}]

            if not inflight:
                break

            done,_=cf.wait(set(inflight),return_when=cf.FIRST_COMPLETED)
            for fut in done:
                begun=inflight.pop(fut)
                try:
                    res=fut.result()
                except Exception as exc:
                    res={"returncode":99,"stdout":str(exc),"payload":None,"output":None,"log":None,"attempt":begun.get("attempts",1),"scout":None}
                q=load_queue(ep)
                byid={x["id"]:x for x in q.get("items") or []}
                item=byid[begun["id"]]
                ok=False
                msg=res.get("stdout") or ""
                if res.get("returncode")==0 and res.get("output") and Path(res["output"]).is_file():
                    ok,msg=ledger_success(ep,item,res)
                event_no+=1
                if ok:
                    scout=res.get("scout") or {}
                    decision=scout.get("decision")
                    item["output_path"]=repo_rel(Path(res["output"]))
                    try:
                        item["lineage"]=asset_lineage.record(ep,int(item["frame"]),Path(res["output"]),kind=str(item.get("kind") or "original"),reason=f"scheduler:{item.get('scope')}",source_item_id=item.get("id"),frame_contract_sha256=current_contract_sha(ep,int(item["frame"])))
                    except Exception as exc:
                        item["lineage_warning"]=str(exc)
                    item["log_path"]=repo_rel(Path(res["log"]))
                    item["completed_at"]=now()
                    item["last_error"]=None
                    item["prompt_package"]=res.get("prompt_package")
                    item["scout"]={"decision":decision,"risk_level":scout.get("risk_level"),"asset_sha256":scout.get("asset_sha256")} if scout else None
                    if decision=="REPAIR_NOW":
                        cp=run([sys.executable,SYSTEM/"production_ledger.py","review",ep,"--frame",f"{int(item['frame']):02d}","--decision","repair","--notes","Phase7 Fast Scout obvious defect"])
                        item["status"]="scout_repair" if cp.returncode==0 else "blocked"
                        if cp.returncode!=0:
                            item["last_error"]="scout repair handoff failed: "+cp.stdout[-1200:]
                    else:
                        item["status"]="generated"
                        if int(item.get("priority") or 0)>=90 and res.get("output"):
                            rf=review_pool.submit(rolling_frame_review.review,ep,int(item["frame"]),Path(res["output"]),codex,min(240,max(60,timeout)))
                            review_futures[rf]=item["id"]
                    stable+=1
                    if stable>=2 and cap<requested:
                        cap+=1
                        stable=0
                else:
                    code=classify_error(msg)
                    ledger_tech_fail(ep,item,code,msg or "image backend failed")
                    item["status"]="tech_failed"
                    item["completed_at"]=now()
                    item["last_error"]=msg[-1600:]
                    cap=max(1,cap-1)
                    stable=0
                q["adaptive_parallel"]=cap
                q["stable_waves"]=stable
                q.setdefault("waves",[]).append({"event":event_no,"mode":"continuous_first_completed","at":now(),"frame":item["frame"],"status":item["status"],"inflight_after":len(inflight),"next_parallel":cap,"elapsed_seconds":((res.get("payload") or {}).get("elapsed_seconds"))})
                save_queue(ep,q)

    for fut,item_id in list(review_futures.items()):
        commit_review(fut,item_id)
    review_pool.shutdown(wait=True)

    q=load_queue(ep)
    ready,blocked=ready_items(ep,q)
    tech=[x for x in q.get("items") or [] if x.get("status")=="tech_failed"]
    queued=[x for x in q.get("items") or [] if x.get("status")=="queued"]
    hard_blocked=[x for x in q.get("items") or [] if x.get("status")=="blocked"]
    scout_repair=[x for x in q.get("items") or [] if x.get("status")=="scout_repair"]
    generated=[x for x in q.get("items") or [] if x.get("status")=="generated"]
    scout_errors=frame_scout.audit(ep,write_summary=True) if frame_scout.required(ep) else []
    summary={"scheduler_mode":"continuous_first_completed","generated":len(generated),"tech_failed":len(tech),"dependency_blocked":len(blocked),"hard_blocked":len(hard_blocked),"scout_repair":len(scout_repair),"scout_audit_errors":scout_errors,"queued":len(queued),"adaptive_parallel":q.get("adaptive_parallel"),"events":q.get("waves") or [],"reported_at":now()}
    write_json(ep/"meta/image-scheduler-performance.json",summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if tech or queued or hard_blocked:
        return 4
    if scout_repair or scout_errors:
        return 5
    return 0


def retry_tech(ep:Path)->dict:
    q=load_queue(ep);count=0
    for item in q.get("items") or []:
        if item.get("status")=="tech_failed":
            item["status"]="queued";item["last_error"]=None;count+=1
    save_queue(ep,q);return {"requeued":count}


def self_test()->None:
    assert MAX_SUPPORTED_WORKERS==3
    assert classify_error("429 Too Many Requests")=="RATE_LIMIT_429"
    assert classify_error("worker timeout")=="TIMEOUT"
    assert classify_error("unknown model")=="MODEL_UNAVAILABLE"
    assert image_worker_pool.CODEX_SESSION_REUSE is False
    assert rolling_frame_review.VALID == {"PASS_PREVIEW","REPAIR_NOW","UNCERTAIN"}
    print("IMAGE SCHEDULER V2.1 PHASE6 SELF-TEST PASS")


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("add");p.add_argument("episode_dir");p.add_argument("--frame",type=int,required=True);p.add_argument("--kind",choices=["original","repair"],default="original");p.add_argument("--scope",choices=["visual_lock","batch","repair"],default="batch");p.add_argument("--prompt-file",required=True);p.add_argument("--reference",action="append",default=[]);p.add_argument("--capture-id");p.add_argument("--model");p.add_argument("--depends-on",action="append",default=[]);p.add_argument("--replace",action="store_true")
    p=sub.add_parser("import-visual-lock");p.add_argument("episode_dir");p.add_argument("--prompt-dir",required=True)
    p=sub.add_parser("import-batch");p.add_argument("episode_dir");p.add_argument("--prompt-dir",required=True)
    p=sub.add_parser("plan");p.add_argument("episode_dir")
    p=sub.add_parser("run");p.add_argument("episode_dir");p.add_argument("--max-workers",type=int,default=3);p.add_argument("--timeout",type=int,default=600);p.add_argument("--codex")
    p=sub.add_parser("retry-tech");p.add_argument("episode_dir")
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
            row=add_item(ep,frame=a.frame,kind=a.kind,prompt_file=prompt,scope=a.scope,references=refs,capture_id=a.capture_id or f"scheduler-{a.frame:02d}",model=a.model or image_model_policy.for_episode(ep)["model"],depends_on=deps,replace=a.replace)
            print(json.dumps(row,ensure_ascii=False,indent=2));return 0
        if a.cmd=="import-visual-lock":print(json.dumps(import_visual_lock(ep,Path(a.prompt_dir).resolve()),ensure_ascii=False,indent=2));return 0
        if a.cmd=="import-batch":print(json.dumps(import_batch(ep,Path(a.prompt_dir).resolve()),ensure_ascii=False,indent=2));return 0
        if a.cmd=="plan":
            q=load_queue(ep);ready,blocked=ready_items(ep,q)
            print(json.dumps({"ready":[{"frame":x["frame"],"priority":x["priority"],"scope":x["scope"]} for x in ready],"blocked":[{"frame":x["frame"],"depends_on":x["depends_on"]} for x in blocked],"adaptive_parallel":q.get("adaptive_parallel",3)},ensure_ascii=False,indent=2));return 0
        if a.cmd=="run":return run_scheduler(ep,a.max_workers,a.timeout,a.codex)
        if a.cmd=="retry-tech":print(json.dumps(retry_tech(ep),ensure_ascii=False,indent=2));return 0
        print((ep/QUEUE_REL).read_text(encoding="utf-8") if (ep/QUEUE_REL).is_file() else "{}");return 0
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print("IMAGE SCHEDULER ERROR:",exc);return 3


if __name__=="__main__":raise SystemExit(main())
