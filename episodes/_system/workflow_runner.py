#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 workflow runner foundation.

Phase 1 centralizes planning/runtime/checkpoint/performance while keeping the proven
CODEX orchestrator as a compatibility execution adapter. Later V2.1 phases can replace
individual adapter steps without changing the public `story_os run` entry point.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from runtime_router import detect
from story_os_contract import story_os_version
import workflow_performance as perf
import workflow_observability as obs
import runtime_request as runtime_request_contract
import image_model_policy
import runtime_dag
import runtime_execution
import performance_guard_v211  # STORY_OS_V211_PERF_RECOVERY
import storyos_config
import runtime_trace
import request_router
import product_runtime_adapter
import next_action
import runtime_timeout_policy

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
_CONFIG = storyos_config.load_config()
CONTRACT = ROOT / str(storyos_config.get_path(_CONFIG, "paths.workflow_contract"))

# STORY_OS_V2_6_2_CONTINUOUS_HOST_LOOP: `runtime.continuous_host_loop` used to have no reader
# anywhere, so on WORK/WEB the DAG returned HOST_WAIT (rc=20) for every scoped step and the
# image dispatch chain stayed manual (`image_scheduler.py run` by hand). The bound below keeps
# the loop finite: only locally executable actions run, and only until the DAG stops asking.
HOST_LOOP_MAX_CYCLES = 12


