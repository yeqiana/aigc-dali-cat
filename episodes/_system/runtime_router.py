#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import os
import shutil
from pathlib import Path

from story_os_contract import story_os_version

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'runtimes' / 'runtime-contract.json'
VALID = {'CODEX', 'WORK', 'WEB'}

def capabilities() -> dict:
    override = os.getenv('STORY_OS_RUNTIME', '').strip().upper()
    codex = shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    return {
        'story_os_version': story_os_version(),
        'runtime_override': override if override in VALID else None,
        'repository_filesystem': ROOT.is_dir(),
        'repository_writable': os.access(ROOT, os.W_OK),
        'codex_cli': codex,
        'codex_subscription_image_eligible': bool(codex),
        'note': 'WORK/WEB are normally selected by the ChatGPT product runtime; local Python proves repository code execution and therefore maps to CODEX unless explicitly overridden.',
    }

def detect() -> tuple[str, str]:
    caps = capabilities()
    if caps['runtime_override']:
        return caps['runtime_override'], 'STORY_OS_RUNTIME override'
    return 'CODEX', 'local repository code execution is available'

def main() -> int:
    ap = argparse.ArgumentParser(description=f'Story OS V{story_os_version()} runtime router')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('detect'); p.add_argument('--json', action='store_true')
    sub.add_parser('capabilities')
    sub.add_parser('contract')
    p = sub.add_parser('show'); p.add_argument('runtime', choices=sorted(VALID))
    args = ap.parse_args()
    if args.cmd == 'detect':
        runtime, reason = detect()
        if args.json:
            print(json.dumps({'runtime': runtime, 'reason': reason, 'capabilities': capabilities()}, ensure_ascii=False, indent=2))
        else:
            print(runtime)
        return 0
    if args.cmd == 'capabilities':
        print(json.dumps(capabilities(), ensure_ascii=False, indent=2)); return 0
    if args.cmd == 'contract':
        print(CONTRACT.read_text(encoding='utf-8')); return 0
    print((ROOT / 'runtimes' / f'{args.runtime}.md').read_text(encoding='utf-8'))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
