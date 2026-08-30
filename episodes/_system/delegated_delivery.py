#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build and verify a complete delegated-auto delivery package from real publish assets."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path

from story_os_contract import story_os_version
from frame_semantic_review import (
    TARGET_CONTRACT as FRAME_SEMANTIC_TARGET,
    episode_contract_version,
    review_required as frame_semantic_required,
    verify_episode as verify_frame_semantic_episode,
    version_tuple,
)
from machine_gate import validate as validate_machine_gate
import final_candidate_snapshot as final_snapshot

ROOT = Path(__file__).resolve().parents[2]
REPORT_REL = Path('meta/delegated-release.json')


def read_json(p: Path) -> dict:
    d=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(d,dict): raise SystemExit(f'JSON root must be object: {p}')
    return d

def write_json(p: Path,d: dict):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def repo_rel(p: Path) -> str:
    try:return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:return p.resolve().as_posix()
def resolve_repo(raw: object, where: str) -> Path:
    if not isinstance(raw,str) or not raw.strip(): raise SystemExit(f'{where} missing')
    rel=Path(raw.strip()); p=(ROOT/rel).resolve() if not rel.is_absolute() else rel.resolve()
    if not p.is_file(): raise SystemExit(f'{where} missing: {raw}')
    return p
def row(p: Path,role: str,arc: str) -> dict:
    return {'role':role,'path':repo_rel(p),'archive_path':arc,'sha256':sha256_file(p),'bytes':p.stat().st_size}


def machine_gate_required_for_delivery(ep: Path) -> bool:
    """Preserve legacy delivery without weakening current strict contracts.

    Explicit pre-2.0.3.3 episodes that never had story-gates may still be packaged.
    Any episode with story-gates, and every 2.0.3.3+ contract, must pass machine gate.
    """
    if (ep/'meta/story-gates.json').is_file():
        return True
    return version_tuple(episode_contract_version(ep)) >= FRAME_SEMANTIC_TARGET


def preflight(ep: Path) -> None:
    if final_snapshot.required(ep) or (ep/final_snapshot.SNAPSHOT_REL).is_file():
        errors=final_snapshot.verify(ep)
        if errors: raise SystemExit('final candidate snapshot preflight failed: ' + '; '.join(errors))
    if frame_semantic_required(ep):
        errors = verify_frame_semantic_episode(ep, metadata_only=False, write_audit=True)
        if errors:
            raise SystemExit('frame semantic preflight failed: ' + '; '.join(errors))
    if machine_gate_required_for_delivery(ep):
        findings = validate_machine_gate(ep, 'PRODUCTION_PASSED', metadata_only=False)
        failures = [str(x) for x in findings if getattr(x, 'level', None) == 'FAIL']
        if failures:
            raise SystemExit('PRODUCTION_PASSED machine gate failed before delivery: ' + '; '.join(failures))

def gather_from_snapshot(ep: Path) -> tuple[list[dict], dict]:
    errors=final_snapshot.verify(ep)
    if errors: raise SystemExit('final candidate snapshot failed before delivery: ' + '; '.join(errors))
    snap=read_json(ep/final_snapshot.SNAPSHOT_REL)
    lock=snap.get('lock') or {}
    files=[]
    for item in lock.get('delivery_files') or []:
        if not isinstance(item,dict): continue
        p=resolve_repo(item.get('path'),'snapshot.delivery_file')
        current=row(p,str(item.get('role') or 'snapshot_file'),str(item.get('archive_path') or ('evidence/'+p.name)))
        if current['sha256'].lower()!=str(item.get('sha256') or '').lower():
            raise SystemExit(f"snapshot delivery SHA drift: {item.get('path')}")
        files.append(current)
    snapshot_path=ep/final_snapshot.SNAPSHOT_REL
    files.append(row(snapshot_path,'final_candidate_snapshot','evidence/final-candidate-snapshot.json'))
    manifest=read_json(ep/'meta/release-manifest.json')
    return files,manifest

