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
import runtime_router
import product_runtime_adapter
import next_action
import episode_performance
import runtime_timeout_policy
import runtime_node_registry
import runtime_node_evidence
import storyos_config
import runtime_scheduler
import runtime_checkpoint
import runtime_command
import runtime_ownership
import validate_episode
import machine_gate
import evidence_gate

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=Path(__file__).resolve().parent
DAG_FILE=ROOT/"runtimes/runtime-dag.json"
from story_os_contract import canonical_stages
STAGES=tuple(canonical_stages())

# STORY_OS_PHASE461_VISUAL_PROFILE_CLOSURE: returned when the pre-resume Visual Profile
# reconciliation refuses to continue (a committed production asset exists on a profile that
# nobody has confirmed).
RECONCILE_BLOCKED_RC=9

# STORY_OS_V211_INCREMENTAL_PLAN_REUSE: the incremental planner's real input surface,
# read off incremental_closure.plan(). The generic input_hash cannot be reused for this
# step: its evidence_paths is meta/runtime-checkpoint.json, which checkpoint() rewrites
# on every step of every pass, so that hash never repeats and would never hit. These are
# the files plan() actually inspects -- episode-state, story-gates (via subtitle_required)
# and the four evidence files. production-ledger.json belongs here because it moves with
# the pixel assets, which is exactly when the plan does need recomputing.
INCREMENTAL_PLAN_STEP="INCREMENTAL_PLAN"
INCREMENTAL_PLAN_INPUTS=[
    "meta/episode-state.json","meta/story-gates.json","meta/story-semantic-review.json",
    "meta/visual-profile-review.json","meta/production-ledger.json",
    "meta/subtitle-layout-audit.json","meta/text-audit.json",
]


def reconcile_visual_profile_closure(ep):
    """Phase 4.6.1: reconcile the Visual Profile closure before the DAG resumes.

    A promote hook only runs at a promotion, so a production asset committed while the profile
    was not yet LOCKED can leave LOCKED + committed asset + not FROZEN with no later trigger.
    This is the single runtime recovery point for that state. It only *consumes*
    visual_profile_closure.reconcile_episode: no registry, lifecycle or asset-commit rule is
    re-implemented here, and nothing is confirmed.

    Returns None when the runtime may continue (frozen / noop / skipped), or a list of blocking
    lines when it may not. A refused recovery (VISUAL_PROFILE_NOT_LOCKED) must not be turned
    into a pass, so this returns a block rather than a diagnostic.
    """
    try:
        import visual_profile_closure as closure
        report=closure.reconcile_episode(ep)
    except Exception as exc:
        return ["visual profile closure reconcile unavailable: "+type(exc).__name__+": "+str(exc)]
    status=str(report.get("status") or "")
    if status!=closure.RESULT_FAIL:
        return None
    return [
        "visual profile closure reconcile refused: "+str(report.get("code")),
        "lifecycle_state="+str(report.get("lifecycle_state")),
        str(report.get("detail") or ""),
    ]

def run(cmd):
    return runtime_command.run_argv([str(x) for x in cmd],cwd=ROOT,capture=True)
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
    ep=Path(ep).resolve()
    findings=validate_episode.validate_episode(ep,ROOT,False,target)
    failed=[str(x) for x in findings if getattr(x,"level",None)=="FAIL"]
    if failed: return False,"\n".join(failed)[-5000:]
    findings=machine_gate.validate(ep,target,metadata_only=False)
    failed=[str(x) for x in findings if getattr(x,"level",None)=="FAIL"]
    if failed: return False,"\n".join(failed)[-5000:]
    ok,messages=evidence_gate.run_gate(ep,target)
    if not ok: return False,"\n".join(str(x) for x in messages)[-5000:]
    return True,"PASS"

# STORY_OS_V262_DAG_STOP_TARGET: an explicit --until target lets a bounded pass end on a chosen
# stage instead of running the whole DAG. It is a caller-imposed stop, never a second stage
# authority: the stop only counts once the canonical state has advanced AND the same three gates
# that guard advancement accept that stage, so --until can never report "reached" for a stage the
# Episode has not actually validated. Default None means every existing caller is unaffected.
STOP_TARGET_REACHED="STOP_TARGET_REACHED"

