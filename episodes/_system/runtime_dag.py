#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, concurrent.futures as cf, json, subprocess, sys, time
from pathlib import Path

import quota_observability
import execution_capsule
import provisional_release
import scoped_codex_worker
import workflow_performance as perf
import workflow_step_protocol as proto

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=Path(__file__).resolve().parent
DAG_FILE=ROOT/"runtimes/runtime-dag.json"
STAGES=("IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED")

def run(cmd):
    return subprocess.run([str(x) for x in cmd],cwd=ROOT,check=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
def load_dag():
    d=json.loads(DAG_FILE.read_text(encoding="utf-8-sig"))
    if d.get("schema_version")!=1: raise ValueError("invalid runtime-dag schema")
    return d
def state(ep):
    p=ep/"meta/episode-state.json"
    if not p.is_file(): return None
    return json.loads(p.read_text(encoding="utf-8-sig")).get("current_state")
def stage_at_least(cur,target):
    return cur in STAGES and target in STAGES and STAGES.index(cur)>=STAGES.index(target)
def validate_target(ep,target):
    outputs=[]
    for script in ("validate_episode.py","machine_gate.py","evidence_gate.py"):
        cp=run([sys.executable,SYSTEM/script,ep,"--target",target]); outputs.append(cp.stdout)
        if cp.returncode!=0: return False,"\n".join(outputs)[-5000:]
    return True,"PASS"
def checkpoint(ep,step,status,elapsed,note,attempt=1,input_hash=None,output_hash=None):
    cmd=[sys.executable,SYSTEM/"runtime_checkpoint.py","record-step",ep,"--step",step,"--status",status,"--attempt",str(attempt),"--finished-at",proto.now(),"--note",note]
    if input_hash: cmd += ["--input-hash",input_hash]
    if output_hash: cmd += ["--output-hash",output_hash]
    run(cmd)

def spec_rows():
    d=load_dag(); rows=[]
    for x in d["steps"]:
        rows.append(proto.StepSpec(
            step_id=x["id"],executor=x["executor"],depends_on=tuple(x.get("depends_on") or []),
            covers=tuple(x.get("covers") or []),target_state=x.get("target_state"),
            evidence_paths=tuple(x.get("evidence_paths") or []),expensive=bool(x.get("expensive"))))
    return rows

def plan(ep):
    cur=state(ep); saved=proto.load_state(ep)
    out=[]
    for s in spec_rows():
        row={"step":s.step_id,"executor":s.executor,"depends_on":list(s.depends_on),"target_state":s.target_state,"covers":list(s.covers),"current_state":cur}
        if s.target_state and stage_at_least(cur,s.target_state):
            ok,_=validate_target(ep,s.target_state); row["action"]="REUSE" if ok else "VERIFY_OR_REPAIR"
        else:
            row["action"]="RUN"
        prev=(saved.get("steps") or {}).get(s.step_id)
        if prev: row["previous"]=prev
        out.append(row)
    return {"current_state":cur,"steps":out}

def execute(ep,codex=None,timeout=7200,run_id=None):
    dag=load_dag(); specs=spec_rows(); total_start=time.monotonic()
    provisional_future=None
    background=cf.ThreadPoolExecutor(max_workers=1,thread_name_prefix="story-os-release-prep")
    for s in specs:
        cur=state(ep)
        prior=(proto.load_state(ep).get("steps") or {}).get(s.step_id) or {}
        attempt=int(prior.get("attempt") or 0)+1
        input_hash=proto.evidence_hash(ep,["meta/runtime-request.json","meta/episode-state.json",*s.evidence_paths])
        if s.target_state and stage_at_least(cur,s.target_state):
            ok,msg=validate_target(ep,s.target_state)
            if ok:
                out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
                res=proto.StepResult(s.step_id,"REUSED",attempt,proto.now(),proto.now(),0.0,input_hash,out_hash,"target already valid",0)
                proto.save_result(ep,res); checkpoint(ep,s.step_id,"REUSED",0,"target already valid",attempt,input_hash,out_hash)
                if run_id: perf.record_step(ep,run_id,s.step_id,"REUSED",0,"target already valid")
                continue
        started_at=proto.now(); t0=time.monotonic(); rc=0; note=""
        if s.executor=="machine_incremental_plan":
            cp=run([sys.executable,SYSTEM/"incremental_closure.py","plan",ep,"--json"]); rc=cp.returncode; note=cp.stdout[-3000:]
        elif s.executor=="scoped_codex":
            execution_capsule.compile_capsule(ep,s.step_id,write=True)
            if s.step_id=="RELEASE" and provisional_future is not None:
                try:
                    prep=provisional_future.result(timeout=120)
                    note=f"provisional_release={prep}"
                except Exception as exc:
                    note=f"provisional_release_nonblocking_failure={exc}"
            step_timeout=min(timeout,int(dag.get("scoped_worker_timeout_seconds") or 3600))
            rc,log=scoped_codex_worker.run_step(ep,s.step_id,codex_raw=codex,timeout=step_timeout); note=(note+" "+f"log={log}").strip()
        else:
            rc=2; note=f"unknown executor {s.executor}"
        elapsed=time.monotonic()-t0
        if rc==0 and s.target_state:
            ok,msg=validate_target(ep,s.target_state)
            if not ok: rc=4; note=(note+"\nPOSTCONDITION FAIL\n"+msg)[-5000:]
        status="PASS" if rc==0 else ("BLOCKED" if rc in {124,3,4} else "FAILED")
        out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
        res=proto.StepResult(s.step_id,status,attempt,started_at,proto.now(),elapsed,input_hash,out_hash,note,rc)
        proto.save_result(ep,res); checkpoint(ep,s.step_id,status,elapsed,note[-1200:],attempt,input_hash,out_hash)
        if run_id: perf.record_step(ep,run_id,s.step_id,status,elapsed,note[-500:])
        try: quota_observability.snapshot(ep,note=f"after {s.step_id}")
        except Exception: pass
        if rc!=0:
            background.shutdown(wait=False,cancel_futures=True)
            return rc
        if s.step_id=="CREATIVE_STORY" and provisional_future is None and bool(dag.get("provisional_release_parallel",True)):
            provisional_future=background.submit(provisional_release.build,ep,codex,900)
    background.shutdown(wait=False)
    return 0

def self_test():
    rows=spec_rows()
    assert [x.step_id for x in rows]==["INCREMENTAL_PLAN","CREATIVE_STORY","VISUAL_LOCK","PRODUCTION","RELEASE"]
    assert rows[-1].target_state=="PUBLISH_READY"
    print("RUNTIME DAG V1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("plan"); p.add_argument("episode_dir")
    for n in ("run","resume"):
        p=sub.add_parser(n); p.add_argument("episode_dir"); p.add_argument("--codex"); p.add_argument("--timeout",type=int,default=7200)
    p=sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="plan": print(json.dumps(plan(ep),ensure_ascii=False,indent=2)); return 0
    if a.cmd=="show": print(json.dumps(proto.load_state(ep),ensure_ascii=False,indent=2)); return 0
    return execute(ep,codex=a.codex,timeout=a.timeout)

if __name__=="__main__": raise SystemExit(main())