def gather(ep: Path) -> tuple[list[dict], dict]:
    if final_snapshot.required(ep) or (ep/final_snapshot.SNAPSHOT_REL).is_file():
        return gather_from_snapshot(ep)
    manifest_path=ep/'meta/release-manifest.json'; manifest=read_json(manifest_path)
    release=manifest.get('release') or {}; artifacts=manifest.get('artifacts') or {}
    pub_raw=release.get('publish_dir')
    if not isinstance(pub_raw,str) or not pub_raw.strip(): raise SystemExit('manifest.release.publish_dir missing')
    publish_dir=(ROOT/pub_raw).resolve() if not Path(pub_raw).is_absolute() else Path(pub_raw).resolve()
    if not publish_dir.is_dir(): raise SystemExit('publish directory missing')
    body_glob=str(release.get('body_glob') or '[0-9][0-9].png')
    body=sorted([p for p in publish_dir.glob(body_glob) if p.is_file()],key=lambda p:p.name)
    expected=release.get('body_frame_count')
    if not isinstance(expected,int) or expected<=0: raise SystemExit('manifest.release.body_frame_count invalid')
    if len(body)!=expected: raise SystemExit(f'publish body incomplete: expected={expected}, found={len(body)}')
    files=[]
    for p in body: files.append(row(p,f'body:{p.stem}',f'publish/{p.name}'))
    cover=resolve_repo(release.get('cover_path'),'manifest.release.cover_path'); files.append(row(cover,'cover','cover'+cover.suffix.lower()))
    required=[('captions','captions'),('publish_copy','publish_copy'),('propagation_card','propagation_card')]
    for key,role in required:
        p=resolve_repo(artifacts.get(key),f'manifest.artifacts.{key}')
        files.append(row(p,role,f'text/{p.name}'))
    production_review=artifacts.get('production_review')
    if production_review:
        p=resolve_repo(production_review,'manifest.artifacts.production_review'); files.append(row(p,'production_review',f'qa/{p.name}'))
    text_audit=ep/'meta/text-audit.json'
    if not text_audit.is_file(): raise SystemExit('meta/text-audit.json missing')
    audit=read_json(text_audit)
    if ((audit.get('summary') or {}).get('passed')) is not True: raise SystemExit('text audit is not PASS')
    files.append(row(text_audit,'text_audit','qa/text-audit.json'))
    files.append(row(manifest_path,'release_manifest','release-manifest.json'))
    checkpoint=ep/'meta/runtime-checkpoint.json'
    if checkpoint.is_file(): files.append(row(checkpoint,'runtime_checkpoint','evidence/runtime-checkpoint.json'))
    ledger=ep/'meta/production-ledger.json'
    if ledger.is_file(): files.append(row(ledger,'production_ledger','evidence/production-ledger.json'))
    for rel_path, role, arc in [
        ('meta/episode-state.json','episode_state','evidence/episode-state.json'),
        ('meta/story-gates.json','story_gates','evidence/story-gates.json'),
        ('meta/story-semantic-review.json','story_semantic_review','qa/story-semantic-review.json'),
        ('meta/visual-profile-review.json','visual_profile_review','qa/visual-profile-review.json'),
        ('meta/subtitle-layout-audit.json','subtitle_layout_audit','qa/subtitle-layout-audit.json'),
        ('meta/frame-semantic-review.json','frame_semantic_review','qa/frame-semantic-review.json'),
        ('meta/frame-semantic-audit.json','frame_semantic_audit','qa/frame-semantic-audit.json'),
    ]:
        p=ep/rel_path
        if p.is_file(): files.append(row(p,role,arc))
        elif frame_semantic_required(ep) and rel_path in {'meta/frame-semantic-review.json','meta/frame-semantic-audit.json'}:
            raise SystemExit(f'required semantic evidence missing: {rel_path}')
    review_dir=ep/'meta/frame-reviews'
    if frame_semantic_required(ep):
        reviews=sorted(review_dir.glob('[0-9][0-9].json')) if review_dir.is_dir() else []
        expected=((manifest.get('release') or {}).get('body_frame_count'))
        if not isinstance(expected,int) or len(reviews)!=expected:
            raise SystemExit(f'frame semantic review count mismatch: expected={expected}, found={len(reviews)}')
        for p in reviews: files.append(row(p,f'frame_review:{p.stem}',f'qa/frame-reviews/{p.name}'))
    return files,manifest