def stop_target_reached(ep,target):
    """Return (reached, detail) for an --until stop target.

    The canonical state read is cheap and happens first, so the three gate subprocesses are
    spawned only once the Episode has actually arrived at the target.
    """
    cur=state(ep)
    if not stage_at_least(cur,target):
        return False,"current_state="+str(cur)
    ok,msg=validate_target(ep,target)
    if not ok:
        return False,"gate rejected "+target+": "+str(msg)[-800:]
    return True,"PASS"
def checkpoint(ep,step,status,elapsed,note,attempt=1,input_hash=None,output_hash=None):
    try:
        runtime_checkpoint.record_step(
            ep,step=step,status=status,attempt=attempt,finished_at=proto.now(),note=note,
            input_hash=input_hash,output_hash=output_hash)
    except FileNotFoundError:
        # Compatibility with the former subprocess path: runtime_checkpoint.py
        # returned non-zero when the file was absent, but DAG intentionally did
        # not treat that recovery-projection failure as stage authority.
        return None

def spec_rows():
    d=load_dag(); rows=[]
    for x in d["steps"]:
        rows.append(proto.StepSpec(
            step_id=x["id"],executor=x["executor"],depends_on=tuple(x.get("depends_on") or []),
            covers=tuple(x.get("covers") or []),target_state=x.get("target_state"),
            evidence_paths=tuple(x.get("evidence_paths") or []),expensive=bool(x.get("expensive"))))
    return rows


def normalize_node_contracts(nodes):
    """Validate scheduling-only nodes without reading or writing Episode state."""
    if isinstance(nodes, dict):
        nodes = nodes.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("node contract must contain a nodes list")
    result = []
    ids = set()
    for index, raw in enumerate(nodes):
        if not isinstance(raw, dict):
            raise ValueError(f"node at index {index} must be an object")
        node_id = str(raw.get("node_id") or "").strip()
        if not node_id or node_id in ids:
            raise ValueError(f"node_id must be unique and non-empty: {node_id!r}")
        depends_on = raw.get("depends_on") or []
        if not isinstance(depends_on, list) or any(not str(x).strip() for x in depends_on):
            raise ValueError(f"node {node_id} has invalid depends_on")
        item = dict(raw)
        item["node_id"] = node_id
        item["depends_on"] = [str(x) for x in depends_on]
        item["_order"] = index
        result.append(item)
        ids.add(node_id)
    unknown = sorted({dep for item in result for dep in item["depends_on"] if dep not in ids})
    if unknown:
        raise ValueError("unknown node dependencies: " + ", ".join(unknown))
    return result


def resolve_node_dependencies(nodes, *, completed=(), failed=()):
    """Return ready, waiting and downstream-blocked nodes for one scheduling pass.

    This is deliberately a pure function.  It neither executes a node nor records
    a runtime status, so it cannot become an Episode stage authority.
    """
    rows = normalize_node_contracts(nodes)
    completed = {str(value) for value in completed}
    failed = {str(value) for value in failed}
    known = {row["node_id"] for row in rows}
    unknown_outcomes = (completed | failed) - known
    if unknown_outcomes:
        raise ValueError("unknown completed/failed nodes: " + ", ".join(sorted(unknown_outcomes)))
    if completed & failed:
        raise ValueError("a node cannot be both completed and failed")

    blocked = set()
    changed = True
    while changed:
        changed = False
        for row in rows:
            node_id = row["node_id"]
            if node_id in completed or node_id in failed or node_id in blocked:
                continue
            if any(dep in failed or dep in blocked for dep in row["depends_on"]):
                blocked.add(node_id)
                changed = True

    ready = []
    waiting = []
    for row in rows:
        node_id = row["node_id"]
        if node_id in completed or node_id in failed or node_id in blocked:
            continue
        if set(row["depends_on"]).issubset(completed):
            ready.append(row)
        else:
            waiting.append(row)
    return {"ready": ready, "waiting": waiting, "blocked": [
        row for row in rows if row["node_id"] in blocked
    ]}

