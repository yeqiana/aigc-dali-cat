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

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
CONTRACT = ROOT / "runtimes" / "workflow-contract.json"


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
    if runtime != "CODEX":
        raise SystemExit(f"local workflow_runner only executes CODEX adapter; detected {runtime}. WORK/WEB are product runtime adapters.")
    run([sys.executable, SYSTEM / "runtime_checkpoint.py", "init", ep, "--runtime", runtime, "--full-auto"])
    run_id = perf.start_run(ep, runtime, "resume" if resume else "run")
    try:
        execution_mode = str(((request_data or {}).get("runtime") or {}).get("execution_mode") or "compat")
        if execution_mode == "dag":
            rc = runtime_dag.execute(ep, codex=codex, timeout=timeout, run_id=run_id)
            total = time.monotonic() - started
            perf.finish_run(ep, run_id, "COMPLETE" if rc == 0 else "BLOCKED", total)
            try:
                obs.collect(ep, write=True)
            except Exception:
                pass
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
        try:
            obs.collect(ep, write=True)
        except Exception:
            pass
        return child.returncode
    except BaseException:
        total = time.monotonic() - started
        try:
            perf.finish_run(ep, run_id, "BLOCKED", total)
        except Exception:
            pass
        try:
            obs.collect(ep, write=True)
        except Exception:
            pass
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("episode_dir")
    for name in ("run", "resume"):
        p = sub.add_parser(name); p.add_argument("episode_dir"); p.add_argument("--full-auto", action="store_true"); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=7200); p.add_argument("--request-file")
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
    return execute(ep, resume=args.cmd == "resume", full_auto=args.full_auto, codex=args.codex, timeout=args.timeout, request_file=args.request_file)


if __name__ == "__main__":
    raise SystemExit(main())
