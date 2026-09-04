#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Warm Python image worker adapter.

Reuses the scheduler Python process/module imports, but deliberately does NOT reuse Codex
conversation state. Current Codex transport remains ephemeral until the CLI exposes a safe
persistent image-generation daemon/session contract.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import codex_subscription_image as backend
import fast_frame_scout as frame_scout
import image_model_policy
import prompt_package
import runtime_trace
import raw_candidate_budget  # STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE
import time

MODE="python_warm_pool_codex_ephemeral"
CODEX_SESSION_REUSE=False

def execute(ep,item,timeout,codex):
    frame=int(item["frame"]); attempt=max(1,int(item.get("attempts") or 1))
    out=ep/"media/candidates/scheduled"/f"{frame:02d}-{item['id']}-a{attempt}.png"
    log=ep/"meta/image-workers"/f"{frame:02d}-{item['id']}-a{attempt}.jsonl"
    out.parent.mkdir(parents=True,exist_ok=True); log.parent.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[2]
    prompt=(root/item["prompt_file"]).resolve()
    refs=[(root/x["path"]).resolve() for x in item.get("references") or []]
    model=str(item.get("model") or image_model_policy.for_episode(ep)["model"])
    quality=str(item.get("quality") or image_model_policy.for_episode(ep)["quality"])
    package=prompt_package.compile_frame(ep,frame,prompt,write=True)
    budget_kind=raw_candidate_budget.kind_for_queue_item(item)
    budget_token=str(item["id"])
    budget_ok,budget_row=raw_candidate_budget.claim(ep,frame,budget_kind,reason=f"formal_generation_entrypoint scope={item.get('scope')} attempt={attempt}",token=budget_token)
    if not budget_ok:
        return {"returncode":98,"stdout":"RAW_CANDIDATE_BUDGET_EXHAUSTED: "+str(budget_row),"payload":None,"output":None,"log":log,"attempt":attempt,"scout":None,"budget":budget_row}
    ns=argparse.Namespace(
        episode_dir=ep,frame=f"{frame:02d}",prompt_file=prompt,output=out,log=log,
        reference=refs,timeout=timeout,codex=codex,image_model=model,image_quality=quality,overwrite=False,
        _raw_candidate_budget_preclaimed=True,_raw_candidate_token=budget_token,candidate_kind=budget_kind)
    trace_span=runtime_trace.start_span(ep,f"image.generate.frame.{frame:02d}",category="image_generation",attrs={"frame":frame,"model":model,"quality":quality})
    trace_started=time.monotonic()
    try:
        payload=backend.generate_for_frame(ns)
        scout=None
        if out.is_file() and frame_scout.required(ep) and not bool(item.get("_defer_scout")):
            scout=frame_scout.evaluate_candidate(ep,frame,out,codex_raw=codex,timeout=min(240,max(60,timeout)))
        runtime_trace.end_span(ep,trace_span,name=f"image.generate.frame.{frame:02d}",category="image_generation",status="PASS",started_monotonic=trace_started,attrs={"frame":frame,"backend":payload.get("backend")})
        return {"returncode":0,"stdout":"","payload":payload,"output":out,"log":log,"attempt":attempt,"scout":scout,"prompt_package":{"package_sha256":package["package_sha256"],"frame_contract_sha256":package["frame_contract_sha256"]},"worker_pool":{"mode":MODE,"codex_session_reuse":False}}
    except Exception as exc:
        raw_candidate_budget.release(ep,budget_token,reason="image_worker_exception")
        runtime_trace.end_span(ep,trace_span,name=f"image.generate.frame.{frame:02d}",category="image_generation",status="FAILED",started_monotonic=trace_started,attrs={"frame":frame,"error":str(exc)})
        return {"returncode":99,"stdout":str(exc),"payload":None,"output":None,"log":log,"attempt":attempt,"scout":None,"worker_pool":{"mode":MODE,"codex_session_reuse":False}}

def self_test():
    assert MODE=="python_warm_pool_codex_ephemeral"
    assert CODEX_SESSION_REUSE is False
    print("IMAGE WORKER POOL SELF-TEST PASS")

if __name__=="__main__": self_test()

# STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE
