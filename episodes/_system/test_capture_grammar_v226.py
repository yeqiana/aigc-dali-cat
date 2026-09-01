#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"

def main():
    cmds = [
        [sys.executable, str(SYSTEM / "capture_grammar_v226.py")],
        [sys.executable, str(SYSTEM / "visual_profile_bridge_v224.py")],
        [sys.executable, str(SYSTEM / "codex_subscription_image.py"), "self-test"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
        if r.stdout.strip():
            print(r.stdout.strip())
        if r.returncode != 0:
            if r.stderr.strip():
                print(r.stderr.strip())
            return r.returncode

    bridge_text = (SYSTEM / "visual_profile_bridge_v224.py").read_text(encoding="utf-8")
    required = [
        "GLOBAL CAPTURE GRAMMAR",
        "capture_grammar_v226",
        "visual_profile_composition_hint_NON_AUTHORITY",
    ]
    for token in required:
        if token not in bridge_text:
            print(f"missing token: {token}")
            return 2

    print("STORY OS V2.2.6 GLOBAL FIRST-PERSON CAPTURE GRAMMAR INTEGRATION SELF-TEST PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
