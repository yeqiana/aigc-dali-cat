#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_profile import resolve_profile
from story_review import review_required as story_review_required, verify as verify_story_review
from visual_review import review_required as visual_review_required, verify as verify_visual_review

ROOT = Path(__file__).resolve().parents[2]
GATES_REL = Path('meta/story-gates.json')
MANIFEST_REL = Path('meta/release-manifest.json')


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise SystemExit(f'JSON root must be object: {path}')
    return data


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ep_dir(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    return ep


def repo_path(raw: object, where: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise SystemExit(f'{where} missing')
    rel = Path(raw.strip())
    if rel.is_absolute():
        raise SystemExit(f'{where} must be repository-relative: {raw}')
    p = (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit(f'{where} escapes repository: {raw}')
    if not p.is_file():
        raise SystemExit(f'{where} file missing: {raw}')
    return p


def row_for_path(path: Path, role: str) -> dict:
    return {
        'role': role,
        'path': path.resolve().relative_to(ROOT.resolve()).as_posix(),
        'sha256': sha256_file(path),
    }


def story_assets(ep: Path) -> list[dict]:
    manifest = load_json(ep / MANIFEST_REL)
    artifacts = manifest.get('artifacts') or {}
    story = repo_path(artifacts.get('story'), 'manifest.artifacts.story')
    storyboard = repo_path(artifacts.get('storyboard'), 'manifest.artifacts.storyboard')
    rows = [row_for_path(story, 'story'), row_for_path(storyboard, 'storyboard')]
    if story_review_required(ep):
        errors = verify_story_review(ep)
        if errors:
            raise SystemExit('story semantic review failed: ' + '; '.join(errors))
        rows.append(row_for_path(ep / 'meta/story-semantic-review.json', 'story_semantic_review'))
    return rows


def visual_assets(ep: Path) -> tuple[list[dict], dict]:
    manifest = load_json(ep / MANIFEST_REL)
    gates = load_json(ep / GATES_REL)
    artifacts = manifest.get('artifacts') or {}
    visual = gates.get('visual') or {}
    rows: list[dict] = []
    spec = repo_path(artifacts.get('visual_spec'), 'manifest.artifacts.visual_spec')
    rows.append(row_for_path(spec, 'visual_spec'))

    sheet = visual.get('calibration_contact_sheet') or {}
    sheet_path = repo_path(sheet.get('path'), 'visual.calibration_contact_sheet.path')
    sheet_row = row_for_path(sheet_path, 'calibration_contact_sheet')
    expected_sheet = str(sheet.get('sha256') or '').lower()
    if expected_sheet and expected_sheet != sheet_row['sha256'].lower():
        raise SystemExit('calibration contact sheet hash already drifted before Visual Lock')
    rows.append(sheet_row)

    refs = visual.get('references') or {}
    for item in refs.get('items') or []:
        if not isinstance(item, dict) or item.get('decision') != 'passed':
            continue
        p = repo_path(item.get('path'), f"reference[{item.get('id')}].path")
        row = row_for_path(p, f"reference:{item.get('id')}")
        expected = str(item.get('sha256') or '').lower()
        if expected and expected != row['sha256'].lower():
            raise SystemExit(f"reference hash drift before Visual Lock: {item.get('id')}")
        rows.append(row)

    profile = resolve_profile(ep)
    pp = repo_path(profile.get('profile_path'), 'resolved visual profile')
    rows.append(row_for_path(pp, f"visual_profile:{profile.get('profile_id')}"))
    if visual_review_required(ep):
        errors = verify_visual_review(ep)
        if errors:
            raise SystemExit('visual profile review failed: ' + '; '.join(errors))
        rows.append(row_for_path(ep / 'meta/visual-profile-review.json', 'visual_profile_review'))
    return rows, profile


def lock(ep: Path, kind: str, rows: list[dict], profile: dict | None, note: str) -> dict:
    gates_path = ep / GATES_REL
    gates = load_json(gates_path)
    approvals = gates.setdefault('approvals', {})
    payload = {
        'approved': True,
        'user_approved': True,
        'approved_at': now_iso(),
        'artifacts': rows,
        'note': note or '',
    }
    if profile is not None:
        payload['resolved_visual_profile'] = profile
    approvals[kind] = payload
    save_json(gates_path, gates)
    return payload


def verify_lock(ep: Path, kind: str) -> list[str]:
    gates = load_json(ep / GATES_REL)
    item = (gates.get('approvals') or {}).get(kind)
    errors: list[str] = []
    if not isinstance(item, dict) or item.get('approved') is not True or item.get('user_approved') is not True:
        return [f'{kind} approval missing or not explicitly user-approved']
    rows = item.get('artifacts')
    if not isinstance(rows, list) or not rows:
        return [f'{kind} approval artifacts missing']
    for row in rows:
        if not isinstance(row, dict):
            errors.append(f'{kind}: invalid artifact row')
            continue
        raw = row.get('path')
        expected = str(row.get('sha256') or '')
        try:
            p = repo_path(raw, f'{kind}.artifact')
        except SystemExit as e:
            errors.append(str(e))
            continue
        actual = sha256_file(p)
        if actual.lower() != expected.lower():
            errors.append(f'{kind}: SHA256 drift {raw}\nexpected={expected}\nactual  ={actual}')
    if kind == 'visual_lock':
        try:
            current = resolve_profile(ep)
        except SystemExit as e:
            errors.append(str(e))
        else:
            locked = item.get('resolved_visual_profile') or {}
            for key in ('selection', 'profile_id', 'profile_path', 'capture_profile'):
                if str(current.get(key)) != str(locked.get(key)):
                    errors.append(f'visual_lock: resolved profile drift at {key}: locked={locked.get(key)!r}, current={current.get(key)!r}')
    return errors


def cmd_story(args: argparse.Namespace) -> int:
    if not args.user_approved:
        raise SystemExit('Story Lock requires --user-approved')
    ep = ep_dir(args.episode_dir)
    payload = lock(ep, 'story_lock', story_assets(ep), None, args.note)
    print('STORY LOCKED + SHA256')
    for row in payload['artifacts']:
        print(f"  {row['role']}: {row['sha256']}  {row['path']}")
    return 0


def cmd_visual(args: argparse.Namespace) -> int:
    if not args.user_approved:
        raise SystemExit('Visual Lock requires --user-approved')
    ep = ep_dir(args.episode_dir)
    rows, profile = visual_assets(ep)
    payload = lock(ep, 'visual_lock', rows, profile, args.note)
    print(f"VISUAL LOCKED + SHA256 | profile={profile['profile_id']} ({profile['selection']})")
    for row in payload['artifacts']:
        print(f"  {row['role']}: {row['sha256']}  {row['path']}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    ep = ep_dir(args.episode_dir)
    kinds = [args.kind] if args.kind != 'all' else ['story_lock', 'visual_lock']
    errors = []
    for kind in kinds:
        e = verify_lock(ep, kind)
        if e:
            errors.extend(e)
        else:
            print(f'{kind}: PASS')
    if errors:
        for e in errors:
            print(f'FAIL: {e}')
        return 2
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ep = ep_dir(args.episode_dir)
    gates = load_json(ep / GATES_REL)
    print(json.dumps(gates.get('approvals') or {}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description='Story OS V1.8 approval provenance + SHA locks')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('story'); p.add_argument('episode_dir'); p.add_argument('--user-approved', action='store_true'); p.add_argument('--note', default=''); p.set_defaults(func=cmd_story)
    p = sub.add_parser('visual'); p.add_argument('episode_dir'); p.add_argument('--user-approved', action='store_true'); p.add_argument('--note', default=''); p.set_defaults(func=cmd_visual)
    p = sub.add_parser('verify'); p.add_argument('episode_dir'); p.add_argument('--kind', choices=['story_lock','visual_lock','all'], default='all'); p.set_defaults(func=cmd_verify)
    p = sub.add_parser('status'); p.add_argument('episode_dir'); p.set_defaults(func=cmd_status)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
