"""Offline, non-billable runtime readiness checks.

A CLI binary or API credential can make a *route* ready but never proves model
or tool capability. No network probe or model call is ever performed here.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

def inspect_native(*, codex_binary: str = "codex", which=None) -> dict:
    find = which if which is not None else shutil.which
    candidate = find(codex_binary)
    if not isinstance(candidate, str) or not candidate.strip():
        return {"status": "BLOCKED", "reason": "CODEX_CLI_NOT_FOUND",
                "capability_status": "UNKNOWN", "may_dispatch": False}
    return {"status": "ROUTE_PRESENT", "reason": "CODEX_CLI_PRESENT_NOT_ATTESTED",
            "capability_status": "UNKNOWN", "may_dispatch": False}

def inspect_api(*, key_env: str = "OPENAI_API_KEY", environ=None) -> dict:
    if key_env != "OPENAI_API_KEY":
        return {"status": "BLOCKED", "reason": "UNAPPROVED_API_CREDENTIAL_ENV",
                "capability_status": "UNKNOWN", "may_dispatch": False}
    env = os.environ if environ is None else environ
    value = env.get(key_env)
    if not isinstance(value, str) or not value.strip():
        return {"status": "BLOCKED", "reason": "OPENAI_API_KEY_MISSING",
                "capability_status": "UNKNOWN", "may_dispatch": False}
    # Never return the credential, its length, suffix, hashes or prefix.
    return {"status": "ROUTE_PRESENT", "reason": "API_KEY_PRESENT_NOT_ATTESTED",
            "capability_status": "UNKNOWN", "may_dispatch": False}


def inspect_native_login(*, codex_binary: str = "codex", command_runner=None,
                         timeout: int = 8) -> dict:
    """Read-only local Codex CLI login state. Never invokes a model or returns output.

    A logged-in CLI remains NOT ATTESTED for the requested model or image tools.
    """
    import subprocess
    run = command_runner if command_runner is not None else subprocess.run
    if not isinstance(timeout, int) or not 1 <= timeout <= 30:
        raise ValueError("CODEX_LOGIN_PROBE_TIMEOUT_INVALID")
    if codex_binary != "codex":
        return {"status": "BLOCKED", "reason": "CODEX_CLI_UNAPPROVED_COMMAND",
                "capability_status": "UNKNOWN", "may_dispatch": False}
    try:
        completed = run([codex_binary, "login", "status"], capture_output=True,
                        timeout=timeout, check=False, text=True)
        stdout = str(getattr(completed, "stdout", "") or "")
        stderr = str(getattr(completed, "stderr", "") or "")
        combined = (stdout + "\n" + stderr).lower()
        if getattr(completed, "returncode", None) == 0 and "logged in" in combined and "not logged in" not in combined:
            return {"status": "LOGIN_PRESENT", "reason": "CODEX_SESSION_PRESENT_NOT_ATTESTED",
                    "capability_status": "UNKNOWN", "may_dispatch": False}
        if "not logged in" in combined:
            return {"status": "BLOCKED", "reason": "CODEX_SESSION_NOT_LOGGED_IN",
                    "capability_status": "UNKNOWN", "may_dispatch": False}
    except Exception:
        pass
    return {"status": "BLOCKED", "reason": "CODEX_LOGIN_STATUS_UNVERIFIED",
            "capability_status": "UNKNOWN", "may_dispatch": False}
