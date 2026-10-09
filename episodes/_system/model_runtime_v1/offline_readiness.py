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
