#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record and verify delegated-auto Story/Visual/Release approvals without impersonating direct user review."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from approval_lock import story_assets, visual_assets
from story_os_contract import story_os_version

REL = Path('meta/delegated-approvals.json')
CHECKPOINT = Path('meta/runtime-checkpoint.json')
ROOT = Path(__file__).resolve().parents[2]
STORY_OS_VERSION = story_os_version()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise SystemExit(f'JSON root must be object: {path}')
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def authorized(ep: Path) -> tuple[bool, str]:
    p = ep / CHECKPOINT
    if not p.is_file():
        return False, 'runtime-checkpoint missing'
    d = read_json(p)
    if d.get('continuous_execution_authorized') is not True:
        return False, 'continuous_execution_authorized is not true'
    if d.get('approval_basis') not in {'delegated_continuous_execution', 'delegated_auto_review'}:
        return False, 'runtime checkpoint approval_basis is not delegated'
    return True, ''


def base_payload(kind: str, rows: list[dict], note: str) -> dict:
    return {
        'approved': True,
        'user_approved': False,
        'delegated_auto_review': True,
        'approval_basis': 'delegated_auto_review',
        'kind': kind,
        'approved_at': now(),
        'artifacts': rows,
        'note': note or '',
    }


def load_store(ep: Path) -> tuple[Path, dict]:
    p = ep / REL
    if p.is_file():
        return p, read_json(p)
    return p, {'schema_version': 1, 'story_os_version': STORY_OS_VERSION, 'approvals': {}}


def repo_file(raw: str) -> Path:
    rel = Path(raw)
    if rel.is_absolute():
        p = rel.resolve()
    else:
        p = (ROOT / rel).resolve()
    if not p.is_file():
        raise SystemExit(f'artifact missing: {raw}')
    return p


def cmd_record(args: argparse.Namespace) -> int:
    ep = Path(args.episode_dir).resolve()
    ok, reason = authorized(ep)
    if not ok:
        raise SystemExit('delegated approval requires full-auto authorization: ' + reason)
    if args.kind == 'story_lock':
        rows = story_assets(ep)
        profile = None
    elif args.kind == 'visual_lock':
        rows, profile = visual_assets(ep)
    else:
        report = ep / 'meta' / 'delegated-release.json'
        if not report.is_file():
            raise SystemExit('delegated release report missing; build delegated delivery first')
        d = read_json(report)
        rows = d.get('files') or []
        package = d.get('package') or {}
        if not rows or not package.get('path') or not package.get('sha256'):
            raise SystemExit('delegated release report incomplete')
        rows = list(rows) + [{
            'role': 'delegated_zip',
            'path': package['path'],
            'sha256': package['sha256'],
        }]
        profile = None
    payload = base_payload(args.kind, rows, args.note)
    if profile is not None:
        payload['resolved_visual_profile'] = profile
    path, store = load_store(ep)
    store['story_os_version'] = STORY_OS_VERSION
    store.setdefault('approvals', {})[args.kind] = payload
    write_json(path, store)
    print(f'{args.kind}: DELEGATED AUTO LOCKED')
    return 0


def verify(ep: Path, kind: str) -> list[str]:
    ok, reason = authorized(ep)
    if not ok:
        return ['delegated authorization invalid: ' + reason]
    path = ep / REL
    if not path.is_file():
        return ['delegated approvals missing']
    item = (read_json(path).get('approvals') or {}).get(kind)
    if not isinstance(item, dict):
        return [f'{kind}: delegated approval missing']
    if item.get('approved') is not True or item.get('delegated_auto_review') is not True or item.get('user_approved') is not False:
        return [f'{kind}: delegated approval provenance invalid']
    errors = []
    rows = item.get('artifacts') or []
    if not rows:
        errors.append(f'{kind}: delegated approval artifacts missing')
    for row in rows:
        if not isinstance(row, dict) or not row.get('path') or not row.get('sha256'):
            errors.append(f'{kind}: invalid artifact row')
            continue
        try:
            p = repo_file(str(row['path']))
        except SystemExit as exc:
            errors.append(str(exc)); continue
        actual = sha256_file(p)
        if actual.lower() != str(row['sha256']).lower():
            errors.append(f'{kind}: SHA256 drift {row["path"]}')
    if kind == 'visual_lock':
        try:
            _, current = visual_assets(ep)
        except SystemExit as exc:
            errors.append(str(exc))
        else:
            locked = item.get('resolved_visual_profile') or {}
            for key in ('selection','profile_id','profile_path','capture_profile'):
                if str(current.get(key)) != str(locked.get(key)):
                    errors.append(f'visual_lock: profile drift at {key}')
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('record','verify'):
        p = sub.add_parser(name)
        p.add_argument('episode_dir')
        p.add_argument('kind', choices=['story_lock','visual_lock','release_lock'])
        if name == 'record': p.add_argument('--note', default='')
    p = sub.add_parser('show'); p.add_argument('episode_dir')
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if args.cmd == 'show':
        path = ep / REL
        print(path.read_text(encoding='utf-8') if path.is_file() else '{}')
        return 0
    if args.cmd == 'record':
        return cmd_record(args)
    errors = verify(ep, args.kind)
    if errors:
        for e in errors: print('FAIL:', e)
        return 2
    print(f'{args.kind}: DELEGATED PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
