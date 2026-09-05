#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explicit Runtime Mode routing/guards for Story OS V2.1 R2.

This module does not create Episode stages. It only constrains how an existing
seven-stage Episode may be executed for resume / repair_only / release_only /
data_review and validates preconditions before expensive work begins.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
STAGES = ("IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED")
SPECIAL = {"repair_only","release_only","data_review"}

def read_json(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
    return data

def state(ep: Path) -> str | None:
    p=ep/"meta/episode-state.json"
    return str(read_json(p).get("current_state") or "") if p.is_file() else None

def at_least(cur: str | None, target: str) -> bool:
    return cur in STAGES and target in STAGES and STAGES.index(cur) >= STAGES.index(target)

def run(cmd: list[object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(x) for x in cmd],cwd=ROOT,check=False,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")

def validate_target(ep: Path, target: str) -> tuple[bool,str]:
    out=[]
    for script in ("validate_episode.py","machine_gate.py","evidence_gate.py"):
        cp=run([sys.executable,SYSTEM/script,ep,"--target",target]); out.append(cp.stdout)
        if cp.returncode != 0:
            return False,"\n".join(out)[-5000:]
    return True,"PASS"

def guard(ep: Path, mode: str) -> list[str]:
    cur=state(ep); errors=[]
    if mode == "resume":
        if not (ep/"meta/runtime-checkpoint.json").is_file():
            errors.append("RESUME_CHECKPOINT_MISSING")
    elif mode == "image_continue":
        if not at_least(cur,"STORYBOARD_LOCKED"):
            errors.append(f"IMAGE_CONTINUE_REQUIRES_STORYBOARD_LOCKED:current={cur}")
    elif mode == "repair_only":
        if cur not in {"VISUAL_CALIBRATED","PRODUCTION_PASSED"}:
            errors.append(f"REPAIR_ONLY_REQUIRES_VISUAL_CALIBRATED_OR_PRODUCTION_PASSED:current={cur}")
    elif mode == "release_only":
        if not at_least(cur,"PRODUCTION_PASSED") or cur in {"PUBLISHED","DATA_REVIEWED"}:
            errors.append(f"RELEASE_ONLY_REQUIRES_PRODUCTION_PASSED_OR_PUBLISH_READY:current={cur}")
    elif mode == "data_review":
        if cur not in {"PUBLISHED","DATA_REVIEWED"}:
            errors.append(f"DATA_REVIEW_REQUIRES_PUBLISHED:current={cur}")
    elif mode == "preproduction_only":
        if cur in {"VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED"}:
            errors.append(f"PREPRODUCTION_ONLY_REFUSES_POST_IMAGE_STATE:current={cur}")
    return errors

def _run_scoped(ep: Path, step: str, codex: str | None, timeout: int, mode: str) -> int:
    import runtime_router
    import product_runtime_adapter
    active_runtime,_=runtime_router.detect()
    if active_runtime in {"WORK","WEB"} and not codex:
        request=product_runtime_adapter.build_request(
            ep,runtime=active_runtime,mode=mode,resume=True,source=f"runtime_mode_router:{step}")
        product_runtime_adapter.print_request(request)
        return product_runtime_adapter.HOST_ACTION_REQUIRED_RC
    import scoped_codex_worker
    rc,log=scoped_codex_worker.run_step(ep,step,codex_raw=codex,timeout=min(timeout,3600))
    print(f"RUNTIME MODE {step}: rc={rc} log={log}")
    return rc

def dispatch_special(ep: Path, mode: str, codex: str | None, timeout: int) -> int | None:
    """Return None for normal DAG modes; otherwise execute the bounded special mode."""
    if mode not in SPECIAL:
        return None
    cur=state(ep)
    if mode == "repair_only":
        # The PRODUCTION scoped directive inspects effective_execution_mode and, in
        # repair_only, is forbidden to generate untouched originals or rewrite story.
        return _run_scoped(ep,"PRODUCTION",codex,timeout,mode)
    if mode == "release_only":
        if cur == "PUBLISH_READY":
            ok,msg=validate_target(ep,"PUBLISH_READY")
            if not ok:
                print("RELEASE_ONLY_EXISTING_PUBLISH_READY_INVALID")
                print(msg)
                return 4
            print("RELEASE_ONLY_REUSE: PUBLISH_READY already valid")
            return 0
        rc=_run_scoped(ep,"RELEASE",codex,timeout,mode)
        if rc != 0: return rc
        ok,msg=validate_target(ep,"PUBLISH_READY")
        if not ok:
            print("RELEASE_ONLY_POSTCONDITION_FAIL")
            print(msg)
            return 4
        return 0
    # data_review
    if cur == "DATA_REVIEWED":
        cp=run([sys.executable,SYSTEM/"post_publish_review.py","verify",ep,"--require-48h"])
        print(cp.stdout)
        return cp.returncode
    cp=run([sys.executable,SYSTEM/"post_publish_review.py","complete",ep])
    print(cp.stdout)
    return cp.returncode

def self_test():
    assert "repair_only" in SPECIAL and "data_review" in SPECIAL
    assert at_least("PUBLISH_READY","PRODUCTION_PASSED")
    assert not at_least("STORYBOARD_LOCKED","VISUAL_CALIBRATED")
    print("RUNTIME MODE ROUTER HOTFIX SELF-TEST PASS")

if __name__=="__main__":
    self_test()
