#!/usr/bin/env python3
"""Explicit-only Windows Codex full-access compatibility shim.

This historical transport exists only for an explicitly selected CODEX runtime
on Windows hosts where Codex sandbox creation fails. It is never selected by
WORK/WEB, contains no user-specific executable path, and refuses to elevate
unless STORY_OS_ALLOW_CODEX_FULL_ACCESS=1 is explicitly set.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_real_codex() -> Path:
    if os.environ.get("STORY_OS_RUNTIME", "").strip().upper() != "CODEX":
        raise RuntimeError("codex_win_fullaccess requires explicit STORY_OS_RUNTIME=CODEX")
    if os.environ.get("STORY_OS_ALLOW_CODEX_FULL_ACCESS", "").strip() != "1":
        raise RuntimeError("full-access shim disabled; set STORY_OS_ALLOW_CODEX_FULL_ACCESS=1 explicitly")
    raw = os.environ.get("CODEX_EXE") or shutil.which("codex.exe") or shutil.which("codex") or shutil.which("codex.cmd")
    if not raw:
        raise RuntimeError("Codex CLI not found; set CODEX_EXE")
    path = Path(raw).expanduser().resolve()
    if path == Path(__file__).resolve():
        raise RuntimeError("CODEX_EXE resolves to the compatibility shim itself")
    if not path.is_file():
        raise RuntimeError(f"Codex CLI not found: {path}")
    return path


def main() -> int:
    try:
        real = resolve_real_codex()
    except RuntimeError as exc:
        print(f"CODEX_FULL_ACCESS_DISABLED: {exc}", file=sys.stderr)
        return 2
    argv = sys.argv[1:]
    rewritten: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in {"-s", "--sandbox"} and index + 1 < len(argv):
            index += 2
            continue
        rewritten.append(arg)
        index += 1
    rewritten += ["-s", "danger-full-access"]
    return subprocess.run([str(real), *rewritten], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
