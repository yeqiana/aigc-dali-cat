#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package current real publish/approved assets without pretending Release Lock approval."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('episode_dir')
    ap.add_argument('--label', default='DELEGATED_AUTO')
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    ledger = ep / 'meta' / 'production-ledger.json'
    if not ledger.is_file():
        raise SystemExit('production-ledger missing')
    data = json.loads(ledger.read_text(encoding='utf-8'))
    frames = data.get('frames') or {}
    publish_dir = ep / 'production' / 'publish'
    approved_dir = ep / 'production' / 'approved'
    missing = []
    files = []
    for key, row in sorted(frames.items()):
        if row.get('status') not in {'PASSED', 'LOCKED'}:
            missing.append(f'{key}:{row.get("status")}')
            continue
        candidates = list(publish_dir.glob(f'{key}.*')) if publish_dir.is_dir() else []
        if not candidates:
            candidates = list(approved_dir.glob(f'{key}.*')) if approved_dir.is_dir() else []
        candidates = [p for p in candidates if p.is_file()]
        if not candidates:
            missing.append(f'{key}:file_missing')
            continue
        files.append((key, candidates[0]))
    if missing:
        raise SystemExit('cannot package; incomplete frames: ' + ', '.join(missing))
    out_dir = ep / 'deliveries'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{ep.name}_{args.label}.zip'
    report = {
        'schema_version': 1,
        'story_os_version': '2.0.1',
        'approval_basis': 'delegated_auto_review',
        'direct_release_lock': False,
        'built_at': dt.datetime.now().astimezone().isoformat(),
        'files': [],
    }
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for key, path in files:
            arc = f'publish/{key}{path.suffix.lower()}'
            zf.write(path, arc)
            report['files'].append({'frame': key, 'path': arc, 'sha256': sha256_file(path)})
        zf.writestr('DELEGATED_AUTO_REPORT.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(out)
    print('SHA256', sha256_file(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
