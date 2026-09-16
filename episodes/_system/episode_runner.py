#!/usr/bin/env python3
"""Bounded recovery coordinator; episode-state remains the stage authority."""
from __future__ import annotations
import argparse
import time
import json
from pathlib import Path
import effective_config
import runtime_dag
import runtime_failure_classifier
import runtime_resume_token
import runner_state_store
import runtime_checkpoint
import next_action
import runtime_timeout_policy
import runtime_evidence_contract
import episode_lifecycle
import episode_performance
import runtime_portability
import runtime_ownership

TERMINAL = {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}

# STORY_OS_V2_6_2_CONTINUOUS_HOST_LOOP: the image dispatch chain is a local executor, so the
# workflow runner (not only a human) must be able to recognize and run it. Keep the action
# list in one place instead of duplicating the set in every caller.
LOCAL_IMAGE_ACTIONS = {"GENERATE_IMAGES", "RETRY_TECHNICAL_FAILURES", "REPAIR_FAILED_IMAGES", "REFRESH_AUTHORITY_IMAGES"}


def record_event(episode, event):
    # Merge lifecycle evidence without overwriting DAG checkpoints/step runs.
    from runtime_atomic_store import update_json
    def mutate(data):
        data = runtime_checkpoint.ensure_shape(data)
        data.setdefault("runner_events", []).append({"at": runtime_checkpoint.now(), **event})
        data["runner_events"] = data["runner_events"][-100:]
    update_json(episode / runtime_checkpoint.REL, dict, mutate)


def local_image_action(action: dict) -> str | None:
    """Return the locally executable image action name, or None when the host owns it.

    Pure decision helper: callers must not need to spawn anything to know whether the
    pending action is image work that this machine executes itself.
    """
    if not isinstance(action, dict):
        return None
    if str(action.get("executor") or "") != "CODEX_IMAGE":
        return None
    name = str(action.get("action") or "")
    return name if name in LOCAL_IMAGE_ACTIONS else None


def run_local_image_action(episode: Path, action: dict) -> int:
    """Execute the local image action and refresh next-action evidence afterwards."""
    name = local_image_action(action)
    if name is None:
        raise ValueError(f"not a local image action: {action.get('action') if isinstance(action, dict) else action}")
    import image_scheduler
    import batch_scheduler
    import storyos_config
    if name == "RETRY_TECHNICAL_FAILURES":
        retry = image_scheduler.retry_tech(episode) or {}
        if int(retry.get("requeued") or 0) == 0 and (retry.get("exhausted_frames") or retry.get("non_retryable_frames")):
            next_action.write(episode)
            # The queue is now deliberately waiting on an external provider/capability.
            # rc=21 would make the resident Runner call it another technical crash;
            # rc=24 is the existing non-retryable CAPABILITY_WAIT protocol result.
            return 24
    elif name == "REPAIR_FAILED_IMAGES":
        import auto_repair_enqueue
        auto_repair_enqueue.enqueue_marked_repairs(episode)
    elif name == "REFRESH_AUTHORITY_IMAGES":
        import auto_repair_enqueue
        refreshed = auto_repair_enqueue.enqueue_authority_refreshes(episode)
        if int(refreshed.get("enqueued") or 0) == 0 and not refreshed.get("frames"):
            next_action.write(episode)
            return 21
    workers = int(storyos_config.get_path(storyos_config.load_config(), "production.max_inflight_images"))
    worker_timeout = runtime_timeout_policy.seconds("image_worker_request")
    try:
        if batch_scheduler.should_use(episode):
            return batch_scheduler.run(episode, workers, worker_timeout, None)
        return image_scheduler.run_scheduler_async(episode, workers, worker_timeout, None)
    finally:
        next_action.write(episode)


