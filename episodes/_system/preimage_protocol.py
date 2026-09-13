#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit and barrier for independently completed PREIMAGE candidates."""
from __future__ import annotations
import datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import authority_commit
import preimage_authority_snapshot
import preimage_task_contract as tasks
import runtime_atomic_store as atomic
import story_json

BARRIER_REL=Path("meta/runtime/preimage-authority-barrier.json")

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def _patches(candidate: dict) -> list[tuple[str,dict]]:
    return [(scope, dict(candidate["payload"][scope])) for scope in candidate["authority_scope"]]

def commit_candidates(ep: Path, snapshot: dict, task_rows: list[dict]) -> dict:
    """Single orchestration path from candidates to committed Snapshot B.

    Each atomic patch compares the latest SHA. Any concurrent authority change
    returns STALE and stops the barrier; it is never overwritten.
    """
    tasks.validate_patch_scopes(task_rows)
    current = preimage_authority_snapshot.sha(Path(ep)/"meta/story-gates.json")
    expected = (snapshot.get("authority_sha256") or {}).get("story_gates")
    if current != expected:
        return {"status":"STALE","reason":"input authority SHA changed","committed":False}
    candidates=[]; patches=[]
    for task in task_rows:
        candidate=tasks.read_candidate(ep,task)
        errors=tasks.verify_candidate(candidate or {},task)
        if errors: return {"status":"FAILED","reason":"; ".join(errors),"committed":False}
        candidates.append(candidate); patches.extend(_patches(candidate))
    scopes={scope for scope,_ in patches}
    result=authority_commit.commit_transaction(ep,"meta/story-gates.json",expected_sha=expected,snapshot_id=snapshot["snapshot_id"],
        task_ids=[task["task_id"] for task in task_rows],node_ids=[task["node_id"] for task in task_rows],patches=patches,
        candidate_paths=[task["candidate_output"] for task in task_rows],
        preflight_validator=lambda: [err for task,candidate in zip(task_rows,candidates) for err in tasks.verify_candidate(candidate,task)],
        replace_existing_scopes=scopes)
    if result["status"] != "PASS": return {"status":result["status"],"committed":False,"transaction":result}
    committed=preimage_authority_snapshot.build(ep,write=True,kind="PREIMAGE_COMMITTED_SNAPSHOT")
    barrier={"schema_version":1,"name":"PREIMAGE_AUTHORITY_READY","not_episode_stage":True,"not_gate_authority":True,
             "canonical_stage_source":"meta/episode-state.json","status":"READY","input_snapshot_id":snapshot["snapshot_id"],
             "committed_snapshot_id":committed["snapshot_id"],"created_at":now(),"commit_count":1}
    atomic.atomic_write_json(Path(ep)/BARRIER_REL,barrier)
    return {"status":"PASS","committed":True,"transaction":result,"committed_snapshot":committed,"barrier":barrier}

def barrier_ready(ep: Path) -> bool:
    row=story_json.read_json(Path(ep)/BARRIER_REL,default={}) or {}
    return row.get("status")=="READY" and bool(row.get("committed_snapshot_id"))

def execute_local(ep: Path, executor, *, max_workers: int = 4) -> dict:
    """Execute distinct local task invocations and then commit verified results.

    ``executor(task)`` is deliberately injected: production supplies one scoped
    worker invocation per task; tests supply a bounded fake worker.  Completion
    remains evidence/candidate based rather than scheduler asserted.
    """
    source=preimage_authority_snapshot.build(ep,write=True,kind="PREIMAGE_INPUT_SNAPSHOT")
    rows=tasks.plan_tasks(ep,source,resume=True)
    pending=[x for x in rows if x["status"] != "REUSED"]
    import threading
    peak=0; active=0; metrics_lock=threading.Lock(); results=[]
    def call(task):
        nonlocal peak,active
        with metrics_lock:
            active += 1; peak=max(peak,active)
        try:
            tasks.update_task_state(ep,task,"RUNNING")
            return task,executor(task)
        finally:
            with metrics_lock: active -= 1
    with ThreadPoolExecutor(max_workers=min(max_workers,len(pending) or 1),thread_name_prefix="story-os-preimage") as pool:
        futures=[]
        for task in pending: futures.append(pool.submit(call,task))
        for future in as_completed(futures):
            task,value=future.result()
            candidate=tasks.read_candidate(ep,task)
            errors=tasks.verify_candidate(candidate or {},task)
            if value not in (0, None) or errors:
                tasks.update_task_state(ep,task,"FAILED",reason="; ".join(errors) or f"worker rc={value}")
                results.append({"task_type":task["task_type"],"status":"FAILED"})
            else:
                tasks.update_task_state(ep,task,"COMPLETED")
                results.append({"task_type":task["task_type"],"status":"COMPLETED"})
    if any(x["status"]=="FAILED" for x in results):
        return {"status":"FAILED","observed_preimage_parallelism_peak":peak,"measurement_method":"active_worker_enter_exit","test_evidence":False,"production_observed":False,"tasks":results}
    committed=commit_candidates(ep,source,rows)
    return {"status":committed["status"],"observed_preimage_parallelism_peak":peak,"measurement_method":"active_worker_enter_exit","test_evidence":False,"production_observed":False,"tasks":results,**committed}
