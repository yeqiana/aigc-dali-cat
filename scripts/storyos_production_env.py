#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run StoryOS local diagnostic/production scripts with the existing runtime.env.

Uses the Phase9 launcher's single allowlisted env parser. Never prints or writes
credentials, never falls back to an unrelated localhost database when the
machine-local runtime.env is missing. This wrapper does not alter Stage or
Provider authority and delegates the requested command unchanged.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

from phase9_runtime_launcher import RUNTIME_ENV_KEYS, load_runtime_env_file

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ENV = ROOT / ".storyos/runtime-launcher/runtime.env"
ALLOWED_SCRIPT_ROOTS = (ROOT / "episodes/_system", ROOT / "scripts")


def prepare_command(path: str, args: list[str], *, environ: dict[str, str] | None = None,
                    runtime_env: Path = RUNTIME_ENV) -> tuple[list[str], dict[str, str]]:
    script = (ROOT / path).resolve()
    if not script.is_file() or script.suffix.lower() != ".py":
        raise ValueError("STORYOS_RUNTIME_SCRIPT_INVALID")
    if not any(script.is_relative_to(root.resolve()) for root in ALLOWED_SCRIPT_ROOTS):
        raise ValueError("STORYOS_RUNTIME_SCRIPT_OUTSIDE_ALLOWED_ROOTS")
    if not runtime_env.is_file():
        raise ValueError("STORYOS_RUNTIME_ENV_MISSING_FAIL_CLOSED")
    source = dict(os.environ if environ is None else environ)
    if str(source.get("STORY_OS_PRODUCTION_MODE") or "").strip().upper() == "CODEX_MANAGED":
        # The interactive-user Codex Runner is a long-lived process with its
        # own environment. Its inherited STORYOS_* database variables may
        # point to a *different*, older MySQL store than the canonical ignored
        # runtime.env used by the foreground production owner.
        # Native formal production must always load one authoritative DB
        # identity; never let a stale Runner login environment override it.
        for key in RUNTIME_ENV_KEYS:
            source.pop(key, None)
        for key in ("OPENAI_BASE_URL", "OPENAI_API_BASE", "CODEX_BASE_URL",
                    "STORY_OS_OPENCODEX_URL", "OPENAI_API_KEY"):
            source.pop(key, None)
    env, _loaded_keys = load_runtime_env_file(runtime_env, source)
    required = ("STORYOS_MYSQL_HOST", "STORYOS_MYSQL_PORT", "STORYOS_MYSQL_DB")
    if any(not env.get(key) for key in required):
        raise ValueError("STORYOS_RUNTIME_DB_CONFIG_INCOMPLETE")
    return [sys.executable, str(script), *args], env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", help="Project-relative Python entrypoint under episodes/_system or scripts")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed unchanged to the script")
    options = parser.parse_args(argv)
    try:
        cmd, env = prepare_command(options.script, options.args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return int(subprocess.run(cmd, cwd=ROOT, env=env, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
