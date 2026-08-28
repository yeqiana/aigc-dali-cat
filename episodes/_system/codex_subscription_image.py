#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate exactly one image using the current Codex CLI ChatGPT sign-in."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

PNG = b'\x89PNG\r\n\x1a\n'
JPEG = b'\xff\xd8\xff'

class BackendError(RuntimeError):
    pass

def valid_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 16:
        return False
    header = path.read_bytes()[:16]
    return header.startswith(PNG) or header.startswith(JPEG)

def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    if not value:
        raise BackendError('Codex CLI not found on PATH')
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise BackendError(f'Codex CLI not found: {path}')
    return path

def command_prefix(codex: Path) -> list[str]:
    if os.name == 'nt' and codex.suffix.lower() in {'.cmd', '.bat'}:
        return ['cmd.exe', '/d', '/c', str(codex)]
    return [str(codex)]

def worker_prompt(scene: str, refs: list[Path], size: str) -> str:
    reference_lines = '\n'.join(f'- reference {i}: {p.name}' for i, p in enumerate(refs, 1)) or '- no references'
    return (
        'You are an isolated Story OS image worker. Use image_generation exactly once.\n'
        f'{reference_lines}\n'
        'Use attached images only as continuity references required by the scene. '
        f'Do not invent a different story. Request {size}.\n\n'
        f'<scene>\n{scene}\n</scene>\n\n'
        'After generation, save or copy the actual generated candidate to ./out.png. '
        'Do not synthesize an image with Python or reuse a cached image. Reply only after out.png exists.'
    )

def generate(args: argparse.Namespace) -> dict:
    prompt_path = args.prompt_file.expanduser().resolve()
    if not prompt_path.is_file():
        raise BackendError(f'prompt missing: {prompt_path}')
    scene = prompt_path.read_text(encoding='utf-8').strip()
    if not scene:
        raise BackendError('prompt is empty')
    refs = [p.expanduser().resolve() for p in args.reference]
    if len(refs) > 2:
        raise BackendError('at most two references are supported')
    for ref in refs:
        if not valid_image(ref):
            raise BackendError(f'invalid reference image: {ref}')
    output = args.output.expanduser().resolve()
    log = args.log.expanduser().resolve()
    if output.exists() and not args.overwrite:
        raise BackendError(f'output exists: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    codex = resolve_codex(args.codex)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='story-os-image-') as raw_dir:
        workdir = Path(raw_dir)
        local_refs = []
        for index, source in enumerate(refs, 1):
            ext = source.suffix.lower() if source.suffix.lower() in {'.png', '.jpg', '.jpeg'} else '.png'
            target = workdir / f'reference-{index:02d}{ext}'
            shutil.copy2(source, target)
            local_refs.append(target)
        cmd = command_prefix(codex) + [
            'exec', '--skip-git-repo-check', '--ephemeral', '--enable', 'image_generation',
            '-c', 'model_reasoning_effort="low"', '-s', 'workspace-write', '-C', str(workdir), '--json'
        ]
        for ref in local_refs:
            cmd.extend(['-i', str(ref)])
        cmd.append('-')
        with log.open('w', encoding='utf-8', newline='\n') as log_handle:
            try:
                completed = subprocess.run(
                    cmd,
                    input=worker_prompt(scene, local_refs, args.size),
                    text=True,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    timeout=args.timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise BackendError(f'image worker timeout after {args.timeout}s; log={log}') from exc
        candidate = workdir / 'out.png'
        if not valid_image(candidate):
            alternatives = [p for p in workdir.glob('*.png') if not p.name.startswith('reference-')]
            if alternatives:
                candidate = max(alternatives, key=lambda p: p.stat().st_mtime)
        if completed.returncode != 0 or not valid_image(candidate):
            raise BackendError(f'Codex image worker failed rc={completed.returncode}; log={log}')
        staged = output.with_name('.' + output.name + '.partial')
        shutil.copy2(candidate, staged)
        os.replace(staged, output)
    return {
        'ok': True,
        'backend': 'codex_subscription',
        'output': str(output),
        'log': str(log),
        'size': args.size,
        'references': [str(p) for p in refs],
        'elapsed_seconds': round(time.monotonic() - started, 2),
    }

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('generate')
    p.add_argument('--prompt-file', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--log', required=True, type=Path)
    p.add_argument('--reference', action='append', default=[], type=Path)
    p.add_argument('--size', default='1024x1280')
    p.add_argument('--timeout', type=int, default=600)
    p.add_argument('--codex')
    p.add_argument('--overwrite', action='store_true')
    sub.add_parser('self-test')
    args = ap.parse_args()
    if args.cmd == 'self-test':
        assert worker_prompt('x', [], '1024x1280').count('image_generation') == 1
        assert not valid_image(Path('__missing__'))
        print('CODEX SUBSCRIPTION IMAGE BACKEND SELF-TEST PASS')
        return 0
    if args.timeout < 60 or args.timeout > 1200:
        raise SystemExit('timeout must be 60..1200 seconds')
    try:
        result = generate(args)
    except (BackendError, OSError, UnicodeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