def build(ep: Path,label: str) -> Path:
    preflight(ep)
    files,manifest=gather(ep)
    out_dir=ep/'deliveries'; out_dir.mkdir(parents=True,exist_ok=True)
    out=out_dir/f'{ep.name}_{label}.zip'
    temp=out.with_suffix('.zip.partial')
    report={
        'schema_version':3,'story_os_version':episode_contract_version(ep),'approval_basis':'delegated_auto_review','direct_release_lock':False,
        'built_at':dt.datetime.now().astimezone().isoformat(),'episode':manifest.get('episode') or {},'files':files,'package':None,
    }
    checks=''.join(f"{x['sha256']}  {x['archive_path']}\n" for x in files)
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for x in files:
            p=resolve_repo(x['path'],'delivery.file'); zf.write(p,x['archive_path'])
        zf.writestr('checksums.sha256',checks)
        zf.writestr('DELEGATED_AUTO_REPORT.json',json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    temp.replace(out)
    report['package']={'path':repo_rel(out),'sha256':sha256_file(out),'bytes':out.stat().st_size}
    write_json(ep/REPORT_REL,report)
    return out

def verify(ep: Path) -> list[str]:
    rp=ep/REPORT_REL
    if not rp.is_file(): return ['delegated release report missing']
    d=read_json(rp); errors=[]; package=d.get('package') or {}
    if d.get('story_os_version') != episode_contract_version(ep): errors.append('delegated report story_os_version mismatch')
    try: zp=resolve_repo(package.get('path'),'delegated.package')
    except SystemExit as exc:return [str(exc)]
    if sha256_file(zp).lower()!=str(package.get('sha256') or '').lower(): errors.append('delegated ZIP SHA drift')
    try:
        with zipfile.ZipFile(zp,'r') as zf:
            if zf.testzip() is not None: errors.append('delegated ZIP corrupt')
            names=set(zf.namelist())
            for x in d.get('files') or []:
                arc=x.get('archive_path')
                if arc not in names: errors.append(f'ZIP missing {arc}'); continue
                if hashlib.sha256(zf.read(arc)).hexdigest().lower()!=str(x.get('sha256') or '').lower(): errors.append(f'ZIP file hash drift {arc}')
            if 'checksums.sha256' not in names or 'DELEGATED_AUTO_REPORT.json' not in names: errors.append('ZIP metadata missing')
    except (zipfile.BadZipFile,OSError) as exc: errors.append(str(exc))
    for x in d.get('files') or []:
        try:p=resolve_repo(x.get('path'),'delegated.file')
        except SystemExit as exc:errors.append(str(exc));continue
        if sha256_file(p).lower()!=str(x.get('sha256') or '').lower(): errors.append(f'source SHA drift {x.get("path")}')
    return errors

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('build'); p.add_argument('episode_dir'); p.add_argument('--label',default='DELEGATED_AUTO')
    p=sub.add_parser('verify'); p.add_argument('episode_dir')
    p=sub.add_parser('show'); p.add_argument('episode_dir')
    args=ap.parse_args(); ep=Path(args.episode_dir).resolve()
    if args.cmd=='build':
        out=build(ep,args.label); print(out); print('SHA256',sha256_file(out)); return 0
    if args.cmd=='show': print((ep/REPORT_REL).read_text(encoding='utf-8')); return 0
    errors=verify(ep)
    if errors:
        for e in errors: print('FAIL:',e)
        return 2
    print('DELEGATED DELIVERY VERIFY PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
