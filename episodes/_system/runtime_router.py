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
VALID_IMAGE_RUNTIMES = {'CODEX', 'PRODUCT_RUNTIME', 'AUTO'}


def preferred_runtime() -> str:
    raw = str(storyos_config.get_path(_CONFIG, 'runtime.preferred_runtime') or 'WORK').strip().upper()
    if raw not in VALID:
        raise ValueError(f'invalid runtime.preferred_runtime: {raw!r}')
    return raw


def image_execution_runtime() -> tuple[str, str]:
    override = os.getenv('STORY_OS_IMAGE_RUNTIME', '').strip().upper()
    if override:
        if override not in VALID_IMAGE_RUNTIMES:
            raise ValueError(f'invalid STORY_OS_IMAGE_RUNTIME: {override!r}')
        return override, 'STORY_OS_IMAGE_RUNTIME override'
    configured = str(storyos_config.get_path(_CONFIG, 'runtime.image_execution_runtime') or 'AUTO').strip().upper()
    if configured not in VALID_IMAGE_RUNTIMES:
        raise ValueError(f'invalid runtime.image_execution_runtime: {configured!r}')
    return configured, 'config runtime.image_execution_runtime'


def _effective_runtime() -> str:
    override = os.getenv('STORY_OS_RUNTIME', '').strip().upper()
    return override if override in VALID else preferred_runtime()


def local_codex_allowed(*, explicit: bool = False) -> bool:
    """Return whether non-image Story OS work may launch local codex.exe.

    A CODEX image execution runtime does not authorize Codex to own Story/PREIMAGE/Review.
    """
    if _effective_runtime() == 'CODEX':
        return True
    return bool(explicit)


def local_codex_image_allowed(*, explicit: bool = False) -> bool:
    if explicit:
        return True
    image_runtime, _ = image_execution_runtime()
    if image_runtime == 'CODEX':
        return True
    return image_runtime == 'AUTO' and _effective_runtime() == 'CODEX'


def capabilities() -> dict:
    override = os.getenv('STORY_OS_RUNTIME', '').strip().upper()
    codex = shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    preferred = preferred_runtime()
    effective = _effective_runtime()
    image_runtime, image_runtime_reason = image_execution_runtime()
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
        'image_execution_runtime': image_runtime,
        'image_execution_runtime_reason': image_runtime_reason,
        'codex_image_controller_model': storyos_config.get_path(_CONFIG, 'runtime.codex_image_controller_model'),
        'codex_image_reasoning_effort': storyos_config.get_path(_CONFIG, 'runtime.codex_image_reasoning_effort'),
        'local_codex_image_spawn_allowed': bool(codex) and local_codex_image_allowed(),
        'codex_subscription_image_eligible': bool(codex) and local_codex_image_allowed(),
        'product_runtime_host_required': effective in {'WORK', 'WEB'},
        'product_runtime_image_host_required': effective in {'WORK', 'WEB'} and image_runtime in {'PRODUCT_RUNTIME', 'AUTO'},
        'note': 'WORK remains the authoring/review runtime. Image execution is independently routed; CODEX image mode authorizes only image generation/repair, not Codex full-auto ownership.',
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
