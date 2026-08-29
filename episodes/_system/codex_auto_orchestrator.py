#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the repository-native Codex worker and deterministically close/verify full-auto production."""
from __future__ import annotations
import argparse, datetime as dt, json, os, shutil, subprocess, sys, time
from pathlib import Path

from story_os_contract import canonical_stages, story_os_version

ROOT=Path(__file__).resolve().parents[2]; SYSTEM=Path(__file__).resolve().parent; CHECKPOINT=Path('meta/runtime-checkpoint.json')
STORY_OS_VERSION=story_os_version()
STATES=canonical_stages()

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')
def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def resolve_episode(raw):
    ep=Path(raw).resolve()
    if not ep.is_dir(): raise SystemExit(f'episode directory not found: {ep}')
    try: ep.relative_to(ROOT.resolve())
    except ValueError: raise SystemExit('episode must be inside repository')
    return ep
def resolve_codex(raw):
    value=raw or shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    if not value: raise SystemExit('Codex CLI not found. Install/login Codex, then retry.')
    return Path(value).resolve()
def prefix(codex):
    if codex.suffix.lower()=='.py': return [sys.executable,str(codex)]
    if os.name=='nt' and codex.suffix.lower() in {'.cmd','.bat'}: return ['cmd.exe','/d','/c',str(codex)]
    return [str(codex)]
def update_checkpoint(ep,state,next_action,error=None,completion=None):
    p=ep/CHECKPOINT; d=read_json(p) if p.exists() else {'schema_version':1,'locked_frames':[],'failed_frames':[]}
    d.update({'story_os_version':STORY_OS_VERSION,'runtime':'CODEX','continuous_execution_authorized':True,'approval_basis':'delegated_continuous_execution','last_completed':state,'next_action':next_action,'updated_at':now()})
    if error:d['last_error']=error
    else:d.pop('last_error',None)
    if completion:d['completion']=completion
    write_json(p,d)
