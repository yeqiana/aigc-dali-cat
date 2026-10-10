#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only Codex CLI minimum-version admission for native StoryOS production.

This proves only locally known *client* minimums, not ChatGPT account model
entitlement, image tool visibility, or a successful provider call. Image payload
model names are not Codex CLI -m selections and are intentionally excluded.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

# Version floors from OpenAI Codex models.json (checked 2026-10-10).
# Unknown CLI model identifiers must be assessed before production; never
# assume they have no minimum client requirement.
CLIENT_FLOORS = {
    "gpt-6-luna": (0, 155, 0),
    "gpt-6-sol": (0, 155, 0),
    "gpt-6-astra": (0, 153, 0),
}
VERSION = re.compile(r"^(?:codex|codex-cli) (\d+)\.(\d+)\.(\d+)(?:[-+][\w.-]+)?$")


def assess(version: str, profiles: dict) -> dict:
    """Pure assessment; no model, MySQL, filesystem or network operations."""
    match = VERSION.fullmatch(str(version or "").strip())
    client = tuple(int(part) for part in match.groups()) if match else None
    required: set[str] = set()
    invalid = False
    for name, profile in profiles.items():
        if name == "image_payload":
            continue
        model = profile.get("model") if isinstance(profile, dict) else None
        if not isinstance(model, str) or not model.strip():
            invalid = True
        else:
            required.add(model.strip())
    unknown = sorted(model for model in required if model not in CLIENT_FLOORS)
    outdated = sorted(model for model in required
                      if model in CLIENT_FLOORS and (client is None or client < CLIENT_FLOORS[model]))
    minimum = max((CLIENT_FLOORS[model] for model in required if model in CLIENT_FLOORS),
                  default=None)
    compatible = bool(client is not None and required and not invalid and not unknown and not outdated)
    return {
        "status": "CLIENT_VERSION_COMPATIBLE" if compatible else "CLIENT_VERSION_BLOCKED",
        "cli_version": str(version).strip() if client is not None else "UNVERIFIED",
        "minimum_cli_version": (".".join(map(str, minimum)) if minimum else None),
        "outdated_models": outdated,
        "unassessed_models": unknown,
        "invalid_policy_profiles": invalid or not required,
        "model_entitlement_verified": False,
        "image_tool_verified": False,
        "model_calls": 0,
        "sql_writes": 0,
    }


def inspect(episode: Path | None = None) -> dict:
    # Keep model authority in MySQL when an Episode binding exists.
    import codex_cli_contract
    import codex_user_runner
    import model_policy
    import model_policy_persistence

    config_policy = model_policy.freeze_for_episode()
    policy = config_policy
    source = "CONFIG_UNBOUND"
    if episode is not None:
        episode = episode.resolve()
        if not episode.is_dir() or not episode.is_relative_to((ROOT / "episodes").resolve()):
            raise ValueError("EPISODE_PATH_INVALID")
        bound = model_policy_persistence.load(episode)
        if bound is not None:
            policy = bound
            source = "MYSQL_EPISODE_MODEL_POLICY"
    # The interactive-user Runner may remain alive across an in-place Codex
    # CLI upgrade. The health endpoint reports its STARTUP version, which can
    # be stale even when the actual executable already satisfies the model
    # policy. Probe the exact runner-owned executable live, without a model
    # call, rather than blocking production on a stale startup snapshot.
    if codex_user_runner.bridge_required():
        health = codex_user_runner.runner_health()
        if health.get("status") != "ok" or health.get("codex_available") is not True:
            raise RuntimeError("USER_RUNNER_CODEX_VERSION_UNVERIFIED")
        check = codex_user_runner.run_codex(
            ["codex", "--version"], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", timeout=30, cwd=ROOT, task_type="smoke",
        )
        version = str(check.stdout or "").strip()
        if check.returncode != 0 or not VERSION.fullmatch(version):
            raise RuntimeError("USER_RUNNER_LIVE_CODEX_VERSION_UNVERIFIED")
        resolution = "INTERACTIVE_USER_RUNNER_LIVE"
    else:
        cli = codex_cli_contract.resolve()
        version = cli.version
        resolution = cli.resolution
    result = assess(version, policy["profiles"])
    result["policy_source"] = source
    result["policy_sha256"] = policy.get("policy_sha256")
    result["cli_resolution"] = resolution
    # Never expose local installation paths, usernames or credentials.
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=Path)
    args = parser.parse_args()
    try:
        output = inspect(ROOT / args.episode if args.episode and not args.episode.is_absolute()
                         else args.episode)
    except Exception:
        output = {
            "status": "CLIENT_VERSION_BLOCKED",
            "reason": "CLI_OR_POLICY_AUTHORITY_UNVERIFIED",
            "model_entitlement_verified": False,
            "image_tool_verified": False,
            "model_calls": 0,
            "sql_writes": 0,
        }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if output["status"] == "CLIENT_VERSION_COMPATIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
