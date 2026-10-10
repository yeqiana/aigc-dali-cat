#!/usr/bin/env python3
"""Read-only native Codex CLI flag probe. Never runs `codex exec` against a model.

This checks syntax support, not user login, model access, attachments or
filesystem isolation. On Windows the current StoryOS runner can use full access.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

VERSION_RE = re.compile(r"^(?:codex|codex-cli) \d+\.\d+\.\d+(?:[-+][\w.-]+)?$")
REQUIRED_FLAGS = ("--ephemeral", "--skip-git-repo-check", "--json", "--sandbox")


def inspect_cli(executable: str, *, platform_name: str | None = None) -> dict:
    name = platform_name or os.name
    values = []
    for argv in ((executable, "--version"), (executable, "exec", "--help")):
        result = subprocess.run(list(argv), capture_output=True, text=True,
                                check=False, timeout=15)
        if result.returncode != 0:
            return {"status": "CLI_PROBE_FAILED", "runtime_model_calls": 0,
                    "command_only": True, "native_credential_check": False,
                    "filesystem_isolation_verified": False}
        values.append(result.stdout)
    version = values[0].strip()
    help_text = values[1]
    flags = {f: f in help_text for f in REQUIRED_FLAGS}
    flags["-C"] = bool(re.search(r"\-C,\s*\-\-cd\b", help_text))
    return {
        "status": "CLI_FLAGS_SUPPORTED" if VERSION_RE.fullmatch(version)
                  and all(flags.values()) else "CLI_FLAGS_INCOMPLETE",
        "version": version if VERSION_RE.fullmatch(version) else "INVALID_VERSION",
        "flags": flags,
        "command_only": True,
        "runtime_model_calls": 0,
        "native_credential_check": False,
        "filesystem_isolation_verified": False,
        "episode_cwd_is_security_boundary": False,
        "windows_critic_default_sandbox_full_access": name == "nt",
        "note": "No model is started; -C only sets working directory. Windows default full-access Critic execution is not a filesystem sandbox.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", help="Native Codex path; defaults to system PATH")
    args = parser.parse_args()
    path = args.codex or shutil.which("codex") or shutil.which("codex.cmd")
    if not path:
        print(json.dumps({"status": "CODEX_NOT_FOUND", "runtime_model_calls": 0}))
        return 2
    try:
        report = inspect_cli(path)
    except (OSError, subprocess.TimeoutExpired):
        report = {"status": "CLI_PROBE_FAILED", "runtime_model_calls": 0}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "CLI_FLAGS_SUPPORTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