def local_host_action(action: dict) -> str | None:
    """Return a deliberately allowlisted local host action, if one exists."""
    name = local_image_action(action)
    if name is not None:
        return name
    import vision_review_executor
    name = vision_review_executor.local_vision_action(action)
    if name is not None:
        return name
    import machine_action_executor
    name = machine_action_executor.local_machine_action(action)
    if name is not None:
        return name
    # Legacy migration fallback only. Golden Path WORK actions are consumed by
    # the current ChatGPT WORK host through DevSpace, not by spawning providers.
    import work_host_action_executor
    return work_host_action_executor.local_work_action(action)


def run_local_host_action(episode: Path, action: dict) -> int:
    if local_image_action(action) is not None:
        return run_local_image_action(episode, action)
    import vision_review_executor
    if vision_review_executor.local_vision_action(action) is not None:
        try:
            result = vision_review_executor.execute(episode, action)
            status = str(result.get("status") or "FAIL").upper()
            record_event(episode, {"type": "vision_host_action", "action": action.get("action"), "status": status})
            # A content FAIL that has been converted into a bounded repair is
            # successful host-loop progress. NEEDS_USER is also a completed
            # review action; next_action owns the subsequent hard stop.
            if status in {"PASS", "REUSED", "REPAIR_ENQUEUED", "NEEDS_USER", "FAIL"}:
                # Content FAIL is a completed review outcome, not an infrastructure
                # failure. The review has already persisted SHA-bound findings;
                # next_action owns bounded candidate/repair selection or the final
                # NEEDS_USER hard stop. Returning a process failure here used to
                # misclassify valid content review results as host technical faults.
                return 0
            if status in {"TECHNICAL_FAILURE", "TECH_FAILED"}:
                return 21
            return 2
        except vision_review_executor.VisionReviewError as exc:
            record_event(episode, {"type": "vision_host_action_failed", "action": action.get("action"), "error": str(exc)})
            return 21
        finally:
            next_action.write(episode)
    import machine_action_executor
    if machine_action_executor.local_machine_action(action) is not None:
        try:
            result = machine_action_executor.execute(episode, action)
            status = str(result.get("status") or "FAIL").upper()
            record_event(episode, {"type": "machine_host_action", "action": action.get("action"), "status": status})
            return 0 if status in {"PASS", "REUSED"} else 2
        except machine_action_executor.MachineActionError as exc:
            record_event(episode, {"type": "machine_host_action_failed", "action": action.get("action"), "error": str(exc)})
            return 21
        finally:
            next_action.write(episode)
    import work_host_action_executor
    if work_host_action_executor.local_work_action(action) is None:
        raise ValueError(f"not a locally executable host action: {action}")
    try:
        result = work_host_action_executor.execute(episode, action)
        return 0 if str((result.get("result") or {}).get("status") or "PASS") == "PASS" else 2
    except work_host_action_executor.WorkHostActionError as exc:
        record_event(episode, {"type": "work_host_action_failed", "action": action.get("action"), "error": str(exc)})
        return 21
    finally:
        next_action.write(episode)


def execute_cycle(episode: Path, codex: str | None = None, timeout: int | None = None) -> int:
    # W-101: once an Episode enters the modern resident Runner, production
    # completion requires all runtime evidence sinks. Historical Episodes are not
    # fabricated/backfilled; the marker is the explicit compatibility boundary.
    runtime_evidence_contract.arm(episode)
    # Record what was in force before acting on it (W-96). After the fact, a run
    # that took STORY_OS_IMAGE_RUNTIME=... was indistinguishable from one that
    # did not: the config file said one thing, the behaviour was another, and no
    # evidence said which. Written every cycle because a long run can span a
    # config edit, and "which value did *this* step use" is the question asked.
    effective_config.write(episode)
    action = next_action.write(episode)
    if local_host_action(action) is not None:
        return run_local_host_action(episode, action)
    # The resident Driver has to be able to run a scoped Codex step itself. Without
    # this the only lane that can execute one is workflow_runner (the bounded
    # `run --full-auto` drain), so "the single resident Driver" would stop at the
    # first step that needs Codex and wait for a host that may never come back.
    rc = runtime_dag.execute(episode, codex=codex, timeout=timeout)
    # A DAG step can legitimately return HOST_WAIT after it has materialized the
    # *next* action.  If that freshly-derived action is now owned by this machine,
    # handing rc=20 to the resident loop would incorrectly terminate an otherwise
    # autonomous run and require an operator to type "continue".  Reconcile once
    # after HOST_WAIT and consume that local action; genuine host-owned waits still
    # return unchanged and therefore never spin.
    if runtime_failure_classifier.classify(rc).category == "HOST_WAIT":
        following = next_action.write(episode)
        if local_host_action(following) is not None:
            return run_local_host_action(episode, following)
    return rc


