#!/usr/bin/env python3
"""Compatibility wrapper. V1.1 delegates to the repository's single validator."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_all.py <episode_dir> [--metadata-only] [--target STATE]", file=sys.stderr)
        return 2
    repo = Path(__file__).resolve().parents[3]
    validator = repo / "episodes" / "_system" / "validate_episode.py"
    cmd = [sys.executable, str(validator), *sys.argv[1:]]
    return subprocess.run(cmd, cwd=repo).returncode

if __name__ == "__main__":
    raise SystemExit(main())
