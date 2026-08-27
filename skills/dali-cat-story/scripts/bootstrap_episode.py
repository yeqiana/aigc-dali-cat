#!/usr/bin/env python3
"""Compatibility wrapper around episodes/_system/episode_state.py init."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    state = repo / "episodes" / "_system" / "episode_state.py"
    print("V1.1 uses the repository's single state machine.")
    print("Example:")
    print('  python episodes/_system/episode_state.py init <episode_dir> --id 10-01 --series 10_新系列 --title "新故事" --frame-count 20')
    if len(sys.argv) > 1:
        print("\nForwarding arguments to episode_state.py init ...")
        return subprocess.run([sys.executable, str(state), "init", *sys.argv[1:]], cwd=repo).returncode
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
