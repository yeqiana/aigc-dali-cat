#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from approval_lock import verify_lock
from release_package import verify_payload
from visual_profile import resolve_profile

ROOT = Path(__file__).resolve().parents[2]
STATES = [
    'IDEA_LOCKED',
    'STORYBOARD_LOCKED',
    'VISUAL_CALIBRATED',
    'PRODUCTION_PASSED',
    'PUBLISH_READY',
    'PUBLISHED',
    'DATA_REVIEWED',
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'JSON root must be object: {path}')
    return data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def version_at_least(raw: object, minimum=(1, 8)) -> bool:
    try:
        parts = str(raw or '').strip().split('.')
        current = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except (ValueError, TypeError, IndexError):
        return False
    return current >= minimum


def resolve_repo_file(raw: object) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    rel = Path(raw.strip())
    if rel.is_absolute():
        return None
    p = (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return p if p.is_file() else None


def is_v18_episode(state: dict, manifest: dict) -> bool:
    return version_at_least(state.get('tool_version')) or version_at_least(manifest.get('tool_version'))


def check_text_audit(ep: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    path = ep / 'meta/text-audit.json'
    if not path.is_file():
        return ['PUBLISH_READY requires meta/text-audit.json']
    try:
        report = load_json(path)
    except Exception as e:
        return [f'invalid text-audit.json: {e}']
    summary = report.get('summary') or {}
    if summary.get('passed') is not True:
        errors.append('text audit summary.passed must be true')
    source_sha = str(report.get('source_sha256') or '')
    if len(source_sha) != 64:
        errors.append('text-audit.json missing source_sha256; rerun Story OS audit-text')
    captions = resolve_repo_file((manifest.get('artifacts') or {}).get('captions'))
    if captions is None:
        errors.append('manifest.artifacts.captions missing/unreadable')
    elif source_sha and len(source_sha) == 64:
        actual = sha256_file(captions)
        if actual.lower() != source_sha.lower():
            errors.append(f'text audit stale: captions SHA256 drift\nexpected={source_sha}\nactual  ={actual}')
    return errors


def check_release_package(ep: Path) -> list[str]:
    path = ep / 'meta/release-package.json'
    if not path.is_file():
        return ['PUBLISH_READY requires meta/release-package.json; run release_package.py build']
    try:
        payload = load_json(path)
    except Exception as e:
        return [f'invalid release-package.json: {e}']
    errors = []
    if payload.get('user_approved') is not True:
        errors.append('release package must be explicitly user-approved')
    errors.extend(verify_payload(ep, payload))
    return errors


def run_gate(ep: Path, target: str) -> tuple[bool, list[str]]:
    state = load_json(ep / 'meta/episode-state.json')
    manifest = load_json(ep / 'meta/release-manifest.json')
    if not is_v18_episode(state, manifest):
        return True, ['legacy/pre-V1.8 episode: evidence gate not enforced until episode metadata is upgraded']
    idx = STATES.index(target)
    errors: list[str] = []

    if idx >= STATES.index('STORYBOARD_LOCKED'):
        errors.extend(verify_lock(ep, 'story_lock'))
    if idx >= STATES.index('VISUAL_CALIBRATED'):
        try:
            resolve_profile(ep)
        except SystemExit as e:
            errors.append(f'visual profile: {e}')
        errors.extend(verify_lock(ep, 'visual_lock'))
    if idx >= STATES.index('PUBLISH_READY'):
        errors.extend(check_text_audit(ep, manifest))
        errors.extend(check_release_package(ep))
    return not errors, errors


def main() -> int:
    ap = argparse.ArgumentParser(description='Compatibility evidence gate implementation introduced in Story OS V1.8')
    ap.add_argument('episode_dir')
    ap.add_argument('--target', required=True, choices=STATES)
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    ok, messages = run_gate(ep, args.target)
    print(f"EVIDENCE COMPAT GATE {'PASS' if ok else 'FAIL'} | target={args.target}")
    for msg in messages:
        print(('INFO: ' if ok else 'FAIL: ') + msg)
    return 0 if ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
