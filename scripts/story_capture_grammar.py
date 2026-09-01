#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

import capture_grammar_v226


def main():
    ap = argparse.ArgumentParser(description="Story OS Capture Grammar")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("show")
    p.add_argument("episode_dir")

    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    result = capture_grammar_v226.compile_capture_contract(ep)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