def production_scheduler_resources() -> dict:
    """Resolved capacity presented to the top-level production scheduler.

    Top-level Runtime steps stay serial unless their Node Contract explicitly
    declares ``parallel_safe``.  The snapshot therefore exposes real lane
    capacity without forcing unsafe composite steps to run concurrently.  Image
    concurrency remains delegated to image_scheduler and PREIMAGE concurrency to
    its task protocol, but the scheduler no longer plans against a fake global
    ``max_workers=1`` resource model.
    """
    config=storyos_config.load_config()
    authority=max(1,int(storyos_config.get_path(config,"runtime.workers.local_codex_preimage",4)))
    derived=max(1,int(storyos_config.get_path(config,"runtime.workers.derived",6)))
    image=max(1,int(storyos_config.get_path(config,"production.max_inflight_images",3)))
    max_workers=max(authority,derived,image,1)
    return {
        "max_workers":max_workers,
        "current_workers":0,
        "runtime_capacity":{
            "text":1,
            "review":1,
            "preimage":authority,
            "authority":authority,
            "derived":derived,
            "image":image,
        },
    }


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

def run_release_preflight_recovery(ep: Path, codex=None, timeout=None) -> tuple[int, str]:
    """Run targeted release evidence recovery after the scoped RELEASE worker.

    The scoped worker creates captions/copy/assets.  This hook reuses the
    existing prepare-auto recovery only after those sources exist, so stale
    caption/compliance/release-review evidence does not force a second full
    RELEASE worker invocation.  Non-zero results are preserved fail-closed.
    """
    import argparse
    import release_preflight
    try:
        rc = int(release_preflight.cmd_prepare_auto(argparse.Namespace(
            episode_dir=str(ep), codex=codex, timeout=timeout,
        )))
    except Exception as exc:
        return 4, f"RELEASE PREFLIGHT AUTO RECOVERY FAIL: {exc}"
    if rc != 0:
        return rc, f"RELEASE PREFLIGHT AUTO RECOVERY rc={rc}"
    return 0, "RELEASE PREFLIGHT AUTO RECOVERY PASS"


