#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

TX_ROOT = Path('meta/text-revisions')
ALLOWED_SUFFIXES = {'.md', '.txt', '.yaml', '.yml', '.json'}
PROTECTED_EXACT = {
    'meta/release-manifest.json',
    'meta/production-ledger.json',
    'meta/episode-state.json',
    'meta/story-gates.json',
}
PROTECTED_DIR_HINTS = ('production/approved', 'production/publish', 'references', 'reference-assets', 'reference_assets')


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise SystemExit(f'file not found: {path}')
    if not isinstance(data, dict):
        raise SystemExit(f'invalid transaction JSON: {path}')
    return data


def resolve_episode(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    return ep


def rel_to_ep(ep: Path, raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = ep / p
    p = p.resolve()
    try:
        rel = p.relative_to(ep)
    except ValueError:
        raise SystemExit(f'text revision file must be inside episode directory: {p}')
    rels = rel.as_posix()
    if rel.suffix.lower() not in ALLOWED_SUFFIXES:
        raise SystemExit(f'unsupported text revision file type: {rel}')
    if rels in PROTECTED_EXACT or rels.startswith('meta/frame-reviews/') or rels.startswith('meta/text-revisions/'):
        raise SystemExit(f'protected system file cannot enter text revision transaction: {rel}')
    return rel


def protected_files(ep: Path) -> list[Path]:
    found: dict[str, Path] = {}
    for rel in PROTECTED_EXACT:
        p = ep / rel
        if p.is_file():
            found[rel] = p
    for base in [ep / 'production/approved', ep / 'production/publish']:
        if base.is_dir():
            for p in base.rglob('*'):
                if p.is_file():
                    found[p.relative_to(ep).as_posix()] = p
    for p in ep.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(ep).as_posix()
        if rel.startswith('meta/text-revisions/'):
            continue
        low = rel.lower()
        if any(hint in low for hint in PROTECTED_DIR_HINTS):
            found[rel] = p
    return [found[k] for k in sorted(found)]


def protected_snapshot(ep: Path) -> dict[str, str]:
    return {p.relative_to(ep).as_posix(): sha256_file(p) for p in protected_files(ep)}


def current_tx(ep: Path) -> tuple[Path, dict]:
    root = ep / TX_ROOT
    active = root / 'ACTIVE'
    if not active.is_file():
        raise SystemExit('no active text revision transaction')
    txid = active.read_text(encoding='utf-8').strip()
    txdir = root / txid
    data = load_json(txdir / 'transaction.json')
    return txdir, data


def copy_snapshot(ep: Path, txdir: Path, folder: str, rels: list[Path]) -> None:
    for rel in rels:
        src = ep / rel
        dst = txdir / folder / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def cmd_start(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    root = ep / TX_ROOT
    root.mkdir(parents=True, exist_ok=True)
    active = root / 'ACTIVE'
    if active.exists():
        raise SystemExit(f'an active text revision already exists: {active.read_text(encoding="utf-8").strip()}')
    if not args.file:
        raise SystemExit('provide at least one --file; explicit file selection prevents accidental scope expansion')
    rels = []
    seen = set()
    for raw in args.file:
        rel = rel_to_ep(ep, raw)
        if rel.as_posix() in seen:
            continue
        if not (ep / rel).is_file():
            raise SystemExit(f'text file not found: {ep / rel}')
        seen.add(rel.as_posix())
        rels.append(rel)

    txid = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    txdir = root / txid
    txdir.mkdir(parents=True)
    copy_snapshot(ep, txdir, 'before', rels)
    files = {rel.as_posix(): {'before_sha256': sha256_file(ep / rel)} for rel in rels}
    data = {
        'schema_version': 1,
        'txid': txid,
        'status': 'OPEN',
        'started_at': now_iso(),
        'note': args.note or '',
        'files': files,
        'protected_snapshot': protected_snapshot(ep),
        'audit': None,
    }
    save_json(txdir / 'transaction.json', data)
    active.write_text(txid + '\n', encoding='utf-8')
    print(f'text revision started: {txid}')
    for rel in rels:
        print(f'  editable: {rel.as_posix()}')
    print('Images/reference assets/release manifest/state files are protected by snapshot/hash checks.')
    return 0


def build_diff(ep: Path, txdir: Path, data: dict) -> str:
    chunks = []
    for rels in data.get('files', {}):
        rel = Path(rels)
        before = (txdir / 'before' / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        current = (ep / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(before, current, fromfile=f'before/{rels}', tofile=f'current/{rels}'))
    text = ''.join(chunks)
    (txdir / 'changes.diff').write_text(text, encoding='utf-8')
    return text


def verify_protected(ep: Path, data: dict) -> list[str]:
    before = data.get('protected_snapshot') or {}
    after = protected_snapshot(ep)
    changed = []
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            changed.append(key)
    return changed


def run_audits(ep: Path, txdir: Path, data: dict, strict_warnings: bool) -> list[dict]:
    script = Path(__file__).resolve().parent / 'text_audit.py'
    results = []
    for rels in data.get('files', {}):
        rel = Path(rels)
        if rel.suffix.lower() not in {'.yaml', '.yml', '.txt'}:
            continue
        report = txdir / 'audit' / (rels.replace('/', '__') + '.json')
        report.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(script), str(ep), '--file', str(ep / rel), '--report', str(report)]
        if strict_warnings:
            cmd.append('--strict-warnings')
        code = subprocess.call(cmd)
        results.append({'file': rels, 'report': str(report.relative_to(txdir)), 'exit_code': code})
    return results


def cmd_diff(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    txdir, data = current_tx(ep)
    diff = build_diff(ep, txdir, data)
    print(diff if diff else '(no text changes)')
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    txdir, data = current_tx(ep)
    if data.get('status') != 'OPEN':
        raise SystemExit(f'transaction must be OPEN to submit; got {data.get("status")}')
    changed_protected = verify_protected(ep, data)
    if changed_protected:
        raise SystemExit('protected assets changed during text revision:\n  ' + '\n  '.join(changed_protected))
    diff = build_diff(ep, txdir, data)
    if not diff:
        raise SystemExit('no text changes detected')
    audit_results = run_audits(ep, txdir, data, args.strict_warnings)
    failed = [r for r in audit_results if r['exit_code'] != 0]
    if failed:
        raise SystemExit('text audit failed; inspect transaction audit reports before submitting')
    for rels, info in data.get('files', {}).items():
        info['submitted_sha256'] = sha256_file(ep / rels)
    data['status'] = 'SUBMITTED'
    data['submitted_at'] = now_iso()
    data['audit'] = audit_results
    save_json(txdir / 'transaction.json', data)
    print(f'text revision submitted: {data["txid"]}')
    print(f'diff: {txdir / "changes.diff"}')
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    if not args.user_approved:
        raise SystemExit('approval requires --user-approved')
    ep = resolve_episode(args.episode_dir)
    txdir, data = current_tx(ep)
    if data.get('status') != 'SUBMITTED':
        raise SystemExit(f'transaction must be SUBMITTED to approve; got {data.get("status")}')
    changed_protected = verify_protected(ep, data)
    if changed_protected:
        raise SystemExit('protected assets changed before approval:\n  ' + '\n  '.join(changed_protected))
    rels = [Path(x) for x in data.get('files', {})]
    copy_snapshot(ep, txdir, 'approved', rels)
    for rels_s, info in data.get('files', {}).items():
        current = sha256_file(ep / rels_s)
        if current != info.get('submitted_sha256'):
            raise SystemExit(f'text changed after submit and before approval: {rels_s}')
        info['approved_sha256'] = current
    data['status'] = 'APPROVED'
    data['approved_at'] = now_iso()
    save_json(txdir / 'transaction.json', data)
    (ep / TX_ROOT / 'ACTIVE').unlink(missing_ok=True)
    print(f'text revision APPROVED: {data["txid"]}')
    return 0


def cmd_revert(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    txdir, data = current_tx(ep)
    for rels in data.get('files', {}):
        rel = Path(rels)
        src = txdir / 'before' / rel
        dst = ep / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    data['status'] = 'REVERTED'
    data['reverted_at'] = now_iso()
    data['revert_reason'] = args.reason or ''
    save_json(txdir / 'transaction.json', data)
    (ep / TX_ROOT / 'ACTIVE').unlink(missing_ok=True)
    print(f'text revision REVERTED: {data["txid"]}')
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    txdir, data = current_tx(ep)
    payload = dict(data)
    payload['transaction_dir'] = str(txdir)
    payload['protected_changed'] = verify_protected(ep, data)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description='Story OS V1.7 text-only revision transaction')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('start')
    p.add_argument('episode_dir')
    p.add_argument('--file', action='append', help='episode-relative file path; repeatable')
    p.add_argument('--note')
    p.set_defaults(func=cmd_start)

    p = sub.add_parser('diff')
    p.add_argument('episode_dir')
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser('submit')
    p.add_argument('episode_dir')
    p.add_argument('--strict-warnings', action='store_true')
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser('approve')
    p.add_argument('episode_dir')
    p.add_argument('--user-approved', action='store_true')
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser('revert')
    p.add_argument('episode_dir')
    p.add_argument('--reason')
    p.set_defaults(func=cmd_revert)

    p = sub.add_parser('status')
    p.add_argument('episode_dir')
    p.set_defaults(func=cmd_status)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
