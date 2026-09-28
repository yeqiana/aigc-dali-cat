#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS shared scoped Codex critic runner (B0).

Single implementation source for the critic process launch shared by
fast_frame_scout / visual_review_legacy / visual_lock_v21 /
frame_semantic_review / incremental_frame_review.  The Visual Lock V2.1
semantics are the reference model:

- prompt goes to stdin in a fresh isolated exec session;
- JSON output is persisted with -o when the consumer asks for a candidate
  file, otherwise it is read back from stdout;
- every launch writes a deterministic per-attempt log file;
- rc=0 plus valid JSON is content territory; anything else is a technical
  failure the consumer classifies with its own taxonomy.

This module never records ledger/health state: consumers keep their
attempt/technical-failure bookkeeping and their own prompts.
"""
from __future__ import annotations

import argparse
import codex_user_runner
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SUCCESS_RC = 0
DEFAULT_LOG_NAME = "codex-critic-run.jsonl"


@dataclass
class LaunchResult:
    returncode: int
    log_path: Path
    log_text: str
    output: bytes = b""
    remote: dict | None = None
    execution_target: dict | None = None
    actual_dispatch_target: dict | None = None


class ExecutionTargetRejected(RuntimeError):
    """The selected route cannot safely be consumed by this executor."""


def effective_execution_target(*, task_type, legacy_target, route_decision=None,
                               production_enabled=None, scheduler_authorized=False):
    """Return the target this local Codex executor is allowed to run.

    Shadow proposals never change dispatch. In production mode only the three
    allowlisted Critic tasks can consume a router decision; NO_ROUTE and
    targets belonging to another runtime fail closed before subprocess launch.
    """
    target = dict(legacy_target or {})
    if not target:
        raise ExecutionTargetRejected("legacy execution target is required")
    if production_enabled is None:
        import capability_router
        production_enabled = capability_router.effective_router_config()["production_enabled"]
    if not production_enabled:
        return target
    allowed = {"story_semantic_critic", "preimage_semantic_critic", "final_semantic_critic"}
    if task_type not in allowed:
        return target
    if scheduler_authorized is not True:
        raise ExecutionTargetRejected("production target requires Runtime Scheduler authorization")
    if not isinstance(route_decision, dict):
        raise ExecutionTargetRejected("production route decision is missing")
    if route_decision.get("effective_action") == "NO_ROUTE":
        raise ExecutionTargetRejected("P4_NO_ROUTE: executor dispatch refused")
    if route_decision.get("effective_action") in {"KEEP_LEGACY", "BYPASS_ROUTER_PRODUCTION"}:
        return target
    if route_decision.get("effective_action") != "FALLBACK":
        raise ExecutionTargetRejected("unsupported production route action")
    selected = route_decision.get("effective_route")
    if not isinstance(selected, dict):
        raise ExecutionTargetRejected("fallback route target is missing")
    if selected.get("provider") != "codex_user_runner" or selected.get("runtime") != "CODEX":
        raise ExecutionTargetRejected("selected route is not consumable by the Codex Critic executor")
    if not isinstance(selected.get("model"), str) or not selected["model"].strip():
        raise ExecutionTargetRejected("selected Codex route has no model")
    return {"provider": selected["provider"], "model": selected["model"],
            "runtime": selected["runtime"]}


def resolve_codex(raw):
    import codex_cli_contract
    return codex_cli_contract.resolve_path(raw)


def prefix(codex):
    import codex_cli_contract
    return codex_cli_contract.command_prefix(codex)


def default_sandbox():
    return "danger-full-access" if os.name == "nt" else "workspace-write"


def resolve_sandbox(requested=None):
    """Resolve the nested-Codex sandbox flag for this platform.

    Windows cannot start the nested CLI under workspace-write
    (CreateProcessWithLogonW fails with 1385), so a workspace-write request
    degrades to the platform default there.  Other platforms keep the
    requested value, and non-workspace-write requests are never rewritten.
    """
    if os.name == "nt" and requested in (None, "workspace-write"):
        return default_sandbox()
    return requested or default_sandbox()


def default_log_path(root, tag="critic"):
    directory = Path(root).resolve() / "meta"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{tag}-run.jsonl"


def build_command(
    *,
    codex,
    root,
    sandbox=None,
    attachments=None,
    model=None,
    reasoning_effort=None,
    reasoning_effort_literal=None,
    output_path=None,
    output_schema=None,
    extra=None,
):
    """Assemble one isolated Codex exec invocation.

    Flags follow visual_lock_v21 ordering.  reasoning_effort_literal passes an
    exact -c value (legacy fast scout uses model_reasoning_effort="low");
    otherwise -c model_reasoning_effort="<effort>" is generated.
    """
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        *(extra or []),
    ]
    if model:
        cmd += ["-m", model]
    if reasoning_effort_literal is not None:
        cmd += ["-c", reasoning_effort_literal]
    elif reasoning_effort:
        cmd += ["-c", f'model_reasoning_effort="{reasoning_effort}"']
    cmd += ["-s", resolve_sandbox(sandbox), "-C", str(root), "--json"]
    if output_schema is not None:
        cmd += ["--output-schema", str(output_schema)]
    if output_path is not None:
        cmd += ["-o", str(output_path)]
    for attachment in attachments or []:
        cmd += ["-i", str(attachment)]
    cmd += ["-"]
    return cmd


def launch(
    prompt,
    *,
    codex,
    root,
    timeout,
    output_path=None,
    output_schema=None,
    attachments=None,
    model=None,
    reasoning_effort=None,
    reasoning_effort_literal=None,
    sandbox=None,
    log_path=None,
    extra=None,
    execution_target=None,
):
    """Run one critic; returns rc plus the full attempt log text.

    subprocess.TimeoutExpired / OSError propagate to the consumer so each lane
    keeps its own technical-failure bookkeeping semantics.
    """
    resolved_log = log_path or default_log_path(root)
    resolved_log.parent.mkdir(parents=True, exist_ok=True)
    if execution_target is not None:
        if (not isinstance(execution_target, dict)
                or execution_target.get("provider") != "codex_user_runner"
                or execution_target.get("runtime") != "CODEX"
                or not isinstance(execution_target.get("model"), str)
                or not execution_target["model"].strip()):
            raise ExecutionTargetRejected("invalid execution target for Codex Critic runner")
        model = execution_target["model"]
    cmd = build_command(
        codex=codex,
        root=root,
        sandbox=sandbox,
        attachments=attachments,
        model=model,
        reasoning_effort=reasoning_effort,
        reasoning_effort_literal=reasoning_effort_literal,
        output_path=output_path,
        output_schema=output_schema,
        extra=extra,
    )
    with resolved_log.open("w", encoding="utf-8", newline="\n") as handle:
        # STORY_OS_V2_7_CODEX_USER_MODE_BRIDGE: one execution contract for every
        # critic lane. Direct when Story OS already runs as the interactive user,
        # otherwise the same declarative task is forwarded to the user-mode runner.
        done = codex_user_runner.run_codex(
            cmd,
            input=prompt.encode("utf-8"),
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            task_type="critic",
        )
    log_text = resolved_log.read_text(encoding="utf-8-sig", errors="replace")
    remote = dict(getattr(done, "remote", {}) or {})
    return LaunchResult(returncode=done.returncode, log_path=resolved_log,
                        log_text=log_text, output=log_text.encode("utf-8"),
                        remote=remote or None,
                        execution_target=dict(execution_target) if execution_target else None,
                        actual_dispatch_target=dict(execution_target) if execution_target else None)


def parse_json_text(text):
    """Parse a critic JSON answer (stdout mode)."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("critic JSON root must be an object")
    return data