def progress_marker(episode:Path):
    """Bounded resident-loop progress fingerprint, not a new authority.

    Stage + queue alone misses legitimate metadata-only progress such as
    APPLY_VISUAL_LOCK_WEAK_PASS: the ledger and next action advance while no image
    row or stage changes.  Include those existing facts so three successful local
    machine actions cannot be misclassified as CAPABILITY_WAIT/no-progress.
    """
    queue=next_action.read_json(episode/"meta/production-queue.json")
    ledger=next_action.read_json(episode/"meta/production-ledger.json")
    action=next_action.load(episode)
    frames=ledger.get("frames") or {}
    ledger_marker=tuple(sorted(
        (str(k), str(v.get("status") or ""), int(v.get("content_repairs_used") or 0))
        for k,v in frames.items() if isinstance(v,dict)
    )) if isinstance(frames,dict) else ()
    action_marker=(
        str(action.get("action") or ""),
        str(action.get("executor") or ""),
        tuple(int(x) for x in (action.get("frames") or []) if str(x).isdigit()),
        bool(action.get("auto_recoverable")),
        bool(action.get("hard_stop")),
    ) if isinstance(action,dict) else ()
    return (
        runtime_dag.state(episode),
        tuple((x.get("id"),x.get("status"),x.get("attempts"),x.get("output_path"))
            for x in queue.get("items") or []),
        ledger_marker,
        action_marker,
    )