def worker_instruction(ep,resume):
    rel=ep.relative_to(ROOT).as_posix(); mode='resume from checkpoint' if resume else 'start from real current repository state'
    return f"""You are the Story OS V{STORY_OS_VERSION} autonomous CODEX writer/producer for exactly {rel}. The user authorized continuous full-auto execution; {mode}.
Read START_HERE.md, SKILL.md, AGENTS.md, runtimes/CODEX.md, AUTHORITY_INDEX, standards/创作执行强制规范_V2.0.3.2.md, standards/生产帧语义强制规范_V1.0.md, episode state/gates/ledger/reviews/checkpoint.
Do not spawn another full-auto supervisor.

STORY LOCK IS THE HIGHEST CREATIVE LOCK.
Before story_lock, finish the whole story and storyboard but do NOT generate images.
Run an independent fresh critic:
  python episodes/_system/story_review.py run-critic "{rel}" --attempt 1
If it FAILS, read meta/story-semantic-review.json, revise story + affected storyboard exactly once, then run a NEW critic:
  python episodes/_system/story_review.py run-critic "{rel}" --attempt 2
If attempt 2 still fails, stop. Never self-author or manually edit the review JSON. Never use propagation score as story proof.
Only after `story_review.py verify` passes may you record delegated story_lock.

VISUAL LOCK:
Resolve the visual profile. If the user did not explicitly override it, M00 is mandatory.
Every formal frame generation via codex_subscription_image.py automatically injects the resolved compact visual contract; never remove or replace it.
Generate exactly the three registered calibration frames first. Review actual images normally, then run an independent fresh visual critic:
  python episodes/_system/visual_review.py run-critic "{rel}" --attempt 1
If it fails, repair/regenerate calibration only within existing one-content-repair limits, then run attempt 2. If still fail, stop.
Only after `visual_review.py verify` passes may you record delegated visual_lock.
A capture_style reference may come only from passed calibration or an explicitly passed capture_style reference; production_ledger enforces this.

PRODUCTION:
For every new/repair image use `codex_subscription_image.py generate-for-frame "{rel}" --frame NN ...`; preserve raw output and exact ledger canvas.
Maintain production ledger. Technical failure does not consume content repair. Do not let an early unapproved generated frame recursively become the style mother reference.
After ALL final approved frames exist, run a FRESH isolated full-frame-set semantic critic:
  python episodes/_system/frame_semantic_review.py run-critic "{rel}" --attempt 1
The critic must judge actual pixels against Story Lock + storyboard + authenticity/continuity anchors, including scene/story-beat fidelity, key prop, character/wardrobe, POV legality, spatial/temporal continuity, anomaly readability, caption-image support and ACTUAL information gain.
If attempt 1 FAILS, repair ONLY the failed frames within the existing one-content-repair-per-frame limit, then run a NEW isolated critic:
  python episodes/_system/frame_semantic_review.py run-critic "{rel}" --attempt 2
If attempt 2 still fails, stop. Never hand-author frame review PASS JSON.
A recovered/locked asset is reusable as PASS only when meta/frame-reviews/NN.json schema 2 is bound to that exact approved asset SHA and current Story/Storyboard/Visual context. "previously reviewed" text alone is not evidence.
Before leaving production run:
  python episodes/_system/frame_semantic_review.py audit "{rel}"

SUBTITLES / RELEASE:
Create the canonical caption source and PASS text audit.
After all approved base images exist, render publish captions ONLY with:
  python episodes/_system/subtitle_layout.py render-all "{rel}"
This renderer deterministically drops a wrapped second line when that line contains punctuation only.
Then run:
  python episodes/_system/subtitle_layout.py audit "{rel}"
Do not substitute another ad-hoc subtitle renderer for V2.0.3.2 episodes.
Create publish copy, propagation card and actual publish assets. Do not use approved-base fallback as a publish substitute.

Use delegated approval provenance honestly after actual independent review. Never fabricate --user-approved.
Update runtime-checkpoint continuously. Do not claim completion yourself; the parent orchestrator performs deterministic postflight and packaging after you return.
"""
def run_cmd(args,cwd=ROOT): return subprocess.run([str(x) for x in args],cwd=cwd,check=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
def advance_to_publish_ready(ep):
    sp=ep/'meta/episode-state.json'
    if not sp.is_file(): return False,'episode-state missing'
    for _ in range(6):
        state=read_json(sp); cur=state.get('current_state')
        if cur=='PUBLISH_READY': return True,''
        if cur not in STATES: return False,'invalid episode state'
        idx=STATES.index(cur)
        if idx>=STATES.index('PUBLISH_READY'): return cur=='PUBLISH_READY','state is beyond/other than PUBLISH_READY'
        target=STATES[idx+1]
        r=run_cmd([sys.executable,SYSTEM/'episode_state.py','transition',ep,target,'--note',f'V{STORY_OS_VERSION} delegated full-auto evidence transition'])
        if r.returncode!=0: return False,r.stdout[-2000:]
    return False,'transition loop exhausted'
def postflight(ep):
    cp=read_json(ep/CHECKPOINT) if (ep/CHECKPOINT).is_file() else {}
    failed=cp.get('failed_frames') or []
    if failed:return 'PAUSED',f'failed_frames present: {failed}',None
    ledger_path=ep/'meta/production-ledger.json'
    if not ledger_path.is_file(): return 'PAUSED','production ledger missing',None
    ledger=read_json(ledger_path); incomplete=[f'{k}:{v.get("status")}' for k,v in (ledger.get('frames') or {}).items() if v.get('status') not in {'PASSED','LOCKED'}]
    if incomplete:return 'PAUSED','production ledger incomplete: '+', '.join(incomplete[:12]),None
    r=run_cmd([sys.executable,SYSTEM/'production_ledger.py','audit',ep,'--require-passed'])
    if r.returncode!=0:return 'PAUSED','production ledger not fully passed:\n'+r.stdout[-2000:],None
    r=run_cmd([sys.executable,SYSTEM/'frame_semantic_review.py','audit',ep])
    if r.returncode!=0:return 'PAUSED','frame semantic review/audit failed:\n'+r.stdout[-2500:],None
    r=run_cmd([sys.executable,SYSTEM/'machine_gate.py',ep,'--target','PRODUCTION_PASSED'])
    if r.returncode!=0:return 'PAUSED','PRODUCTION_PASSED machine gate failed before packaging:\n'+r.stdout[-2500:],None
    try:
        from delegated_delivery import build, verify
        package=build(ep,'DELEGATED_AUTO')
        errors=verify(ep)
        if errors:return 'BLOCKED','delegated delivery verify failed: '+'; '.join(errors),None
    except SystemExit as exc:return 'PAUSED','delegated delivery incomplete: '+str(exc),None
    r=run_cmd([sys.executable,SYSTEM/'delegated_approval.py','record',ep,'release_lock','--note',f'Deterministic V{STORY_OS_VERSION} delegated delivery verified'])
    if r.returncode!=0:return 'BLOCKED','cannot record delegated release approval: '+r.stdout[-1500:],None
    ok,reason=advance_to_publish_ready(ep)
    if not ok:return 'PAUSED','state could not advance to PUBLISH_READY: '+reason,None
    r=run_cmd([sys.executable,SYSTEM/'evidence_gate.py',ep,'--target','PUBLISH_READY'])
    if r.returncode!=0:return 'BLOCKED','PUBLISH_READY evidence gate failed: '+r.stdout[-2000:],None
    return 'COMPLETE','all deterministic postflight checks passed',package
def run_worker(args,resume):
    ep=resolve_episode(args.episode_dir); codex=resolve_codex(args.codex); log=ep/'meta/codex-auto-run.jsonl'; log.parent.mkdir(parents=True,exist_ok=True)
    update_checkpoint(ep,'ORCHESTRATOR_STARTED','CODEX_WORKER_RUNNING')
    cmd=prefix(codex)+['exec','--skip-git-repo-check','--ephemeral','-s','workspace-write','-C',str(ROOT),'--json','-']
    with log.open('a',encoding='utf-8',newline='\n') as h:
        try: completed=subprocess.run(cmd,input=worker_instruction(ep,resume),text=True,stdout=h,stderr=subprocess.STDOUT,timeout=args.timeout,check=False)
        except subprocess.TimeoutExpired:
            update_checkpoint(ep,'ORCHESTRATOR_BLOCKED','RESUME_FULL_AUTO','worker timeout'); print('FULL-AUTO BLOCKED: worker timeout'); return 3
    if completed.returncode!=0:
        update_checkpoint(ep,'ORCHESTRATOR_BLOCKED','INSPECT_CODEX_LOG_AND_RESUME',f'codex rc={completed.returncode}; log={log}'); print(f'FULL-AUTO BLOCKED rc={completed.returncode}; log={log}'); return 3
    status,reason,package=postflight(ep)
    if status=='COMPLETE':
        update_checkpoint(ep,'FULL_AUTO_COMPLETE','USER_MAY_PUBLISH',completion={'status':'COMPLETE','package':str(package),'verified_at':now()}); print(f'FULL-AUTO COMPLETE: {package}'); return 0
    if status=='PAUSED':
        update_checkpoint(ep,'FULL_AUTO_PAUSED','RESUME_FULL_AUTO',reason,{'status':'PAUSED'}); print('FULL-AUTO PAUSED:',reason); return 4
    update_checkpoint(ep,'FULL_AUTO_BLOCKED','INSPECT_AND_RESUME',reason,{'status':'BLOCKED'}); print('FULL-AUTO BLOCKED:',reason); return 3
def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    for name in ('run','resume'):
        p=sub.add_parser(name); p.add_argument('episode_dir'); p.add_argument('--full-auto',action='store_true'); p.add_argument('--codex'); p.add_argument('--timeout',type=int,default=7200)
    p=sub.add_parser('status'); p.add_argument('episode_dir'); p=sub.add_parser('postflight'); p.add_argument('episode_dir'); sub.add_parser('self-test')
    a=ap.parse_args()
    if a.cmd=='self-test':
        assert STATES[4]=='PUBLISH_READY'; assert CHECKPOINT.as_posix()=='meta/runtime-checkpoint.json'; print('CODEX AUTO ORCHESTRATOR SELF-TEST PASS'); return 0
    if a.cmd=='status':
        ep=resolve_episode(a.episode_dir); p=ep/CHECKPOINT; print(p.read_text(encoding='utf-8') if p.exists() else 'NO CHECKPOINT'); return 0
    if a.cmd=='postflight':
        ep=resolve_episode(a.episode_dir); status,reason,package=postflight(ep); print(status,reason,package or ''); return 0 if status=='COMPLETE' else 4 if status=='PAUSED' else 3
    if not a.full_auto: raise SystemExit('run/resume requires explicit --full-auto')
    return run_worker(a,a.cmd=='resume')
if __name__=='__main__': raise SystemExit(main())
