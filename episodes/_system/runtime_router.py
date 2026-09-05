#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import os
import shutil
from pathlib import Path

from story_os_contract import story_os_version
import storyos_config

ROOT = Path(__file__).resolve().parents[2]
_CONFIG = storyos_config.load_config()
CONTRACT = ROOT / str(storyos_config.get_path(_CONFIG, 'paths.runtime_contract'))
VALID = {'CODEX', 'WORK', 'WEB'}


def preferred_runtime() -> str:
    raw = str(storyos_config.get_path(_CONFIG, 'runtime.preferred_runtime') or 'WORK').strip().upper()
    if raw not in VALID:
        raise ValueError(f'invalid runtime.preferred_runtime: {raw!r}')
    return raw


def local_codex_allowed(*, explicit: bool = False) -> bool:
    """Return whether Story OS may launch local codex.exe in this process.

    Product runtimes never silently consume local Codex quota. CODEX remains available
    through STORY_OS_RUNTIME=CODEX or an explicit caller opt-in.
    """
    runtime, _ = detect()
    if runtime == 'CODEX':
        return True
    return bool(explicit)


def capabilities() -> dict:
    override = os.getenv('STORY_OS_RUNTIME', '').strip().upper()
    codex = shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    preferred = preferred_runtime()
    effective = override if override in VALID else preferred
    return {
        'story_os_version': story_os_version(),
        'runtime_override': override if override in VALID else None,
        'preferred_runtime': preferred,
        'effective_runtime': effective,
        'repository_filesystem': ROOT.is_dir(),
        'repository_writable': os.access(ROOT, os.W_OK),
        'codex_cli': codex,
        'codex_cli_installed': bool(codex),
        'local_codex_spawn_allowed': effective == 'CODEX',
        'codex_subscription_image_eligible': bool(codex) and effective == 'CODEX',
        'product_runtime_host_required': effective in {'WORK', 'WEB'},
        'note': 'WORK is product-runtime-first by default. Local Codex is installed capability only and is never a silent fallback; set STORY_OS_RUNTIME=CODEX to opt in.',
    }


def detect() -> tuple[str, str]:
    caps = capabilities()
    if caps['runtime_override']:
        return caps['runtime_override'], 'STORY_OS_RUNTIME override'
    runtime = caps['preferred_runtime']
    return runtime, 'config runtime.preferred_runtime'

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
