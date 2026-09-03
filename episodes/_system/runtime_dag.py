#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, concurrent.futures as cf, json, subprocess, sys, time
from pathlib import Path

import quota_observability
import execution_capsule
import character_contract
import provisional_release
import preproduction_handoff
import resource_library
import intro_policy
import multi_level_cache
import runtime_execution
import scoped_codex_worker
import runtime_mode_router
import directing_quality
import world_identity_contract  # STORY_OS_V221_WORLD_IDENTITY
import character_appearance_anchor  # STORY_OS_V221_CHARACTER_CONTINUITY
import workflow_performance as perf
import workflow_step_protocol as proto
import speculative_production  # STORY_OS_V211_PERF_RECOVERY
import performance_guard_v211
import runtime_trace

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
def request_mode(ep):
    return runtime_execution.effective_mode(ep)
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

def execute(ep,codex=None,timeout=7200,run_id=None,trace_id=None):
    dag=load_dag(); specs=spec_rows(); total_start=time.monotonic()
    mode=request_mode(ep)
    mode_errors=runtime_mode_router.guard(ep,mode)
    if mode_errors:
        print("RUNTIME_MODE_GUARD_FAIL")
        for err in mode_errors: print(err)
        return 8
    special_rc=runtime_mode_router.dispatch_special(ep,mode,codex,timeout)
    if special_rc is not None: return special_rc
    if mode=="image_continue":
        preproduction_handoff.migrate_legacy_boundary(ep)  # STORY_OS_V211_PERF_RECOVERY
        handoff_errors=preproduction_handoff.verify(ep)
        if handoff_errors:
            print("HANDOFF VERIFY FAIL")
            for err in handoff_errors:print(err)
            return 6
        resource_library.resolve(ep,write=True)
    provisional_future=None
    background=cf.ThreadPoolExecutor(max_workers=1,thread_name_prefix="story-os-release-prep")
    for s in specs:
        cur=state(ep)
        if s.step_id=="CREATIVE_STORY" and not stage_at_least(cur,"STORYBOARD_LOCKED"):
            directing_quality.before_step(ep,s.step_id)
            character_contract.prepare(ep,force=False)
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
                _t=time.monotonic()
                _sp=runtime_trace.start_span(ep,s.step_id,category="workflow_step",trace_id=trace_id,run_id=run_id,attrs={"reused":True})
                runtime_trace.end_span(ep,_sp,name=s.step_id,category="workflow_step",status="REUSED",started_monotonic=_t,trace_id=trace_id,run_id=run_id,attrs={"target_state":s.target_state})
                continue
        started_at=proto.now(); t0=time.monotonic(); rc=0; note=""
        trace_span=runtime_trace.start_span(ep,s.step_id,category="workflow_step",trace_id=trace_id,run_id=run_id,attrs={"executor":s.executor,"target_state":s.target_state})
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
        if rc==0 and s.step_id=="CREATIVE_STORY":
            character_errors=character_contract.validate(ep,require_locked=True)
            if character_errors:
                rc=4
                note=(note+"\nCHARACTER CONTRACT FAIL\n"+"\n".join(character_errors))[-5000:]
            elif world_identity_contract.required(ep):
                world_errors=world_identity_contract.verify(ep)
                if world_errors:
                    rc=4
                    note=(note+"\nWORLD IDENTITY FAIL\n"+"\n".join(world_errors))[-5000:]
                else:
                    try:
                        character_appearance_anchor.build(ep,write=True)
                        anchor_errors=character_appearance_anchor.verify(ep)
                    except Exception as exc:
                        anchor_errors=[str(exc)]
                    if anchor_errors:
                        rc=4
                        note=(note+"\nCHARACTER APPEARANCE ANCHOR FAIL\n"+"\n".join(anchor_errors))[-5000:]
        if rc==0:
            quality_errors=directing_quality.after_step(ep,s.step_id)
            if quality_errors:
                rc=4
                note=(note+"\nDIRECTING QUALITY FAIL\n"+"\n".join(quality_errors))[-5000:]
        if rc==0 and s.target_state:
            ok,msg=validate_target(ep,s.target_state)
            if not ok: rc=4; note=(note+"\nPOSTCONDITION FAIL\n"+msg)[-5000:]
        status="PASS" if rc==0 else ("BLOCKED" if rc in {124,3,4} else "FAILED")
        out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
        res=proto.StepResult(s.step_id,status,attempt,started_at,proto.now(),elapsed,input_hash,out_hash,note,rc)
        proto.save_result(ep,res); checkpoint(ep,s.step_id,status,elapsed,note[-1200:],attempt,input_hash,out_hash)
        if run_id: perf.record_step(ep,run_id,s.step_id,status,elapsed,note[-500:])
        runtime_trace.end_span(ep,trace_span,name=s.step_id,category="workflow_step",status=status,started_monotonic=t0,trace_id=trace_id,run_id=run_id,attrs={"rc":rc,"attempt":attempt})
        try: quota_observability.snapshot(ep,note=f"after {s.step_id}")
        except Exception: pass
        try: performance_guard_v211.observe(ep,run_id,context=s.step_id)
        except Exception: pass
        if rc!=0:
            # STORY_OS_V211_PERF_RECOVERY: on Visual Lock infrastructure failure,
            # generate at most six non-approvable candidates instead of idling.
            if s.step_id=="VISUAL_LOCK" and mode=="image_continue":
                try:
                    spec=speculative_production.run(ep,codex=codex,timeout=min(600,max(60,int(timeout))),max_frames=6)
                    spec_elapsed=float(spec.get("elapsed_seconds") or 0.0)
                    if run_id: perf.record_step(ep,run_id,"SPECULATIVE_PRODUCTION","PASS" if spec.get("status")=="GENERATED_CANDIDATES" else "SKIPPED",spec_elapsed,json.dumps(spec,ensure_ascii=False)[:500])
                    checkpoint(ep,"SPECULATIVE_PRODUCTION","PASS" if spec.get("status")=="GENERATED_CANDIDATES" else "SKIPPED",spec_elapsed,json.dumps(spec,ensure_ascii=False)[:1000])
                except Exception as exc:
                    if run_id: perf.record_step(ep,run_id,"SPECULATIVE_PRODUCTION","FAILED",0.0,str(exc)[:500])
            background.shutdown(wait=False,cancel_futures=True)
            return rc
        if mode=="preproduction_only" and s.step_id=="CREATIVE_STORY":
            resource_library.resolve(ep,write=True)
            intro_policy.resolve(ep,write=True)
            pre_started=time.monotonic()
            pre_rc,pre_log=scoped_codex_worker.run_step(ep,"PREIMAGE_COMPILE",codex_raw=codex,timeout=min(timeout,int(dag.get("scoped_worker_timeout_seconds") or 3600)))
            pre_elapsed=time.monotonic()-pre_started
            checkpoint(ep,"PREIMAGE_COMPILE","PASS" if pre_rc==0 else "FAILED",pre_elapsed,f"log={pre_log}")
            if run_id:perf.record_step(ep,run_id,"PREIMAGE_COMPILE","PASS" if pre_rc==0 else "FAILED",pre_elapsed,f"log={pre_log}")
            if pre_rc!=0:
                background.shutdown(wait=False,cancel_futures=True)
                return pre_rc
            quality_errors=directing_quality.verify_preimage(ep)
            if quality_errors:
                print("PREIMAGE DIRECTING QUALITY FAIL")
                for err in quality_errors: print(err)
                background.shutdown(wait=False,cancel_futures=True)
                return 4
            try:
                provisional_release.build(ep,codex,900)
            except Exception as exc:
                print("PROVISIONAL RELEASE NONBLOCKING:",exc)
            try:
                handoff=preproduction_handoff.build(ep,source_runtime="chatgpt_or_codex")
                checkpoint(ep,"PREPRODUCTION_HANDOFF","PASS",0.0,handoff.get("manifest_sha256",""))
                if run_id:perf.record_step(ep,run_id,"PREPRODUCTION_HANDOFF","PASS",0.0,handoff.get("manifest_sha256",""))
            except Exception as exc:
                print("PREPRODUCTION HANDOFF FAIL:",exc)
                background.shutdown(wait=False,cancel_futures=True)
                return 7
            background.shutdown(wait=False,cancel_futures=True)
            return 0
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

# STORY_OS_V211_RUNTIME_CLOSURE_R31