def execute(ep,codex=None,timeout=None,run_id=None,trace_id=None,until=None):
    # W-11: a recorded production-owner switch only becomes effective when the
    # Production Kernel consumes it. Direct DAG execution is a production entry,
    # so fail closed before any reconcile/executor side effect.
    runtime_ownership.assert_v3_owner("runtime_dag.execute")
    # STORY_OS_V262_DAG_STOP_TARGET: a stop target is a canonical Episode stage, never a step id.
    # Reject an unknown target before any reconcile, lock or executor exists.
    if until is not None and until not in STAGES:
        raise ValueError("unknown runtime DAG stop target: "+str(until))
    blocked=reconcile_visual_profile_closure(ep)
    if blocked is not None:
        # Phase 4.6.1: an unreconcilable Visual Profile closure fails closed. It is never
        # reported as a pass, and no production step is started.
        print("VISUAL PROFILE CLOSURE RECONCILE BLOCKED")
        for line in blocked: print(line)
        return RECONCILE_BLOCKED_RC
    dag=load_dag(); specs=spec_rows(); total_start=time.monotonic()
    if timeout is None:
        timeout = runtime_timeout_policy.seconds("codex_supervisor_run")
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
    # V3 V2.1: retain existing executors and evidence/Gate behavior, but let the
    # scheduler release the next real Runtime step from its declared dependencies.
    # max_workers remains 1 because these composite legacy steps are not yet safe
    # to execute concurrently.
    step_by_id={spec.step_id: spec for spec in specs}
    completed_nodes=set()
    node_contract=runtime_node_registry.runtime_step_nodes(specs)
    scheduler_resources=production_scheduler_resources()
    if until:
        # Already at or past the target: stopping is a no-op, so do not spawn INCREMENTAL_PLAN
        # or any other step merely to arrive back here.
        reached,detail=stop_target_reached(ep,until)
        if reached:
            background.shutdown(wait=False,cancel_futures=True)
            print(STOP_TARGET_REACHED+" "+until+" (already valid)")
            return 0
    while len(completed_nodes)<len(specs):
        wave=runtime_scheduler.schedule(
            node_contract,
            completed=completed_nodes,
            max_workers=scheduler_resources["max_workers"],
            resource_snapshot=scheduler_resources,
        )
        if not wave["dispatch"]:
            background.shutdown(wait=False,cancel_futures=True)
            print("RUNTIME DAG SCHEDULER BLOCKED", json.dumps({
                "waiting":[x["node_id"] for x in wave["waiting"]],
                "blocked":[x["node_id"] for x in wave["blocked"]],
            },ensure_ascii=True))
            return 2
        s=step_by_id[wave["dispatch"][0]["node_id"]]
        cur=state(ep)
        if s.step_id=="CREATIVE_STORY" and not stage_at_least(cur,"STORYBOARD_LOCKED"):
            directing_quality.before_step(ep,s.step_id)
            preparation_started=proto.now()
            character_contract.prepare(ep,force=False)
            runtime_node_evidence.record(
                ep,node_id="character_prepare",start_time=preparation_started,end_time=proto.now(),
                status="PASS",attempt=1,output="character_contract.prepare completed",
                evidence=["meta/character-contract.json"])
        prior=(proto.load_state(ep).get("steps") or {}).get(s.step_id) or {}
        attempt=int(prior.get("attempt") or 0)+1
        input_hash=proto.evidence_hash(ep,["meta/runtime-request.json","meta/episode-state.json",*s.evidence_paths])
        if s.step_id==INCREMENTAL_PLAN_STEP:
            input_hash=proto.evidence_hash(ep,INCREMENTAL_PLAN_INPUTS)
        if s.step_id=="PREIMAGE_COMPILE":
            handoff_valid=False
            try:
                handoff_valid=(ep/"meta/preproduction-handoff.json").is_file() and not preproduction_handoff.verify(ep)
            except Exception:
                handoff_valid=False
            if handoff_valid or stage_at_least(cur,"VISUAL_CALIBRATED"):
                reason="preproduction handoff already valid" if handoff_valid else "downstream stage already valid; legacy preimage not backfilled"
                out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
                res=proto.StepResult(s.step_id,"REUSED",attempt,proto.now(),proto.now(),0.0,input_hash,out_hash,reason,0)
                proto.save_result(ep,res); checkpoint(ep,s.step_id,"REUSED",0,reason,attempt,input_hash,out_hash)
                if run_id: perf.record_step(ep,run_id,s.step_id,"REUSED",0,reason)
                episode_performance.safe_end_stage(ep,s.step_id,status="REUSED",metadata={"reused":True,"reason":reason})
                next_action.write(ep)
                runtime_node_evidence.record(
                    ep,node_id=s.step_id,start_time=res.started_at,end_time=res.finished_at,
                    status="REUSED",attempt=attempt,output=reason,evidence=s.evidence_paths)
                completed_nodes.add(s.step_id)
                if mode=="preproduction_only":
                    background.shutdown(wait=False,cancel_futures=True)
                    return 0
                continue
        # STORY_OS_V211_INCREMENTAL_PLAN_REUSE: the planner is a pure function of the files
        # in INCREMENTAL_PLAN_INPUTS (all four subcommands it spawns are read-only) and
        # incremental_closure.py:143 returns 0 unconditionally, so re-running it on unchanged
        # inputs recomputes a verdict this DAG discards anyway. Skip the ~4 subprocess spawns.
        if (s.step_id==INCREMENTAL_PLAN_STEP and prior.get("status") in {"PASS","REUSED"}
                and prior.get("input_hash")==input_hash):
            reason="plan inputs unchanged since last run"
            out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
            res=proto.StepResult(s.step_id,"REUSED",attempt,proto.now(),proto.now(),0.0,input_hash,out_hash,reason,0)
            proto.save_result(ep,res); checkpoint(ep,s.step_id,"REUSED",0,reason,attempt,input_hash,out_hash)
            if run_id: perf.record_step(ep,run_id,s.step_id,"REUSED",0,reason)
            episode_performance.safe_end_stage(ep,s.step_id,status="REUSED",metadata={"reused":True,"reason":reason})
            _t=time.monotonic()
            _sp=runtime_trace.start_span(ep,s.step_id,category="workflow_step",trace_id=trace_id,run_id=run_id,attrs={"reused":True})
            runtime_trace.end_span(ep,_sp,name=s.step_id,category="workflow_step",status="REUSED",started_monotonic=_t,trace_id=trace_id,run_id=run_id,attrs={"reason":reason})
            runtime_node_evidence.record(
                ep,node_id=s.step_id,start_time=res.started_at,end_time=res.finished_at,
                status="REUSED",attempt=attempt,output=reason,evidence=s.evidence_paths)
            completed_nodes.add(s.step_id)
            continue
        if s.target_state and stage_at_least(cur,s.target_state):
            ok,msg=validate_target(ep,s.target_state)
            if ok:
                out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
                res=proto.StepResult(s.step_id,"REUSED",attempt,proto.now(),proto.now(),0.0,input_hash,out_hash,"target already valid",0)
                proto.save_result(ep,res); checkpoint(ep,s.step_id,"REUSED",0,"target already valid",attempt,input_hash,out_hash)
                if run_id: perf.record_step(ep,run_id,s.step_id,"REUSED",0,"target already valid")
                episode_performance.safe_end_stage(ep,s.step_id,status="REUSED",metadata={"reused":True,"target_state":s.target_state})
                _t=time.monotonic()
                _sp=runtime_trace.start_span(ep,s.step_id,category="workflow_step",trace_id=trace_id,run_id=run_id,attrs={"reused":True})
                runtime_trace.end_span(ep,_sp,name=s.step_id,category="workflow_step",status="REUSED",started_monotonic=_t,trace_id=trace_id,run_id=run_id,attrs={"target_state":s.target_state})
                runtime_node_evidence.record(
                    ep,node_id=s.step_id,start_time=res.started_at,end_time=res.finished_at,
                    status="REUSED",attempt=attempt,output="target already valid",evidence=s.evidence_paths)
                completed_nodes.add(s.step_id)
                continue
        started_at=proto.now(); t0=time.monotonic(); rc=0; note=""
        episode_performance.safe_begin_stage(ep,s.step_id,source="runtime_dag",metadata={"executor":s.executor,"target_state":s.target_state})
        trace_span=runtime_trace.start_span(ep,s.step_id,category="workflow_step",trace_id=trace_id,run_id=run_id,attrs={"executor":s.executor,"target_state":s.target_state})
        if s.step_id=="PREIMAGE_COMPILE":
            resource_library.resolve(ep,write=True)
            intro_policy.resolve(ep,write=True)
        if s.executor=="machine_incremental_plan":
            cp=run([sys.executable,SYSTEM/"incremental_closure.py","plan",ep,"--json"]); rc=cp.returncode; note=cp.stdout[-3000:]
        elif s.executor in {"scoped_model","scoped_codex"}:
            execution_capsule.compile_capsule(ep,s.step_id,write=True)
            active_runtime,_=runtime_router.detect()
            if active_runtime in {"WORK","WEB"} and not codex:
                deterministic_preimage_step=None
                if s.step_id=="PREIMAGE_COMPILE":
                    host_step,_=product_runtime_adapter.next_host_step(ep,mode)
                    if host_step=="PREIMAGE_FRAME_CONTRACT_COMPILE":
                        import frame_contract
                        try:
                            index=frame_contract.compile_all(ep)
                            deterministic_preimage_step=host_step
                            note=json.dumps({"deterministic_step":host_step,"frame_contract_index_sha256":index.get("index_sha256")},ensure_ascii=True)
                        except Exception as exc:
                            rc=4
                            note=f"PREIMAGE FRAME CONTRACT COMPILE FAIL: {exc}"
                    elif host_step=="PREIMAGE_VERIFY":
                        deterministic_preimage_step=host_step
                        note=json.dumps({"deterministic_step":host_step,"reason":"current authority exists; verify/build handoff locally"},ensure_ascii=True)
                if deterministic_preimage_step is not None:
                    rc=0
                elif rc==0:
                    request=product_runtime_adapter.build_request(
                        ep,runtime=active_runtime,mode=mode,resume=True,source=f"runtime_dag:{s.step_id}")
                    rc=product_runtime_adapter.HOST_ACTION_REQUIRED_RC
                    note=json.dumps(request,ensure_ascii=True)
            elif s.step_id=="PREIMAGE_COMPILE":
                # A local explicit CODEX run executes four bounded workers.  It
                # is not a threaded wrapper around the legacy composite prompt.
                import preimage_protocol
                import preimage_task_contract
                # Fail here, before the fan-out, if any task's step is missing
                # from a registry: the alternative is discovering it inside a
                # worker 20 minutes in, with the other three already running.
                preimage_task_contract.assert_registries_aligned()
                # This branch is the explicit local-Codex PREIMAGE fallback only.
                # WORK + DevSpace production goes through the host-action branch above;
                # its concurrency is owned by the host transport, not this local pool.
                workers=int(storyos_config.get_path(storyos_config.load_config(),"runtime.workers.local_codex_preimage") or 4)
                def _worker(task):
                    step=preimage_task_contract.canonical_step(task["task_type"])
                    execution_capsule.compile_capsule(ep,step,write=True)
                    value, _log=scoped_codex_worker.run_step(ep,step,codex_raw=codex,timeout=timeout)
                    return value
                outcome=preimage_protocol.execute_local(ep,_worker,max_workers=workers)
                rc=0 if outcome.get("status")=="PASS" else 4
                if rc == 0:
                    import frame_contract
                    try:
                        index=frame_contract.compile_all(ep)
                        outcome["frame_contract_index_sha256"]=index.get("index_sha256")
                    except Exception as exc:
                        rc=4; outcome["frame_contract_compile_error"]=str(exc)
                note=(note+" "+json.dumps(outcome,ensure_ascii=True))[-5000:]
            else:
                if s.step_id=="RELEASE" and provisional_future is not None:
                    try:
                        prep=provisional_future.result(timeout=120)
                        note=f"provisional_release={prep}"
                    except Exception as exc:
                        note=f"provisional_release_nonblocking_failure={exc}"
                step_timeout=min(timeout,int(dag.get("scoped_worker_timeout_seconds") or runtime_timeout_policy.seconds("codex_scoped_step")))
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
        if rc==0 and s.step_id=="PREIMAGE_COMPILE":
            quality_errors=directing_quality.verify_preimage(ep)
            if quality_errors:
                rc=4
                note=(note+"\nPREIMAGE DIRECTING QUALITY FAIL\n"+"\n".join(quality_errors))[-5000:]
            else:
                try:
                    handoff=preproduction_handoff.build(ep,source_runtime="chatgpt_or_codex")
                    note=(note+"\npreproduction_handoff="+str(handoff.get("manifest_sha256") or ""))[-5000:]
                except Exception as exc:
                    rc=7
                    note=(note+"\nPREPRODUCTION HANDOFF FAIL: "+str(exc))[-5000:]
        if rc==0:
            quality_errors=directing_quality.after_step(ep,s.step_id)
            if quality_errors:
                rc=4
                note=(note+"\nDIRECTING QUALITY FAIL\n"+"\n".join(quality_errors))[-5000:]
        if rc==0 and s.step_id=="RELEASE":
            recovery_rc,recovery_note=run_release_preflight_recovery(ep,codex=codex,timeout=timeout)
            note=(note+"\n"+recovery_note)[-5000:]
            if recovery_rc!=0:
                rc=recovery_rc
        if rc==0 and s.target_state:
            ok,msg=validate_target(ep,s.target_state)
            if not ok: rc=4; note=(note+"\nPOSTCONDITION FAIL\n"+msg)[-5000:]
        status="PASS" if rc==0 else ("HOST_WAIT" if rc==product_runtime_adapter.HOST_ACTION_REQUIRED_RC else ("BLOCKED" if rc in {124,3,4} else "FAILED"))
        out_hash=proto.evidence_hash(ep,["meta/episode-state.json",*s.evidence_paths])
        res=proto.StepResult(s.step_id,status,attempt,started_at,proto.now(),elapsed,input_hash,out_hash,note,rc)
        proto.save_result(ep,res); checkpoint(ep,s.step_id,status,elapsed,note[-1200:],attempt,input_hash,out_hash)
        runtime_node_evidence.record(
            ep,node_id=s.step_id,start_time=started_at,end_time=res.finished_at,status=status,
            attempt=attempt,output=note[-1200:],evidence=s.evidence_paths)
        if run_id: perf.record_step(ep,run_id,s.step_id,status,elapsed,note[-500:])
        runtime_trace.end_span(ep,trace_span,name=s.step_id,category="workflow_step",status=status,started_monotonic=t0,trace_id=trace_id,run_id=run_id,attrs={"rc":rc,"attempt":attempt})
        if status != "HOST_WAIT":
            episode_performance.safe_end_stage(ep,s.step_id,status=status,metadata={"rc":rc,"attempt":attempt})
        try: quota_observability.snapshot(ep,note=f"after {s.step_id}")
        except Exception: pass
        try: performance_guard_v211.observe(ep,run_id,context=s.step_id)
        except Exception: pass
        next_action.write(ep)
        if rc!=0:
            # STORY_OS_V211_PERF_RECOVERY: on Visual Lock infrastructure failure,
            # generate at most six non-approvable candidates instead of idling.
            if s.step_id=="VISUAL_LOCK" and mode=="image_continue":
                try:
                    spec=speculative_production.run(ep,codex=codex,timeout=runtime_timeout_policy.clamp("image_lane_run", int(timeout)),max_frames=6)
                    spec_elapsed=float(spec.get("elapsed_seconds") or 0.0)
                    if run_id: perf.record_step(ep,run_id,"SPECULATIVE_PRODUCTION","PASS" if spec.get("status")=="GENERATED_CANDIDATES" else "SKIPPED",spec_elapsed,json.dumps(spec,ensure_ascii=True)[:500])
                    checkpoint(ep,"SPECULATIVE_PRODUCTION","PASS" if spec.get("status")=="GENERATED_CANDIDATES" else "SKIPPED",spec_elapsed,json.dumps(spec,ensure_ascii=True)[:1000])
                except Exception as exc:
                    if run_id: perf.record_step(ep,run_id,"SPECULATIVE_PRODUCTION","FAILED",0.0,str(exc)[:500])
            background.shutdown(wait=False,cancel_futures=True)
            return rc
        completed_nodes.add(s.step_id)
        if until:
            reached,detail=stop_target_reached(ep,until)
            if reached:
                # The step already wrote its checkpoint, node evidence, trace span and
                # next-action above, so a clean stop here loses no evidence.
                background.shutdown(wait=False,cancel_futures=True)
                print(STOP_TARGET_REACHED+" "+until+" after "+s.step_id)
                return 0
        if mode=="preproduction_only" and s.step_id=="PREIMAGE_COMPILE":
            try:
                # 900s was the historical review-critic default; build() now owns that default.
                provisional_release.build(ep,codex)
            except Exception as exc:
                print("PROVISIONAL RELEASE NONBLOCKING:",exc)
            background.shutdown(wait=False,cancel_futures=True)
            next_action.write(ep)
            return 0
        if s.step_id=="CREATIVE_STORY" and provisional_future is None and bool(dag.get("provisional_release_parallel",True)):
            provisional_future=background.submit(provisional_release.build,ep,codex)
    background.shutdown(wait=False)
    return 0

