#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"

def run(cmd):
    r = subprocess.run(
        cmd, cwd=ROOT, text=True, capture_output=True,
        encoding="utf-8", errors="replace"
    )
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        if r.stderr.strip():
            print(r.stderr.strip())
        raise SystemExit(r.returncode)

def main():
    run([sys.executable, str(SYSTEM / "test_stage_v227.py"), "self-test"])
    run([sys.executable, str(SYSTEM / "test_stage_v225.py"), "self-test"])
    run([sys.executable, str(SYSTEM / "capture_grammar_v226.py")])
    run([sys.executable, str(SYSTEM / "codex_subscription_image.py"), "self-test"])

    source = (SYSTEM / "test_stage_v227.py").read_text(encoding="utf-8")
    forbidden_prepare_tokens = [
        "skip_if_previous_pass\": True",
        "reuse_previous_visual_test\": True",
        "cache_hit_allowed\": True",
    ]
    for token in forbidden_prepare_tokens:
        if token in source:
            raise SystemExit(f"append-only contract violated: {token}")

    required = [
        "AUDIT_ONLY_NEVER_EXECUTION_INPUT",
        "VISUAL_TEST_NATIVE_IMAGE_REQUIRED",
        "visual-record-failure",
        "visual-history",
        "run_id",
    ]
    for token in required:
        if token not in source:
            raise SystemExit(f"missing V2.2.7 token: {token}")

    print("STORY OS V2.2.7 APPEND-ONLY INTEGRATION SELF-TEST PASS")

if __name__ == "__main__":
    main()