def run_episode(episode: Path, *, interval: int = 10, max_loops: int | None = None,
                resume: bool = False, max_attempts: int = 3,
                codex: str | None = None, timeout: int | None = None) -> int:
    episode = Path(episode).resolve()
    runtime_portability.assert_episode_directory(episode)
    # W-11: resident Runner is a production owner, not a neutral observer.
    # Refuse to mutate Episode production facts unless the control-plane record
    # explicitly assigns production to V3_RUNTIME.
    runtime_ownership.assert_v3_owner("episode_runner.run_episode")
    if interval < 0 or max_attempts < 1 or (max_loops is not None and max_loops < 1):
        raise ValueError("invalid runner bounds")
    cycles = 0
    failures = 0
    previous_state = None
    idle_cycles = 0
    perf_session = episode_performance.safe_begin_execution_session(
        episode, source="episode_runner", metadata={"resume": bool(resume)})
    episode_performance.safe_transition_execution_state(
        episode, "ACTIVE", session_id=perf_session, source="episode_runner")
    if resume:
        record_event(episode, {"type": "resume", "token": runtime_resume_token.load(episode)})
    runner_state_store.save(episode, status="RUNNING", resume_enabled=resume)
    while True:
        if episode_lifecycle.is_terminal(episode):
            disposition = episode_lifecycle.disposition(episode)
            runner_state_store.save(episode, status="TERMINATED", disposition=disposition)
            record_event(episode, {"type": "terminated", "disposition": disposition})
            episode_performance.safe_transition_execution_state(episode,"IDLE",session_id=perf_session,source="episode_runner")
            episode_performance.safe_finish_execution_session(episode,session_id=perf_session,status="TERMINATED")
            return 0
        state = runtime_dag.state(episode)
        if state in TERMINAL:
            valid,note=runtime_dag.validate_target(episode,"PUBLISH_READY")
            if not valid:
                runner_state_store.save(episode,status="HARD_STOP",return_code=23,last_error=note)
                episode_performance.safe_transition_execution_state(episode,"IDLE",session_id=perf_session,source="episode_runner")
                episode_performance.safe_finish_execution_session(episode,session_id=perf_session,status="HARD_STOP")
                return 23
            runner_state_store.save(episode, status="COMPLETED", state=state)
            record_event(episode, {"type": "completed", "state": state})
            episode_performance.safe_transition_execution_state(episode,"IDLE",session_id=perf_session,source="episode_runner")
            episode_performance.safe_finish_execution_session(episode,session_id=perf_session,status="COMPLETE")
            return 0
        if state != previous_state:
            failures = 0
            previous_state = state
        before=progress_marker(episode)
        rc = execute_cycle(episode, codex=codex, timeout=timeout)
        cycles += 1
        decision = runtime_failure_classifier.classify(rc)
        record_event(episode, {"type": "cycle", "return_code": rc, "cycle": cycles,
                               "category": decision.category})
        if rc != 0:
            failures += 1
            runtime_resume_token.save(episode, stage=str(state), step=decision.action,
                attempt=failures, failure_category=decision.category,
                last_event=decision.reason, resume_action=decision.action)
            if decision.retryable and failures < max_attempts:
                runner_state_store.save(episode, status="RETRY_WAIT", attempt=failures)
                episode_performance.safe_transition_execution_state(
                    episode,"IDLE",session_id=perf_session,source="episode_runner",
                    metadata={"reason":"technical_retry_backoff"})
                time.sleep(min(interval * 2 ** (failures - 1), 60))
                episode_performance.safe_transition_execution_state(
                    episode,"ACTIVE",session_id=perf_session,source="episode_runner")
                continue
            runner_state_store.save(episode, status=decision.category, return_code=rc,
                                    attempt=failures, last_action=decision.action)
            wait_state=episode_performance.execution_state_for_result(
                rc,next_action.load(episode))
            episode_performance.safe_transition_execution_state(
                episode,wait_state,session_id=perf_session,source="episode_runner")
            if wait_state=="IDLE":
                episode_performance.safe_finish_execution_session(
                    episode,session_id=perf_session,status=decision.category)
            return rc
        failures = 0
        if runtime_dag.state(episode) in TERMINAL:
            continue
        if max_loops is not None and cycles >= max_loops:
            runner_state_store.save(episode, status="YIELDED", cycles=cycles)
            episode_performance.safe_transition_execution_state(episode,"IDLE",session_id=perf_session,source="episode_runner")
            episode_performance.safe_finish_execution_session(episode,session_id=perf_session,status="YIELDED")
            return 0
        idle_cycles=idle_cycles+1 if progress_marker(episode)==before else 0
        if idle_cycles>=max_attempts:
            runner_state_store.save(episode,status="CAPABILITY_WAIT",return_code=24,
                last_error="NO_PROGRESS: repeated successful cycles did not advance stage or queue")
            episode_performance.safe_transition_execution_state(
                episode,"IDLE",session_id=perf_session,source="episode_runner",metadata={"reason":"no_progress"})
            episode_performance.safe_finish_execution_session(
                episode,session_id=perf_session,status="CAPABILITY_WAIT")
            return 24
        episode_performance.safe_transition_execution_state(
            episode,"IDLE",session_id=perf_session,source="episode_runner",metadata={"reason":"runner_interval"})
        time.sleep(interval)
        episode_performance.safe_transition_execution_state(
            episode,"ACTIVE",session_id=perf_session,source="episode_runner")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--codex", default=None)
    args = parser.parse_args()
    # Both public entrypoints use the same ownership lock and heartbeat.
    import persistent_runner_daemon
    return persistent_runner_daemon.run(args.episode, args.interval, args.resume, args.codex)


if __name__ == "__main__":
    raise SystemExit(main())