def self_test():
    rows=spec_rows()
    assert [x.step_id for x in rows]==["INCREMENTAL_PLAN","CREATIVE_STORY","PREIMAGE_COMPILE","VISUAL_LOCK","PRODUCTION","RELEASE"]
    assert rows[-1].target_state=="PUBLISH_READY"
    # STORY_OS_V262_DAG_STOP_TARGET: --until takes a canonical stage, and every step's
    # declared target_state must be one, so a stop target and a step target are comparable.
    assert "PRODUCTION_PASSED" in STAGES, STAGES
    assert "PRODUCTION" not in STAGES, "a step id is not a stage"
    for row in rows:
        assert row.target_state is None or row.target_state in STAGES, row
    assert stage_at_least("PRODUCTION_PASSED","PRODUCTION_PASSED")
    assert not stage_at_least("VISUAL_CALIBRATED","PRODUCTION_PASSED")
    print("RUNTIME DAG V1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("plan"); p.add_argument("episode_dir")
    for n in ("run","resume"):
        p=sub.add_parser(n); p.add_argument("episode_dir"); p.add_argument("--codex"); p.add_argument("--timeout",type=int,default=None)
        p.add_argument("--until",choices=STAGES,default=None,help="stop cleanly once this canonical stage is reached and validated")
    p=sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="plan": print(json.dumps(plan(ep),ensure_ascii=True,indent=2)); return 0
    if a.cmd=="show": print(json.dumps(proto.load_state(ep),ensure_ascii=True,indent=2)); return 0
    return execute(ep,codex=a.codex,timeout=runtime_timeout_policy.resolve("codex_supervisor_run", a.timeout),until=a.until)

if __name__=="__main__": raise SystemExit(main())

# STORY_OS_V211_RUNTIME_CLOSURE_R31
