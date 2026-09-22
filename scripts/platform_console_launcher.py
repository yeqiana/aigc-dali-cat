"""Run Platform API and the built Web Console as one local service unit."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phase9_runtime_launcher import load_runtime_env_file

WEB = ROOT / "web-console"
API = ROOT / "scripts" / "platform_api_server.py"
VITE = WEB / "node_modules" / "vite" / "bin" / "vite.js"


@dataclass(frozen=True)
class ChildSpec:
    name: str
    command: tuple[str, ...]
    log_path: Path
    cwd: Path


def build_children(*, python_exe: str, node_exe: str, run_root: Path, web_port: int = 3100) -> list[ChildSpec]:
    return [
        ChildSpec("platform-api", (python_exe, str(API), "--host", "127.0.0.1", "--port", "8080"), run_root / "platform-api.log", ROOT),
        ChildSpec("web-console", (node_exe, str(VITE), "preview", "--host", "127.0.0.1", "--port", str(web_port), "--strictPort"), run_root / "web-console.log", WEB),
    ]


def _healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return 200 <= response.status < 300
    except OSError:
        return False


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="StoryOS Platform Console launcher")
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--node-exe", required=True)
    parser.add_argument("--run-root", default=str(ROOT / ".storyos" / "platform-console"))
    parser.add_argument("--runtime-env-file")
    parser.add_argument("--web-port", type=int, default=3100)
    parser.add_argument("--startup-timeout", type=float, default=45)
    parser.add_argument("--max-seconds", type=float)
    args = parser.parse_args(argv)
    run_root = Path(args.run_root)
    evidence = run_root / "launcher-evidence.json"
    required = [Path(args.python_exe), Path(args.node_exe), API, VITE, WEB / "dist" / "index.html"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        _write(evidence, {"status": "FAILED", "missing": missing})
        return 2

    env_file = Path(args.runtime_env_file) if args.runtime_env_file else run_root / "runtime.env"
    env, loaded = load_runtime_env_file(env_file, dict(os.environ))
    children = build_children(python_exe=args.python_exe, node_exe=args.node_exe, run_root=run_root, web_port=args.web_port)
    processes: dict[str, subprocess.Popen] = {}
    logs = []
    failure = None
    try:
        run_root.mkdir(parents=True, exist_ok=True)
        for child in children:
            log = child.log_path.open("a", encoding="utf-8")
            logs.append(log)
            processes[child.name] = subprocess.Popen(child.command, cwd=child.cwd, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
        deadline = time.monotonic() + args.startup_timeout
        while time.monotonic() < deadline:
            failure = next((name for name, proc in processes.items() if proc.poll() is not None), None)
            if failure:
                break
            if _healthy("http://127.0.0.1:8080/healthz") and _healthy(f"http://127.0.0.1:{args.web_port}/"):
                break
            time.sleep(0.25)
        else:
            failure = "readiness-timeout"
        if failure:
            return 4
        _write(evidence, {
            "status": "RUNNING", "pids": {name: proc.pid for name, proc in processes.items()},
            "endpoints": ["http://127.0.0.1:8080/healthz", f"http://127.0.0.1:{args.web_port}/traces"],
            "mysql": {"host": env.get("STORYOS_MYSQL_HOST"), "port": env.get("STORYOS_MYSQL_PORT"), "database": env.get("STORYOS_MYSQL_DB"), "password_configured": bool(env.get("STORYOS_MYSQL_PWD"))},
            "runtime_env_keys": list(loaded),
        })
        begun = time.monotonic()
        while args.max_seconds is None or time.monotonic() - begun < args.max_seconds:
            failure = next((name for name, proc in processes.items() if proc.poll() is not None), None)
            if failure:
                return 4
            time.sleep(0.5)
        return 0
    finally:
        if failure:
            _write(evidence, {"status": "FAILED", "reason": failure})
        for proc in processes.values():
            if proc.poll() is None:
                proc.terminate()
        for proc in processes.values():
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        for log in logs:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())
