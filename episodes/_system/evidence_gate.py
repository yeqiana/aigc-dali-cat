#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stable Story OS evidence gate supporting direct-user or delegated-auto approval provenance."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from approval_lock import verify_lock
from delegated_approval import verify as verify_delegated
from release_package import verify_payload
from visual_profile import resolve_profile
from story_os_contract import canonical_stages
from story_review import review_required as story_review_required, verify as verify_story_review
from visual_review import review_required as visual_review_required, verify as verify_visual_review
from subtitle_layout import layout_required as subtitle_layout_required, verify_audit as verify_layout_audit

ROOT=Path(__file__).resolve().parents[2]
STATES=canonical_stages()

def load_json(p: Path) -> dict:
    d=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(d,dict):raise ValueError(f'JSON root must be object: {p}')
    return d

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def version_at_least(raw,minimum=(1,8)):
    try:
        parts=str(raw or '').split('.');cur=(int(parts[0]),int(parts[1]) if len(parts)>1 else 0);return cur>=minimum
    except Exception:return False
def is_enforced(state,manifest):return version_at_least(state.get('tool_version')) or version_at_least(manifest.get('tool_version'))
def resolve_repo_file(raw):
    if not isinstance(raw,str) or not raw.strip():return None
    rel=Path(raw.strip());p=(ROOT/rel).resolve() if not rel.is_absolute() else rel.resolve()
    try:p.relative_to(ROOT.resolve())
    except ValueError:return None
    return p if p.is_file() else None
def check_text_audit(ep,manifest):
    errors=[];p=ep/'meta/text-audit.json'
    if not p.is_file():return ['PUBLISH_READY requires meta/text-audit.json']
    try:r=load_json(p)
    except Exception as exc:return [f'invalid text-audit.json: {exc}']
    if ((r.get('summary') or {}).get('passed')) is not True:errors.append('text audit summary.passed must be true')
    source=str(r.get('source_sha256') or '');caps=resolve_repo_file((manifest.get('artifacts') or {}).get('captions'))
    if len(source)!=64:errors.append('text-audit.json missing source_sha256; rerun Story OS audit-text')
    if caps is None:errors.append('manifest.artifacts.captions missing/unreadable')
    elif len(source)==64 and sha256_file(caps).lower()!=source.lower():errors.append('text audit stale: captions SHA256 drift')
    return errors
def any_approval(ep,kind):
    direct=verify_lock(ep,kind)
    if not direct:return True,[],'direct_user_review'
    delegated=verify_delegated(ep,kind)
    if not delegated:return True,[],'delegated_auto_review'
    return False,['direct: '+'; '.join(direct),'delegated: '+'; '.join(delegated)],'none'
def direct_release(ep):
    p=ep/'meta/release-package.json'
    if not p.is_file():return ['release-package.json missing']
    try:payload=load_json(p)
    except Exception as exc:return [f'invalid release-package.json: {exc}']
    e=[]
    if payload.get('user_approved') is not True:e.append('release package is not direct-user approved')
    e.extend(verify_payload(ep,payload));return e
def run_gate(ep,target):
    state=load_json(ep/'meta/episode-state.json');manifest=load_json(ep/'meta/release-manifest.json')
    if not is_enforced(state,manifest):return True,['legacy/pre-V1.8 episode: evidence gate not enforced until metadata is upgraded']
    idx=STATES.index(target);errors=[];info=[]
    if idx>=STATES.index('STORYBOARD_LOCKED'):
        ok,e,b=any_approval(ep,'story_lock');errors.extend(['story_lock: '+x for x in e] if not ok else []);info.extend(['story_lock basis='+b] if ok else [])
        if story_review_required(ep):
            errors.extend(['story_semantic_review: '+x for x in verify_story_review(ep)])
    if idx>=STATES.index('VISUAL_CALIBRATED'):
        try:resolve_profile(ep)
        except SystemExit as exc:errors.append('visual profile: '+str(exc))
        ok,e,b=any_approval(ep,'visual_lock');errors.extend(['visual_lock: '+x for x in e] if not ok else []);info.extend(['visual_lock basis='+b] if ok else [])
        if visual_review_required(ep):
            errors.extend(['visual_profile_review: '+x for x in verify_visual_review(ep)])
    if idx>=STATES.index('PUBLISH_READY'):
        errors.extend(check_text_audit(ep,manifest))
        if subtitle_layout_required(ep):
            errors.extend(['subtitle_layout: '+x for x in verify_layout_audit(ep)])
        direct=direct_release(ep)
        if not direct:info.append('release_lock basis=direct_user_review')
        else:
            delegated=verify_delegated(ep,'release_lock')
            if delegated:errors.append('release_lock direct: '+'; '.join(direct));errors.append('release_lock delegated: '+'; '.join(delegated))
            else:info.append('release_lock basis=delegated_auto_review')
    return not errors,info if not errors else errors
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('episode_dir');ap.add_argument('--target',required=True,choices=STATES);a=ap.parse_args();ep=Path(a.episode_dir).resolve()
    if not ep.is_dir():raise SystemExit(f'episode directory not found: {ep}')
    ok,msg=run_gate(ep,a.target);print(f"EVIDENCE GATE {'PASS' if ok else 'FAIL'} | target={a.target}")
    for m in msg:print(('INFO: ' if ok else 'FAIL: ')+m)
    return 0 if ok else 2
if __name__=='__main__':raise SystemExit(main())
