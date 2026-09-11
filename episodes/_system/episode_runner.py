#!/usr/bin/env python3
"""Bounded recovery coordinator; episode-state remains the stage authority."""
from __future__ import annotations
import argparse
import time
import json
from pathlib import Path
import runtime_dag
import runtime_failure_classifier
import runtime_resume_token
import runner_state_store
import runtime_checkpoint
import next_action
import runtime_timeout_policy

TERMINAL = {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}

# STORY_OS_V2_6_2_CONTINUOUS_HOST_LOOP: the image dispatch chain is a local executor, so the
# workflow runner (not only a human) must be able to recognize and run it. Keep the action
# list in one place instead of duplicating the set in every caller.
LOCAL_IMAGE_ACTIONS = {"GENERATE_IMAGES", "RETRY_TECHNICAL_FAILURES", "REPAIR_FAILED_IMAGES"}


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
        image_scheduler.retry_tech(episode)
    workers = int(storyos_config.get_path(storyos_config.load_config(), "production.max_inflight_images"))
    worker_timeout = runtime_timeout_policy.seconds("image_worker_request")
    try:
        if batch_scheduler.should_use(episode):
            return batch_scheduler.run(episode, workers, worker_timeout, None)
        return image_scheduler.run_scheduler_async(episode, workers, worker_timeout, None)
    finally:
        next_action.write(episode)


def execute_cycle(episode: Path) -> int:
    action = next_action.write(episode)
    if local_image_action(action) is not None:
        return run_local_image_action(episode, action)
    return runtime_dag.execute(episode)


def progress_marker(episode:Path):
    queue=next_action.read_json(episode/"meta/production-queue.json")
    return (runtime_dag.state(episode), tuple((x.get("id"),x.get("status"),x.get("attempts"),x.get("output_path"))
        for x in queue.get("items") or []))


def run_episode(episode: Path, *, interval: int = 10, max_loops: int | None = None,
                resume: bool = False, max_attempts: int = 3) -> int:
    episode = Path(episode).resolve()
    if interval < 0 or max_attempts < 1 or (max_loops is not None and max_loops < 1):
        raise ValueError("invalid runner bounds")
    cycles = 0
    failures = 0
    previous_state = None
    idle_cycles = 0
    if resume:
        record_event(episode, {"type": "resume", "token": runtime_resume_token.load(episode)})
    runner_state_store.save(episode, status="RUNNING", resume_enabled=resume)
    while True:
        state = runtime_dag.state(episode)
        if state in TERMINAL:
            valid,note=runtime_dag.validate_target(episode,"PUBLISH_READY")
            if not valid:
                runner_state_store.save(episode,status="HARD_STOP",return_code=23,last_error=note)
                return 23
            runner_state_store.save(episode, status="COMPLETED", state=state)
            record_event(episode, {"type": "completed", "state": state})
            return 0
        if state != previous_state:
            failures = 0
            previous_state = state
        before=progress_marker(episode)
        rc = execute_cycle(episode)
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
                time.sleep(min(interval * 2 ** (failures - 1), 60))
                continue
            runner_state_store.save(episode, status=decision.category, return_code=rc,
                                    attempt=failures, last_action=decision.action)
            return rc
        failures = 0
        if runtime_dag.state(episode) in TERMINAL:
            continue
        if max_loops is not None and cycles >= max_loops:
            runner_state_store.save(episode, status="YIELDED", cycles=cycles)
            return 0
        idle_cycles=idle_cycles+1 if progress_marker(episode)==before else 0
        if idle_cycles>=max_attempts:
            runner_state_store.save(episode,status="CAPABILITY_WAIT",return_code=24,
                last_error="NO_PROGRESS: repeated successful cycles did not advance stage or queue")
            return 24
        time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    # Both public entrypoints use the same ownership lock and heartbeat.
    import persistent_runner_daemon
    return persistent_runner_daemon.run(args.episode, args.interval, args.resume)


if __name__ == "__main__":
    raise SystemExit(main())
