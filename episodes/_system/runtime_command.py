#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-shell-safe command transport for Story OS V2.6.0.

Rules:
- argv list only; shell=False always
- UTF-8 stdin/stdout
- no Bash heredoc, no PowerShell here-string, no nested `powershell -Command`
- structured payloads go through files or stdin, never shell interpolation
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FORBIDDEN_INLINE = ("<<EOF", "<<'EOF'", '<<"EOF"', "powershell -Command", "pwsh -Command", "@'", '@"')

def command_prefix(executable: str | Path) -> list[str]:
    p = Path(executable).expanduser()
    suffix = p.suffix.lower()
    if suffix == ".py":
        return [sys.executable, str(p)]
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        # Only the executable path is wrapped; payload arguments remain argv elements.
        return ["cmd.exe", "/d", "/s", "/c", str(p)]
    return [str(p)]

def validate_argv(argv: list[str]) -> None:
    if not isinstance(argv, list) or not argv:
        raise ValueError("argv must be a non-empty list")
    for value in argv:
        if not isinstance(value, str):
            raise ValueError("argv items must be strings")
    joined = " ".join(argv)
    for token in FORBIDDEN_INLINE:
        if token.lower() in joined.lower():
            raise ValueError(f"cross-shell unsafe inline construct forbidden: {token}")

def run_argv(argv: list[str], *, cwd: str | Path | None = None, stdin_text: str | None = None,
             timeout: int | float | None = None, capture: bool = True) -> subprocess.CompletedProcess[str]:
    validate_argv(argv)
    child_env = os.environ.copy()
    # STORY_OS_V2_6_0_R2_WINDOWS_UTF8:
    # Windows Python subprocesses attached to pipes may otherwise choose the active
    # ANSI/OEM code page (for example GBK/cp936) while the parent decodes as UTF-8.
    # Force one canonical transport encoding for every Python-aware child process.
    child_env["PYTHONUTF8"] = "1"
    child_env["PYTHONIOENCODING"] = "utf-8"
    kwargs = dict(
        cwd=str(cwd) if cwd is not None else None,
        check=False,
        shell=False,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=timeout,
        env=child_env,
    )
    if stdin_text is not None:
        kwargs["input"] = stdin_text
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT
    return subprocess.run(argv, **kwargs)

def run_python(script: str | Path, args: list[str] | None = None, *, cwd: str | Path | None = None,
               stdin_text: str | None = None, timeout: int | float | None = None) -> subprocess.CompletedProcess[str]:
    return run_argv([sys.executable, str(Path(script)), *(args or [])], cwd=cwd, stdin_text=stdin_text, timeout=timeout)

def run_request(path: Path) -> subprocess.CompletedProcess[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    argv = data.get("argv")
    if not isinstance(argv, list):
        raise ValueError("request.argv must be a list")
    stdin_text = data.get("stdin_text")
    stdin_file = data.get("stdin_file")
    if stdin_text is not None and stdin_file:
        raise ValueError("use only one of stdin_text/stdin_file")
    if stdin_file:
        stdin_text = Path(stdin_file).read_text(encoding="utf-8")
    return run_argv(
        [str(x) for x in argv],
        cwd=data.get("cwd"),
        stdin_text=stdin_text,
        timeout=data.get("timeout"),
        capture=True,
    )

def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="Story OS 中文 空格 ") as td:
        root = Path(td)
        script = root / "echo args.py"
        script.write_text(
            "import json,sys\n"
            "print(json.dumps({'argv':sys.argv[1:],'stdin':sys.stdin.read()},ensure_ascii=False))\n",
            encoding="utf-8",
            newline="\n",
        )
        # Windows-safe contract:
        # - paths / ordinary argv may contain Chinese, spaces and shell metacharacters;
        # - quote-heavy structured content must travel through UTF-8 stdin/file, not argv.
        args = ["中文 路径", "ordinary value with spaces", "$not-shell", "{plain-token}"]
        structured = '{"字幕":"夏夜","quote":"a\\\"b","apostrophe":"c\'d","path":"D:\\\\story OS\\\\中文","emoji":"✓"}'
        cp = run_python(script, args, cwd=root, stdin_text=structured, timeout=15)
        assert cp.returncode == 0, cp.stdout
        json_lines = [line for line in (cp.stdout or "").splitlines() if line.lstrip().startswith("{")]
        if not json_lines:
            raise AssertionError("child produced no structured JSON line: " + (cp.stdout or "")[-1200:])
        out = json.loads(json_lines[-1])
        if out["argv"] != args:
            raise AssertionError(f"argv round-trip mismatch: expected={args!r} actual={out['argv']!r}")
        assert out["stdin"] == structured
        try:
            validate_argv(["powershell", "-Command", "Write-Host x"])
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe PowerShell inline command was not rejected")
    print("RUNTIME COMMAND V2.6.0 CROSS-SHELL SELF-TEST PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run-request")
    p.add_argument("request_json", type=Path)
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    cp = run_request(args.request_json)
    if cp.stdout:
        print(cp.stdout, end="" if cp.stdout.endswith("\n") else "\n")
    return int(cp.returncode)

if __name__ == "__main__":
    raise SystemExit(main())

# STORY_OS_V2_6_0_R2_WINDOWS_UTF8
