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


def resolve_codex(raw):
    value = raw or shutil.which("codex") or shutil.which("codex.exe") \
        or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found")
    p = Path(value).expanduser().resolve()
    if not p.exists():
        raise RuntimeError(f"Codex CLI not found: {p}")
    return p


def prefix(codex):
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        # The user-mode bridge owns the Windows .cmd driver. Sending an outer
        # ``cmd.exe /c`` wrapper across the bridge makes older runner processes
        # treat /c as a Codex argument. Keep direct-mode compatibility while
        # sending the bridge a normalized Codex argv.
        if codex_user_runner.bridge_required():
            return [str(codex)]
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]


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
    attachments=None,
    model=None,
    reasoning_effort=None,
    reasoning_effort_literal=None,
    sandbox=None,
    log_path=None,
    extra=None,
):
    """Run one critic; returns rc plus the full attempt log text.

    subprocess.TimeoutExpired / OSError propagate to the consumer so each lane
    keeps its own technical-failure bookkeeping semantics.
    """
    resolved_log = log_path or default_log_path(root)
    resolved_log.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_command(
        codex=codex,
        root=root,
        sandbox=sandbox,
        attachments=attachments,
        model=model,
        reasoning_effort=reasoning_effort,
        reasoning_effort_literal=reasoning_effort_literal,
        output_path=output_path,
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
    return LaunchResult(returncode=done.returncode, log_path=resolved_log,
                        log_text=log_text)


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
