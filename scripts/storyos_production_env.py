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

from phase9_runtime_launcher import load_runtime_env_file

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
    env, _loaded_keys = load_runtime_env_file(runtime_env, dict(os.environ if environ is None else environ))
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