def parse_json_file(path):
    """Parse a critic JSON answer persisted with -o."""
    import story_json

    return story_json.read_json(path)


def recover_completed_agent_json(log_text: str) -> dict | None:
    """Recover a completed critic answer when Codex crashes after the answer.

    Fail closed: accept only a JSONL ``item.completed`` agent_message whose
    inner text is a JSON object and which is followed by ``turn.completed``.
    This deliberately rejects partial streaming output and pre-completion
    messages. The caller must still validate source hashes and the review schema.
    """
    last_agent: tuple[int, dict] | None = None
    completed_indexes: list[int] = []
    for index, raw in enumerate(str(log_text or "").splitlines()):
        try:
            event = json.loads(raw)
        except Exception:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "turn.completed":
            completed_indexes.append(index)
            continue
        item = event.get("item") if event.get("type") == "item.completed" else None
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        try:
            payload = parse_json_text(text)
        except Exception:
            continue
        last_agent = (index, payload)
    if not last_agent:
        return None
    index, payload = last_agent
    if not any(done_index > index for done_index in completed_indexes):
        return None
    return payload


def self_test():
    import tempfile

    assert prefix(Path("codex.py")) == [sys.executable, "codex.py"]
    with tempfile.TemporaryDirectory(prefix="critic runner self test ") as td:
        root = Path(td)
        cmd = build_command(codex=Path("codex.exe"), root=root,
                            model="m", reasoning_effort="low",
                            attachments=[Path("a.png")],
                            output_path=Path("out.json"))
        assert "--skip-git-repo-check" in cmd and "--json" in cmd
        assert cmd[-1] == "-" and "-i" in cmd
        payload = {"summary": {"passed": True}}
        out = root / "out.json"
        out.write_text(json.dumps(payload), encoding="utf-8")
        assert parse_json_file(out) == payload
        assert parse_json_text(json.dumps(payload)) == payload
        recovered_log = "\n".join([
            json.dumps({"type":"item.completed","item":{"type":"agent_message","text":json.dumps(payload)}}),
            json.dumps({"type":"turn.completed","usage":{}}),
            "memory allocation failed",
        ])
        assert recover_completed_agent_json(recovered_log) == payload
        partial_log = json.dumps({"type":"item.completed","item":{"type":"agent_message","text":json.dumps(payload)}})
        assert recover_completed_agent_json(partial_log) is None
        try:
            parse_json_text("[1]")
            raise AssertionError("non-object JSON must be rejected")
        except ValueError:
            pass
    print("CODEX CRITIC RUNNER SELF-TEST PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="self-test")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