def resolve_episode(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep


def run(args: list[object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(x) for x in args], cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")


def load_contract() -> dict:
    storyos_config.load_config()
    storyos_config.load_index()
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    version = str(data.get("workflow_version") or "") if isinstance(data, dict) else ""
    if not isinstance(data, dict) or not version.startswith("2.1"):
        raise SystemExit(f"invalid V2.1 workflow contract: {version!r}")
    return data


def plan(ep: Path) -> dict:
    cp = run([sys.executable, SYSTEM / "incremental_closure.py", "plan", ep, "--json"])
    if cp.returncode != 0:
        raise SystemExit(cp.stdout[-2500:])
    data = json.loads(cp.stdout)
    runtime, reason = detect()
    return {"story_os_version": story_os_version(), "workflow_version": load_contract()["workflow_version"], "runtime": runtime, "runtime_reason": reason, "closure": data}


def record_checkpoint_step(ep: Path, step: str, status: str, elapsed: float, note: str = "") -> None:
    run([sys.executable, SYSTEM / "runtime_checkpoint.py", "record-step", ep, "--step", step, "--status", status, "--finished-at", perf.now(), "--note", f"{note} elapsed={elapsed:.3f}s"])


def continuous_host_loop_enabled() -> bool:
    return bool(storyos_config.get_path(_CONFIG, "runtime.continuous_host_loop", False))


def host_loop_step(ep: Path) -> tuple[bool, str]:
    """Run at most one locally executable host action.

    Returns ``(progressed, detail)``; ``progressed=False`` means the pending action needs the
    real host (Codex/ChatGPT Work), so the DAG result must be handed back unchanged.
    """
    import episode_runner
    action = next_action.write(ep)
    name = episode_runner.local_image_action(action)
    if name is None:
        return False, str(action.get("action") or "UNKNOWN")
    rc = episode_runner.run_local_image_action(ep, action)
    return True, f"{name} rc={rc}"


def advance_host_loop(ep: Path, *, codex: str | None, timeout: int, run_id: str, trace_id: str,
                      max_cycles: int | None = None) -> tuple[int, str]:
    """Drain locally executable host actions, resuming the DAG between them.

    Stops on the first DAG return code that is not HOST_WAIT, when no local executor owns the
    pending action, or at the cycle cap. Never turns a required host decision into a PASS.
    """
    cap = int(max_cycles or HOST_LOOP_MAX_CYCLES)
    rc = product_runtime_adapter.HOST_ACTION_REQUIRED_RC
    note = ""
    for cycle in range(1, cap + 1):
        progressed, detail = host_loop_step(ep)
        if not progressed:
            return rc, f"{note} stop_cycle={cycle} host_owns={detail}".strip()
        note = f"{note} cycle={cycle} {detail};".strip()
        rc = runtime_dag.execute(ep, codex=codex, timeout=timeout, run_id=run_id, trace_id=trace_id)
        if rc != product_runtime_adapter.HOST_ACTION_REQUIRED_RC:
            return rc, f"{note} dag_rc={rc}".strip()
    return rc, f"{note} max_cycles={cap}".strip()


def execute(ep: Path, *, resume: bool, full_auto: bool, codex: str | None, timeout: int, request_file: str | None = None) -> int:
    if not full_auto:
        raise SystemExit("run/resume requires explicit --full-auto")
    started = time.monotonic()
    request_data = None
    if request_file:
        incoming=runtime_request_contract.read_json(Path(request_file).resolve())
        incoming_errors=runtime_request_contract.validate_request(incoming)
        if incoming_errors: raise SystemExit("invalid runtime request: " + "; ".join(incoming_errors))
        existing=runtime_request_contract.effective_for_episode(ep)
        if existing and incoming.get("mode")=="image_continue":
            runtime_execution.set_mode(ep,"image_continue","request_file_execution_override")
        else:
            runtime_request_contract.bind_request(Path(request_file), ep, force=False)
    request_data = runtime_request_contract.effective_for_episode(ep)
    if request_data:
        errors = runtime_request_contract.validate_request(request_data)
        if errors: raise SystemExit("invalid runtime request: " + "; ".join(errors))
    runtime, reason = detect()
    run([sys.executable, SYSTEM / "runtime_checkpoint.py", "init", ep, "--runtime", runtime, "--full-auto"])
    if runtime not in {"WORK", "WEB", "CODEX"}:
        raise SystemExit(f"unsupported runtime: {runtime}")
    run_id = perf.start_run(ep, runtime, "resume" if resume else "run")
    route_decision = request_router.route_episode(ep, request_data, write=True) if request_data else None
    trace_id = runtime_trace.start_run(ep, run_id, request_data, runtime, route_decision)
    if route_decision:
        runtime_trace.route_event(ep, route_decision)
    try:
        execution_mode = str(((request_data or {}).get("runtime") or {}).get("execution_mode") or storyos_config.get_path(_CONFIG,"runtime.execution_mode"))
        if runtime in {"WORK", "WEB"} or execution_mode == "dag":
            rc = runtime_dag.execute(ep, codex=codex, timeout=timeout, run_id=run_id, trace_id=trace_id)
            host_loop_note = ""
            if rc == product_runtime_adapter.HOST_ACTION_REQUIRED_RC and continuous_host_loop_enabled():
                t_loop = time.monotonic()
                rc, host_loop_note = advance_host_loop(ep, codex=codex, timeout=timeout, run_id=run_id, trace_id=trace_id)
                loop_elapsed = time.monotonic() - t_loop
                loop_status = "HOST_WAIT" if rc == product_runtime_adapter.HOST_ACTION_REQUIRED_RC else ("PASS" if rc == 0 else "FAILED")
                perf.record_step(ep, run_id, "HOST_LOOP", loop_status, loop_elapsed, host_loop_note[:500])
                record_checkpoint_step(ep, "HOST_LOOP", loop_status, loop_elapsed, host_loop_note[:400])
            total = time.monotonic() - started
            final_status = "COMPLETE" if rc == 0 else ("HOST_WAIT" if rc == product_runtime_adapter.HOST_ACTION_REQUIRED_RC else "BLOCKED")
            perf.finish_run(ep, run_id, final_status, total)
            try: performance_guard_v211.observe(ep, run_id, context="DAG_FINISH")
            except Exception: pass
            try:
                obs.collect(ep, write=True)
            except Exception:
                pass
            try: next_action.write(ep)
            except Exception: pass
            runtime_trace.finish_run(ep, trace_id, run_id, final_status, note=f"runtime_dag {host_loop_note}".strip())
            return rc  # RUNTIME_DAG_V1
        t0 = time.monotonic()
        p = plan(ep)
        elapsed = time.monotonic() - t0
        closure_action = str((p.get("closure") or {}).get("action") or "UNKNOWN")
        perf.record_step(ep, run_id, "INCREMENTAL_PLAN", "PASS", elapsed, closure_action)
        record_checkpoint_step(ep, "INCREMENTAL_PLAN", "PASS", elapsed, closure_action)

        cmd = [sys.executable, SYSTEM / "codex_auto_orchestrator.py", "resume" if resume else "run", ep, "--full-auto", "--timeout", str(timeout)]
        if codex:
            cmd += ["--codex", codex]
        if request_data:
            cmd += ["--runtime-request", str(ep / runtime_request_contract.EPISODE_REL)]
        t1 = time.monotonic()
        child = subprocess.run([str(x) for x in cmd], cwd=ROOT, check=False)
        child_elapsed = time.monotonic() - t1
        child_status = "PASS" if child.returncode == 0 else "FAILED"
        perf.record_step(ep, run_id, "CODEX_COMPAT_ADAPTER", child_status, child_elapsed, f"rc={child.returncode}")
        record_checkpoint_step(ep, "CODEX_COMPAT_ADAPTER", child_status, child_elapsed, f"rc={child.returncode}")
        total = time.monotonic() - started
        perf.finish_run(ep, run_id, "COMPLETE" if child.returncode == 0 else "FAILED", total)
        try: performance_guard_v211.observe(ep, run_id, context="COMPAT_FINISH")
        except Exception: pass
        try:
            obs.collect(ep, write=True)
        except Exception:
            pass
        runtime_trace.finish_run(ep, trace_id, run_id, "COMPLETE" if child.returncode == 0 else "FAILED", note="compat_adapter")
        return child.returncode
    except BaseException:
        total = time.monotonic() - started
        try:
            perf.finish_run(ep, run_id, "BLOCKED", total)
            try: performance_guard_v211.observe(ep, run_id, context="EXCEPTION_FINISH")
            except Exception: pass
        except Exception:
            pass
        try:
            obs.collect(ep, write=True)
        except Exception:
            pass
        try:
            runtime_trace.finish_run(ep, trace_id, run_id, "BLOCKED", note="workflow_exception")
        except Exception:
            pass
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("episode_dir")
    for name in ("run", "resume"):
        p = sub.add_parser(name); p.add_argument("episode_dir"); p.add_argument("--full-auto", action="store_true"); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=None); p.add_argument("--request-file")
    p = sub.add_parser("performance"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        data = load_contract()
        assert data["rules"]["zip_is_delivery_adapter_not_stage_gate"] is True
        assert "RESTORE" in data["steps"]
        assert data["rules"].get("max_parallel_image_workers") == 3
        assert data["rules"].get("production_ledger_single_writer") is True
        assert "IMAGE_WAVES" in data["steps"]
        assert data["rules"].get("fast_scout_never_final_pass") is True
        assert data["rules"].get("delivery_consumes_verified_snapshot") is True
        assert "FAST_FRAME_SCOUT" in data["steps"]
        assert "FINAL_CANDIDATE_SNAPSHOT" in data["steps"]
        assert data["rules"].get("legacy_no_evidence_fabrication") is True
        assert data["rules"].get("post_publish_manifest_immutable") is True
        assert data["rules"].get("data_reviewed_requires_48h") is True
        assert "PUBLISH_RECORD" in data["steps"]
        assert "DATA_REVIEWED_GATE" in data["steps"]
        assert image_model_policy.DEFAULT_MODEL == "gpt-image-2"
        assert data["rules"].get("current_visual_lock_calibration_count") == 4
        assert (ROOT / "runtimes/runtime-dag.json").is_file()
        print("WORKFLOW RUNNER V2.1 SELF-TEST PASS | PHASE910")
        return 0
    ep = resolve_episode(args.episode_dir)
    if args.cmd == "plan":
        print(json.dumps(plan(ep), ensure_ascii=False, indent=2)); return 0
    if args.cmd == "performance":
        print(json.dumps(perf.read(ep), ensure_ascii=False, indent=2)); return 0
    return execute(ep, resume=args.cmd == "resume", full_auto=args.full_auto, codex=args.codex, timeout=runtime_timeout_policy.resolve("codex_supervisor_run", args.timeout), request_file=args.request_file)


if __name__ == "__main__":
    raise SystemExit(main())

# STORY_OS_V211_RUNTIME_CLOSURE_R31
