#!/usr/bin/env python3
"""Bounded WORK/DevSpace host-action consumer.

This module deliberately owns a narrow allowlist.  It executes a real DevSpace
vision review, writes only the frozen candidate requested by the product-review
contract, then reuses the canonical finalizer.  It never advances episode state.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

import product_review_adapter
import runtime_timeout_policy
import story_json
import storyos_config
import visual_lock_baseline_gate

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_ACTIONS = {"REVIEW_ORDINARY_BASELINE"}


class WorkHostActionError(RuntimeError):
    pass


def local_work_action(action: dict) -> str | None:
    if not isinstance(action, dict):
        return None
    if str(action.get("executor") or "").upper() != "WORK":
        return None
    name = str(action.get("action") or "")
    return name if name in ALLOWED_ACTIONS else None


def _provider() -> str:
    cfg = storyos_config.load_config()
    if str(storyos_config.get_path(cfg, "runtime.review.runtime") or "").upper() != "WORK":
        raise WorkHostActionError("WORK host action requires runtime.review.runtime=WORK")
    if str(storyos_config.get_path(cfg, "runtime.review.workspace_transport") or "").upper() != "DEVSPACE":
        raise WorkHostActionError("WORK host action requires runtime.review.workspace_transport=DEVSPACE")
    if storyos_config.get_path(cfg, "runtime.review.allow_webcodex") is not False:
        raise WorkHostActionError("WebCodex must remain disabled")
    if storyos_config.get_path(cfg, "runtime.review.allow_local_codex_review") is not False:
        raise WorkHostActionError("local Codex review must remain disabled")
    provider = str(storyos_config.get_path(cfg, "runtime.review.bounded_devspace_provider") or "").lower()
    if not provider:
        raise WorkHostActionError("bounded WORK review requires an explicitly configured DevSpace provider")
    if provider in {"codex", "webcodex"}:
        raise WorkHostActionError("bounded WORK review provider must not be Codex/WebCodex")
    return provider


def _log_path(ep: Path, request_id: str) -> Path:
    safe = "".join(ch for ch in request_id if ch.isalnum() or ch in {"-", "_"})
    return ep / "meta/runtime/work-host-actions" / f"{safe}.jsonl"


def _run_devspace_review(ep: Path, request: dict) -> Path:
    candidate = (ROOT / str(request.get("candidate_path") or "")).resolve()
    try:
        candidate.relative_to(ep.resolve())
    except ValueError as exc:
        raise WorkHostActionError("bounded review candidate must stay inside episode") from exc
    candidate.unlink(missing_ok=True)
    provider = _provider()
    prompt = (
        "Execute this frozen Story OS WORK_DEVSPACE_BOUNDED actual-pixel review. "
        "Use DevSpace workspace access to inspect the image file itself. Do not use WebCodex or local Codex. "
        "Do not modify any source, authority, queue, ledger, or image. "
        "If actual pixels cannot be inspected or a required check fails, write a FAIL candidate.\n\n"
        + str(request.get("prompt") or "")
    )
    log = _log_path(ep, str(request.get("request_id") or "bounded-review"))
    log.parent.mkdir(parents=True, exist_ok=True)
    executable = shutil.which("devspace.cmd") or shutil.which("devspace")
    if not executable:
        raise WorkHostActionError("DevSpace CLI is unavailable")
    try:
        done = subprocess.run(
            [executable, "agents", "run", provider, "--json", prompt],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=runtime_timeout_policy.seconds("review_critic"),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkHostActionError(f"DevSpace bounded review transport unavailable: {exc}") from exc
    transcript = [done.stdout or ""]
    if done.returncode != 0:
        log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
        raise WorkHostActionError(f"DevSpace bounded review failed rc={done.returncode}; log={log.relative_to(ROOT).as_posix()}")
    try:
        launched = json.loads(done.stdout or "{}")
        agent_id = str(launched.get("id") or "")
    except json.JSONDecodeError as exc:
        log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
        raise WorkHostActionError("DevSpace bounded review did not return an agent id") from exc
    if not agent_id:
        log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
        raise WorkHostActionError("DevSpace bounded review agent id missing")
    deadline = time.monotonic() + runtime_timeout_policy.seconds("review_critic")
    while True:
        try:
            # Two-level bound: one status RPC gets the probe bound, the wait loop as a
            # whole gets the review-critic bound (deadline above). Neither is a literal.
            status_call = subprocess.run(
                [executable, "agents", "show", agent_id, "--json"],
                cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                timeout=runtime_timeout_policy.seconds("review_status_probe"),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
            raise WorkHostActionError(f"DevSpace bounded review status unavailable: {exc}") from exc
        transcript.append(status_call.stdout or "")
        if status_call.returncode != 0:
            log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
            raise WorkHostActionError(f"DevSpace bounded review status failed rc={status_call.returncode}")
        try:
            status = json.loads(status_call.stdout or "{}")
        except json.JSONDecodeError as exc:
            log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
            raise WorkHostActionError("DevSpace bounded review status is invalid JSON") from exc
        state = str(status.get("status") or "").lower()
        if state in {"completed", "complete", "succeeded", "success"}:
            break
        if state in {"failed", "cancelled", "canceled"}:
            log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
            message = ((status.get("error") or {}).get("message") or state)
            raise WorkHostActionError(f"DevSpace bounded review agent {state}: {message}")
        if time.monotonic() >= deadline:
            log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
            raise WorkHostActionError("DevSpace bounded review timed out waiting for agent completion")
        time.sleep(1)
    log.write_text("\n".join(transcript), encoding="utf-8", newline="\n")
    if not candidate.is_file():
        raise WorkHostActionError(f"DevSpace bounded review returned without candidate: {candidate.relative_to(ROOT).as_posix()}")
    return log


def execute(ep: Path, action: dict) -> dict:
    ep = Path(ep).resolve()
    name = local_work_action(action)
    if name is None:
        raise WorkHostActionError(f"not an auto-allowed WORK action: {action.get('action') if isinstance(action, dict) else action}")
    if name != "REVIEW_ORDINARY_BASELINE":
        raise WorkHostActionError(f"unsupported WORK action: {name}")
    request_path = product_review_adapter.request_path(ep, "visual-lock-baseline")
    existing = story_json.read_json(request_path, default={}) if request_path.is_file() else {}
    if existing.get("status") == "AWAITING_PRODUCT_REVIEW" and existing.get("review_kind") == "visual-lock-baseline":
        # The frozen request is immutable.  Reusing it prevents a Resume from
        # creating a competing attempt merely because derived runtime evidence
        # changed after the request was prepared.
        request = existing
    else:
        request = visual_lock_baseline_gate.run_product_critic(ep, attempt=1)
    log = _run_devspace_review(ep, request)
    result = visual_lock_baseline_gate.finalize_product_critic(
        ep, attempt=1, runtime="WORK", bounded_devspace=True,
    )
    evidence = {
        "action": name,
        "request_id": request.get("request_id"),
        "runtime": "WORK_DEVSPACE_BOUNDED",
        "workspace_transport": "DEVSPACE",
        "webcodex_used": False,
        "isolated": False,
        "log_path": log.relative_to(ROOT).as_posix(),
        "agent_provider": _provider(),
        "result": result,
    }
    story_json.write_json(ep / "meta/runtime/work-host-action-last.json", evidence)
    return evidence
