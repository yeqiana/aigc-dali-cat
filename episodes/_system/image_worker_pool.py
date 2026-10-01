#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Warm Python image worker adapter.

Reuses the scheduler Python process/module imports, but deliberately does NOT reuse Codex
conversation state. Current Codex transport remains ephemeral until the CLI exposes a safe
persistent image-generation daemon/session contract.
"""
from __future__ import annotations
import argparse
import os
import uuid
from pathlib import Path

import codex_subscription_image as backend
import image_model_policy
import model_policy
import prompt_package
import runtime_trace
import raw_candidate_budget  # STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
import runtime_circuit_breaker
import time
import runtime_router
import product_runtime_adapter
import resource_library
import production_recovery
import runtime_timeout_policy

MODE="python_warm_pool_codex_ephemeral"
CODEX_SESSION_REUSE=False

def model_policy_for_item(ep,item):
    episode_model_policy=image_model_policy.for_episode(ep)
    model=str(item.get("model") or episode_model_policy["model"])
    quality=str(item.get("quality") or episode_model_policy["quality"])
    return {**episode_model_policy,"model":model,"quality":quality,"strict_model":bool(item.get("strict_model",episode_model_policy.get("strict_model")))}

def generation_attempt_context(ep, item, payload_policy):
    """Capture the Episode-bound execution request before reserving an Attempt.

    These values describe the requested/bound execution context; they are not
    Provider confirmation.  The Attempt Authority persists this mapping in the
    durable row's CONTEXT before the Gateway can commit dispatch.
    """
    controller = model_policy.resolve("image.controller", episode=ep)
    payload = model_policy.resolve("image.payload", episode=ep)
    provider_candidate = str(item.get("provider_candidate") or item.get("provider") or "codex_subscription")
    runner_candidate = str(item.get("runner_candidate") or item.get("runner") or "codex_user_runner")
    return {
        "scope": item.get("scope"),
        "model_role": "image.controller",
        "profile": controller.get("profile"),
        "controller_model": controller.get("model"),
        "controller_effort": controller.get("reasoning_effort"),
        "payload_model": str(payload_policy.get("model") or payload.get("model") or ""),
        "payload_quality": str(payload_policy.get("quality") or payload.get("quality") or ""),
        "model_policy_version": controller.get("policy_version"),
        "model_policy_sha256": controller.get("model_policy_sha256"),
        "provider": provider_candidate,
        "provider_candidate": provider_candidate,
        "runner_candidate": runner_candidate,
        "controller_model_source": "EPISODE_BOUND_RUNTIME_POLICY",
        "payload_model_source": "EXPLICIT_RUNTIME_BINDING",
    }

def execute(ep,item,timeout,codex):
    resource_library.ensure_fresh(ep)
    runtime,_=runtime_router.detect()
    image_runtime,_=runtime_router.image_execution_runtime()
    if runtime in {"WORK","WEB"} and not codex and image_runtime != "CODEX":
        request=product_runtime_adapter.build_image_request(
            ep,runtime=runtime,queue_items=[item],source="image_worker_pool")
        return {
            "returncode":product_runtime_adapter.HOST_ACTION_REQUIRED_RC,
            "stdout":"HOST_ACTION_REQUIRED: product runtime image generation required; Codex image execution is not selected",
            "payload":{"product_runtime_request":request},
            "output":None,"log":None,"attempt":max(1,int(item.get("attempts") or 1)),"scout":None,
            "worker_pool":{"mode":"product_runtime_host","codex_session_reuse":False},
        }
    frame=int(item["frame"]); attempt=max(1,int(item.get("attempts") or 1))
    out=ep/"media/candidates/scheduled"/f"{frame:02d}-{item['id']}-a{attempt}.png"
    log=ep/"meta/image-workers"/f"{frame:02d}-{item['id']}-a{attempt}.jsonl"
    out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True)
    production_recovery.write_lifecycle(ep, item, "WORKER_STARTED", worker_pid=os.getpid(),
                                        expected_output=str(out), expected_log=str(log))
    root=Path(__file__).resolve().parents[2]
    prompt=(root/item["prompt_file"]).resolve()
    refs=[(root/x["path"]).resolve() for x in item.get("references") or []]
    effective_model_policy=model_policy_for_item(ep,item)
    model=str(effective_model_policy["model"])
    quality=str(effective_model_policy["quality"])
    package=prompt_package.compile_frame(ep,frame,prompt,write=True)
    blocked=runtime_circuit_breaker.blocking(ep,"image")
    if blocked:
        result={"returncode":97,"stdout":"RUNTIME_CIRCUIT_OPEN: "+str(blocked),"payload":None,"output":None,"log":log,"attempt":attempt,"scout":None}
        production_recovery.write_lifecycle(ep, item, "FAILED", worker_pid=os.getpid(), error=result["stdout"], result=result)
        return result
    budget_kind=raw_candidate_budget.kind_for_queue_item(item)
    budget_token=str(item["id"])
    budget_semantic_key=raw_candidate_budget.semantic_key_for_queue_item(item)
    attempt_context = generation_attempt_context(ep, item, effective_model_policy)
    budget_ok,budget_row=raw_candidate_budget.claim(ep,frame,budget_kind,reason=f"formal_generation_entrypoint scope={item.get('scope')} attempt={attempt}",token=budget_token,semantic_key=budget_semantic_key,
        generation_context=attempt_context)
    if not budget_ok:
        result={"returncode":98,"stdout":"RAW_CANDIDATE_BUDGET_EXHAUSTED: "+str(budget_row),"payload":None,"output":None,"log":log,"attempt":attempt,"scout":None,"budget":budget_row}
        production_recovery.write_lifecycle(ep, item, "FAILED", worker_pid=os.getpid(), error=result["stdout"], result=result)
        return result
    generation_lease = budget_row.get("lease") or {}
    item["generation_key"] = generation_lease.get("generation_key")
    item["attempt_index"] = generation_lease.get("attempt_index")
    production_recovery.write_lifecycle(
        ep, item, "ATTEMPT_RESERVED", generation_key=generation_lease.get("generation_key"),
        attempt_index=generation_lease.get("attempt_index"), fencing_token=generation_lease.get("fencing_token"),
        lease_token_hash=generation_lease.get("lease_token_hash"),
    )
    runner_request_id = uuid.uuid4().hex
    item.setdefault("execution", {})["runner_request_id"] = runner_request_id
    ns=argparse.Namespace(
        episode_dir=ep,frame=f"{frame:02d}",prompt_file=prompt,output=out,log=log,
        reference=refs,timeout=timeout,codex=codex,image_model=model,image_quality=quality,overwrite=False,
        _image_model_policy=effective_model_policy,
        _raw_candidate_budget_preclaimed=True,_raw_candidate_token=budget_token,candidate_kind=budget_kind,
        _generation_attempt_lease=generation_lease,
        _runner_request_id=runner_request_id)
    # Resident Runner image workers do not always inherit a workflow trace
    # context. Keep the span evidence correlated instead of turning a missing
    # observability context into a false worker failure.
    trace_context = runtime_trace.current(ep)
    trace_id = str(trace_context.get("trace_id") or ("ST_" + uuid.uuid4().hex[:16]))
    trace_run_id = trace_context.get("run_id")
    trace_span=runtime_trace.start_span(
        ep,f"image.generate.frame.{frame:02d}",category="image_generation",
        trace_id=trace_id,run_id=trace_run_id,
        attrs={"frame":frame,"model":model,"quality":quality})
    trace_started=time.monotonic()
    try:
        production_recovery.write_lifecycle(ep, item, "BACKEND_INVOKED", worker_pid=os.getpid(),
                                            expected_output=str(out), expected_log=str(log),
                                            runner_request_id=runner_request_id)
        payload=backend.generate_for_frame(ns)
    except Exception as exc:
        code=runtime_circuit_breaker.classify_text(str(exc))
        if code:runtime_circuit_breaker.record_failure(ep,"image",code)
        raw_candidate_budget.release(ep,budget_token,reason="generation_failed_before_candidate_commit")
        runtime_trace.end_span(ep,trace_span,name=f"image.generate.frame.{frame:02d}",category="image_generation",status="FAILED",started_monotonic=trace_started,trace_id=trace_id,run_id=trace_run_id,attrs={"frame":frame,"error":str(exc)})
        result={"returncode":99,"stdout":str(exc),"payload":None,"output":None,"log":log,"attempt":attempt,"scout":None,"worker_pool":{"mode":MODE,"codex_session_reuse":False}}
        production_recovery.write_lifecycle(ep, item, "FAILED", worker_pid=os.getpid(), error=str(exc), result=result)
        return result

    # A backend return is not success by itself.  Historical workers could
    # return rc=0 while producing no usable artifact, which let the scheduler
    # commit budget and only discover the missing file later.  Fail closed at
    # the worker boundary so technical retry/failover sees an explicit cause.
    if not out.is_file() or out.stat().st_size <= 0:
        code="IMAGE_BACKEND_NO_OUTPUT"
        raw_candidate_budget.release(ep,budget_token,reason="backend_returned_without_output")
        runtime_trace.end_span(ep,trace_span,name=f"image.generate.frame.{frame:02d}",category="image_generation",
                               status="FAILED",started_monotonic=trace_started,
                               trace_id=trace_id,run_id=trace_run_id,
                               attrs={"frame":frame,"error":code,"runner_request_id":runner_request_id})
        result={"returncode":95,"stdout":f"{code}: expected={out}","payload":payload,"output":None,"log":log,
                "attempt":attempt,"scout":None,"worker_pool":{"mode":MODE,"codex_session_reuse":False}}
        production_recovery.write_lifecycle(ep,item,"FAILED",worker_pid=os.getpid(),error=result["stdout"],result=result)
        return result

    commit_ok,commit_row=raw_candidate_budget.commit(ep,budget_token,reason="normalized_candidate_exists")
    if not commit_ok:
        runtime_trace.end_span(ep,trace_span,name=f"image.generate.frame.{frame:02d}",category="image_generation",status="FAILED",started_monotonic=trace_started,trace_id=trace_id,run_id=trace_run_id,attrs={"frame":frame,"error":"candidate commit failed"})
        result={"returncode":96,"stdout":"CANDIDATE_COMMIT_FAILED: "+str(commit_row),"payload":payload,"output":out,"log":log,"attempt":attempt,"scout":None}
        production_recovery.write_lifecycle(ep, item, "FAILED", worker_pid=os.getpid(), error=result["stdout"], result=result)
        return result
    runtime_circuit_breaker.record_success(ep,"image")

    # Review belongs to the independent durable Review Lane. Keep the worker
    # critical path limited to generation and artifact commit.
    scout=None
    runtime_trace.end_span(ep,trace_span,name=f"image.generate.frame.{frame:02d}",category="image_generation",status="PASS",started_monotonic=trace_started,trace_id=trace_id,run_id=trace_run_id,attrs={"frame":frame,"backend":payload.get("backend"),"candidate_committed":True})
    result={"returncode":0,"stdout":"","payload":payload,"output":out,"log":log,"attempt":attempt,"scout":scout,"candidate_budget":commit_row,"prompt_package":{"package_sha256":package["package_sha256"],"scene_prompt_sha256":package["scene_prompt_sha256"],"frame_contract_sha256":package["frame_contract_sha256"]},"worker_pool":{"mode":MODE,"codex_session_reuse":False}}
    production_recovery.write_lifecycle(ep, item, "SUCCEEDED", worker_pid=os.getpid(), result=result)
    return result

def self_test():
    assert MODE=="python_warm_pool_codex_ephemeral"
    assert CODEX_SESSION_REUSE is False
    print("IMAGE WORKER POOL SELF-TEST PASS")

if __name__=="__main__": self_test()

# STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE

# STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
