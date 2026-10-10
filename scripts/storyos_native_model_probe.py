#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explicit paid native-Codex model execution probe for an existing StoryOS Episode.

This diagnostic is deliberately separate from the free, read-only production
plan. It cannot authorize a Stage transition, Review PASS or an Image Attempt.
Only a matching completed native model response counts as a positive result.
"""
from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

# A fixed, small allowlist avoids accidentally probing image payload or
# arbitrary task roles. Both must use the Episode's model policy.
ROLES = ("story.authoring", "critic.story")
PROBE_TASK_TYPE = "smoke"  # Existing codex_user_runner ALLOWED_TASK_TYPES
MAX_OUTPUT_BYTES = 1_048_576


def confirmed_native_reply(output: str, expected: str) -> bool:
    """Require the exact marker from a completed CLI turn, not a log echo."""
    if not isinstance(output, str) or len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        return False
    complete = False
    message = False
    failed = False
    for raw in output.splitlines():
        try:
            event = json.loads(raw)
        except (ValueError, TypeError):
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "turn.completed":
            complete = True
        elif event.get("type") == "turn.failed":
            failed = True
        elif event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                message |= str(item.get("text") or "").strip() == expected
    return complete and message and not failed


def command(model: str, effort: str, *, launcher: list[str]) -> list[str]:
    return [*launcher, "exec", "--skip-git-repo-check", "--ephemeral",
            "-m", model, "-c", f'model_reasoning_effort="{effort}"',
            "-s", "read-only", "-C", str(ROOT), "--json", "-"]


def evaluate_result(*, completed, expected: str, model: str, role: str,
                    policy_sha: str, policy_source: str, cli_version: str) -> dict:
    remote = getattr(completed, "remote", None)
    remote = remote if isinstance(remote, dict) else {}
    native = remote.get("transport_route") == "native_codex"
    matched = confirmed_native_reply(completed.stdout or "", expected)
    valid = (completed.returncode == 0 and native and matched)
    return {
        "status": "NATIVE_MODEL_EXECUTION_PROVEN" if valid else "NATIVE_MODEL_EXECUTION_NOT_PROVEN",
        "reason": ("NATIVE_MODEL_RESPONSE_MATCHED" if valid else
                   "NATIVE_ROUTE_UNVERIFIED" if not native else
                   "CODEX_EXEC_NONZERO" if completed.returncode != 0 else
                   "EXPECTED_COMPLETED_RESPONSE_MISSING"),
        "role": role,
        "requested_model": model,
        "cli_version": cli_version,
        "model_policy_source": policy_source,
        "model_policy_sha256": policy_sha,
        "native_route_verified": native,
        "model_execution_verified": valid,
        "image_tool_verified": False,
        "review_authority_granted": False,
        "production_authorization": False,
        "model_calls": 1,
        "sql_writes": 0,
    }


def probe(episode: Path, role: str, *, env: dict[str, str]) -> dict:
    """Execute a single explicitly authorized paid probe via the production Runner."""
    import codex_cli_contract
    import codex_user_runner
    import model_policy
    import model_policy_persistence
    import storyos_native_model_readiness

    readiness = storyos_native_model_readiness.inspect(episode)
    if readiness["status"] != "CLIENT_VERSION_COMPATIBLE":
        return {"status": "NATIVE_MODEL_PROBE_BLOCKED",
                "reason": "MODEL_CLIENT_VERSION_OR_POLICY_UNVERIFIED",
                "model_calls": 0, "sql_writes": 0,
                "production_authorization": False}
    bound = model_policy_persistence.load(episode)
    selected = model_policy.resolve(role, episode=episode if bound is not None else None)
    policy_source = "MYSQL_EPISODE_MODEL_POLICY" if bound is not None else "CONFIG_UNBOUND"
    if (readiness.get("policy_sha256") != selected.get("model_policy_sha256")
            or readiness.get("policy_source") != policy_source):
        return {"status": "NATIVE_MODEL_PROBE_BLOCKED",
                "reason": "MODEL_POLICY_CHANGED_BETWEEN_CHECKS",
                "model_calls": 0, "sql_writes": 0,
                "production_authorization": False}
    model = str(selected["model"]).strip()
    effort = str(selected["reasoning_effort"]).strip()
    # In bridged mode the interactive user's Runner resolves its own Codex
    # executable. Do not force the service account's different PATH on it.
    launcher = (["codex"] if codex_user_runner.bridge_required()
                else codex_cli_contract.command_prefix(codex_cli_contract.resolve_path()))
    marker = "STORYOS_NATIVE_OK_" + secrets.token_hex(12)
    text = ("仅输出以下唯一字符串，不调用工具，不读取文件，也不要解释：\n" + marker)
    cmd = command(model, effort, launcher=launcher)
    completed = codex_user_runner.run_model_codex(
        cmd, input=text, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", check=False,
        timeout=90, cwd=ROOT, task_type=PROBE_TASK_TYPE, env=env,
    )
    return evaluate_result(
        completed=completed, expected=marker, model=model, role=role,
        policy_sha=selected["model_policy_sha256"],
        policy_source=policy_source, cli_version=readiness["cli_version"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--role", choices=ROLES, default="critic.story")
    parser.add_argument("--ack-real-model-call", action="store_true")
    args = parser.parse_args(argv)
    if not args.ack_real_model_call:
        print(json.dumps({"status": "NATIVE_MODEL_PROBE_BLOCKED",
                          "reason": "REAL_MODEL_CALL_ACK_REQUIRED", "model_calls": 0,
                          "sql_writes": 0, "production_authorization": False}))
        return 2
    try:
        import storyos_codex_managed
        episode = storyos_codex_managed.canonical_episode(args.episode)
        env = storyos_codex_managed.native_environment()
        result = probe(episode, args.role, env=env)
    except (Exception, subprocess.TimeoutExpired):
        # No credentials, prompts, local paths, CLI transcripts or stack traces.
        result = {"status": "NATIVE_MODEL_EXECUTION_NOT_PROVEN",
                  "reason": "NATIVE_PROBE_TRANSPORT_OR_AUTHORITY_FAILURE",
                  "model_calls": "UNKNOWN_AFTER_DISPATCH",
                  "sql_writes": 0, "production_authorization": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "NATIVE_MODEL_EXECUTION_PROVEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
