#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stable Story OS evidence-gate entrypoint."""
from __future__ import annotations
import argparse
from pathlib import Path
from v18_gate import STATES, run_gate

def main() -> int:
    ap = argparse.ArgumentParser(description='Story OS stable evidence gate')
    ap.add_argument('episode_dir')
    ap.add_argument('--target', required=True, choices=STATES)
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    ok, messages = run_gate(ep, args.target)
    print(f"EVIDENCE GATE {'PASS' if ok else 'FAIL'} | target={args.target}")
    for msg in messages:
        print(('INFO: ' if ok else 'FAIL: ') + msg)
    return 0 if ok else 2

if __name__ == '__main__':
    raise SystemExit(main())
