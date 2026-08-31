#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility CODEX adapter for Story OS V2.1 Workflow Runner.

The parent workflow runner owns orchestration. This adapter preserves the proven V2.0.3.6
creative worker behavior while CODEX completion now stops at PUBLISH_READY + evidence PASS.
ZIP delivery is not a CODEX production gate.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, shutil, subprocess, sys
from pathlib import Path

from story_os_contract import canonical_stages, story_os_version
import episode_performance

ROOT=Path(__file__).resolve().parents[2]; SYSTEM=Path(__file__).resolve().parent; CHECKPOINT=Path('meta/runtime-checkpoint.json')
STORY_OS_VERSION=story_os_version(); STATES=canonical_stages()

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')
def read_json(p): return json.loads(p.read_text(encoding='utf-8-sig'))
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
    p=ep/CHECKPOINT; d=read_json(p) if p.exists() else {'schema_version':2,'locked_frames':[],'failed_frames':[],'step_runs':[]}
    d.update({'story_os_version':STORY_OS_VERSION,'runtime':'CODEX','continuous_execution_authorized':True,'approval_basis':'delegated_continuous_execution','last_completed':state,'next_action':next_action,'updated_at':now()})
    d.setdefault('step_runs',[])
    if error:d['last_error']=error
    else:d.pop('last_error',None)
    if completion:d['completion']=completion
    write_json(p,d)
    episode_performance.observe_checkpoint(ep,state)
def runtime_request_block(ep, request_path=None):
    path = Path(request_path).resolve() if request_path else (ep / "meta/runtime-request.json")
    if not path.is_file(): return ""
    data = read_json(path)
    story = data.get("story_input") or {}
    image = data.get("image") or {}
    mode = story.get("mode")
    directives = {
        "auto_create": "No plot was supplied. You MUST author the complete story yourself: diverge concepts first, pass Concept Ambition, then Story Build. Do not ask the user for a plot.",
        "user_seed": "The user supplied a rough story seed. Preserve core intent but strengthen and rewrite mechanism, logic, escalation, climax and ending. Never mechanically split the raw seed into frames.",
        "core_constraints": "The user supplied hard story constraints. Preserve every constraint, but optimize the remaining structure and escalation.",
        "locked_story": "The user explicitly locked the story. Only logic/polish repairs are allowed; do not structurally rewrite it.",
    }
    return "\n<RUNTIME_REQUEST>\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n</RUNTIME_REQUEST>\nRUNTIME REQUEST DIRECTIVE: " + directives.get(mode, "") + f"\nIMAGE MODEL CONTRACT: requested={image.get('model') or 'gpt-image-2'} source={image.get('source')} strict={bool(image.get('strict_model'))}. Never silently substitute an explicitly requested image model.\n"

def worker_instruction(ep,resume,request_path=None):
    rel=ep.relative_to(ROOT).as_posix(); mode='resume from checkpoint' if resume else 'start from real current repository state'
    request_block = runtime_request_block(ep, request_path)
    return f"""You are the Story OS V{STORY_OS_VERSION} autonomous CODEX writer/producer for exactly {rel}. The user authorized continuous full-auto execution; {mode}.
{request_block}
Read START_HERE.md, SKILL.md, AGENTS.md, runtimes/CODEX.md, AUTHORITY_INDEX, standards/创作执行强制规范_V2.0.3.2.md, standards/生产帧语义强制规范_V1.0.md, episode state/gates/ledger/reviews/checkpoint.
Do not spawn another full-auto supervisor.

MINIMAL CLOSURE FIRST:
Run `python episodes/_system/incremental_closure.py plan \"{rel}\" --json` before spending a critic call. CLEAN SHA-bound evidence MUST be reused. Do not rerun Story/Visual/Frame critics merely for reassurance. If the planner reports MISSING_EVIDENCE, repair the missing evidence honestly; never treat it as CLEAN.

RELEASE GUARD V2.0.3.6:
Before Story Lock, run:
  python episodes/_system/release_preflight.py enable \"{rel}\"
  python episodes/_system/release_preflight.py build-recent5 \"{rel}\"
Never replace this with story.recent5_checked=true.
If this is a continuous multi-episode series, create/bind the shared series lock before Visual Lock.
Before returning from RELEASE work, initialize compliance and run the final release critic:
  python episodes/_system/release_preflight.py init-compliance \"{rel}\"
  python episodes/_system/release_preflight.py run-release-critic \"{rel}\"
  python episodes/_system/release_preflight.py verify \"{rel}\"

PHASE 10 ACCOUNT LEARNING INPUT:
Before V2.1 concept divergence, run:
  python episodes/_system/account_learning_index.py rebuild --limit 5
If reports/account-learning-index.json has sample_size > 0, read it as account-relative evidence. Use it to understand which mechanisms/hooks produced observable engagement, but DO NOT mechanically repeat winners, DO NOT treat one weak post as proof that high-ambition concepts are bad, and DO NOT override Concept Ambition with metrics.

PHASE 2 CONCEPT AMBITION GATE:
For V2.1+ episodes only, BEFORE writing the final Story/Storyboard:
- Read recent account mechanism context, but do not shrink every idea into a light anomaly.
- Create meta/concept-candidates.json with 8-12 genuinely different concepts.
- Do NOT reject an idea merely because its ruin, dream-space, anomaly scale, case phenomenon, creature, geography or world rule cannot exist in reality.
- Every candidate must define one_line_hook, anomaly_ceiling initial/middle/climax, Cover/Mid/Climax viral frames and discussion_question.
- At least three candidates must push beyond the normal safe zone.
- Run `python episodes/_system/concept_ambition.py run-critic \"{rel}\" --attempt 1`.
- If FAIL, strengthen/replace weak candidates ONCE, then attempt 2. If still FAIL, stop.
- Verify with `python episodes/_system/concept_ambition.py verify \"{rel}\"`.
- Build Story/Storyboard ONLY from the selected_id that passed Concept Voltage >=80 and all wordless tests.
Legacy 2.0.x episodes do not backfill this evidence.

STORY LOCK IS THE HIGHEST CREATIVE LOCK.
Before story_lock, finish the whole story and storyboard but do NOT generate images.
Run an independent fresh critic:
  python episodes/_system/story_review.py run-critic \"{rel}\" --attempt 1
If it FAILS, revise story + affected storyboard exactly once, then run attempt 2. If attempt 2 still fails, stop. Never self-author review JSON.
Only after `story_review.py verify` passes may you record delegated story_lock.

PHASE 3 ENVIRONMENT / IMPACT CONTRACT:
For V2.1+ episodes, AFTER Story Lock and BEFORE Visual Lock:
- Populate story-gates.visual.environment_contract with baseline + segments + frame_overrides. Weather is physics, not a blanket filter.
- Populate story-gates.visual.frame_directives for EVERY frame: narrative_role, frame_mode, impact_level 0..4, required_visual_cues, scale_reference, escalation_from.
- anomaly_amplified / climax_impact require impact 3..4, a concrete real-world scale reference, and an earlier escalation_from frame.
- Run `python episodes/_system/environment_contract.py verify \"{rel}\"`; do not continue on FAIL.
- Before EACH formal generation/repair, run `python episodes/_system/environment_contract.py resolve-frame \"{rel}\" --frame NN --json` and carry that resolved environment + directive into the frame prompt.
- Do not add heat haze, rain-on-lens, fog, wet reflections, snow residue or similar effects unless the resolved physical conditions support them.
- Reality constrains HOW the anomaly is captured, not how large or impossible the anomaly may be.


PHASE 4 RESOLVED FRAME CONTRACT:
For V2.1+ episodes, AFTER Phase 3 Environment/Impact PASS and BEFORE generating Visual Lock calibration frames:
- Run `python episodes/_system/frame_contract.py compile-all \"{rel}\"`.
- Run `python episodes/_system/frame_contract.py verify \"{rel}\"`; do not continue on FAIL.
- Treat `meta/runtime/contracts/frames/NN.json` as derived caches only. Never edit them to change the story.
- Every formal generation/repair must use the current resolved Frame Contract. `codex_subscription_image.py generate-for-frame` injects it automatically.
- Production Ledger must record `request.frame_contract.contract_sha256`.
- If Story / localized Storyboard beat / Visual / Authenticity / Continuity / Environment / Impact / applicable Reference changes, recompile before generation.
- Do not let an old generation attempt with a stale frame-contract SHA pass as current production evidence.
- After Visual Lock PASS, run `python episodes/_system/frame_contract.py verify \"{rel}\"` again before Batch. If it is stale, do not patch the cache by hand: recompile and regenerate/review any calibration frame whose generation contract no longer matches.
VISUAL LOCK:
For the current V2.1 Phase5 flow, activate the four-admission policy:
0. Run `python episodes/_system/fast_frame_scout.py enable "{rel}"`. This activates Phase7 triage without changing final review authority.
1. Run `python episodes/_system/visual_lock_v21.py prepare "{rel}"`. This chooses four DISTINCT real episode frames and writes `meta/visual-lock-plan.json`: ordinary_baseline first, then worst_capture_condition / first_major_anomaly / high_impact_admission.
2. Create concise scene prompt files at `{rel}/prompts/production/NN.txt` for those frames. Do not duplicate the full rules into scene prompts; Resolved Frame Contract carries the locked context.
3. Initialize/import the scheduler:
   python episodes/_system/image_scheduler.py init "{rel}"
   python episodes/_system/image_scheduler.py import-visual-lock "{rel}" --prompt-dir "{rel}/prompts/production"
4. Run `python episodes/_system/image_scheduler.py run "{rel}" --max-workers 3`. The baseline dependency makes baseline run first; after it succeeds, the other three admissions may run concurrently. If the scheduler returns PARTIAL because of TECH_FAILED, it has already continued all unrelated work. Use `retry-tech` and rerun after inspecting the technical reason; do not consume content repair.
5. Run `python episodes/_system/visual_lock_v21.py bind-from-queue "{rel}"`.
6. Run `python episodes/_system/visual_review.py run-critic "{rel}" --attempt 1`; for Phase5 episodes this dispatches to the four-image unified Visual Lock Critic.
7. If attempt 1 FAILS, read the actual failed calibration rows. The Visual Lock tool records those ready candidates as CONTENT_FAILED in the production ledger when possible. Authorize ONLY the failed frames with `production_ledger.py authorize-repair --delegated-auto`, create concise repair prompts, enqueue them with `image_scheduler.py add --kind repair --scope repair`, run the scheduler, bind-from-queue again, then run critic attempt 2. If attempt 2 still fails, stop.
8. Only after `visual_review.py verify` PASS may you record delegated visual_lock.
9. Run `frame_contract.py verify "{rel}"` again before Batch. Do not hand-edit derived contract caches.

The high-impact admission exists specifically to prevent over-restraint: large/cosmic/impossible anomaly scale is allowed. It must visibly deliver the locked impact/scale reference while keeping plausible optics, available light, atmosphere, occlusion, photographer behavior and non-cinematic capture.

PRODUCTION:
Do NOT manually serialize all formal `codex_subscription_image.py` calls. Phase6 owns expensive image concurrency.
- Keep all per-frame scene prompts concise under the existing ledger prompt budget; Frame Contract carries global/visual/environment context.
- Import remaining original frames:
  python episodes/_system/image_scheduler.py import-batch "{rel}" --prompt-dir "{rel}/prompts/production"
- Inspect `image_scheduler.py plan`, then run:
  python episodes/_system/image_scheduler.py run "{rel}" --max-workers 3
The scheduler uses high-risk/critical-path priority, `escalation_from` dependencies, unique worker outputs/logs, adaptive 3→2→1 throttling, and fail-soft execution. Only image backend work is concurrent; all production-ledger mutations remain serial in the scheduler main thread.
- Scheduler PARTIAL is not Production PASS. If TECH_FAILED exists, unrelated frames have already continued; use `retry-tech` then rerun. Technical failure never consumes content-repair budget.
- After all current approved/candidate frames exist, run:
  python episodes/_system/incremental_frame_review.py review "{rel}" --attempt 1
- If content review FAILS, repair ONLY failed dirty frames. Use the existing single content-repair authorization, write a repair prompt, enqueue with:
  python episodes/_system/image_scheduler.py add "{rel}" --frame NN --kind repair --scope repair --prompt-file <path> ...
  python episodes/_system/image_scheduler.py run "{rel}" --max-workers 3
  Then run frame review attempt 2.
- Before leaving production:
  python episodes/_system/incremental_frame_review.py audit "{rel}"
Phase7 Fast Frame Scout is active inside image_scheduler for high-risk frames. PASS_FAST is triage only; do not skip or replace the final Frame Semantic Critic.

SUBTITLES / RELEASE:
Create canonical caption source and PASS text audit. Render publish captions only with subtitle_layout.py render-all, then audit.
Create publish copy, propagation card and actual publish assets. Do not use approved-base fallback as publish substitute.
Run release_preflight prepare-auto / verify. Then Phase8 MUST freeze the final candidate before release_lock:
  python episodes/_system/final_candidate_snapshot.py enable "{rel}"
  python episodes/_system/final_candidate_snapshot.py build "{rel}"
  python episodes/_system/final_candidate_snapshot.py verify "{rel}"
If Snapshot is STALE, stop and resolve the drift; never hand-edit snapshot SHAs.
Use delegated approval provenance honestly. Never fabricate --user-approved.
Update runtime-checkpoint continuously. Do not build a ZIP in CODEX. Do not claim completion yourself; the parent performs deterministic postflight and stops at PUBLISH_READY + evidence PASS.
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
    if failed:return 'PAUSED',f'failed_frames present: {failed}'
    ledger_path=ep/'meta/production-ledger.json'
    if not ledger_path.is_file(): return 'PAUSED','production ledger missing'
    ledger=read_json(ledger_path); incomplete=[f'{k}:{v.get("status")}' for k,v in (ledger.get('frames') or {}).items() if v.get('status') not in {'PASSED','LOCKED'}]
    if incomplete:return 'PAUSED','production ledger incomplete: '+', '.join(incomplete[:12])
    r=run_cmd([sys.executable,SYSTEM/'production_ledger.py','audit',ep,'--require-passed'])
    if r.returncode!=0:return 'PAUSED','production ledger not fully passed:\n'+r.stdout[-2000:]
    r=run_cmd([sys.executable,SYSTEM/'incremental_frame_review.py','audit',ep])
    if r.returncode!=0:return 'PAUSED','incremental frame semantic review/audit failed:\n'+r.stdout[-2500:]
    r=run_cmd([sys.executable,SYSTEM/'machine_gate.py',ep,'--target','PRODUCTION_PASSED'])
    if r.returncode!=0:return 'PAUSED','PRODUCTION_PASSED machine gate failed:\n'+r.stdout[-2500:]
    r=run_cmd([sys.executable,SYSTEM/'release_preflight.py','prepare-auto',ep])
    if r.returncode!=0:return 'PAUSED','semantic release preflight failed:\n'+r.stdout[-3000:]
    r=run_cmd([sys.executable,SYSTEM/'final_candidate_snapshot.py','enable',ep])
    if r.returncode!=0:return 'PAUSED','cannot enable final candidate snapshot:\n'+r.stdout[-1500:]
    r=run_cmd([sys.executable,SYSTEM/'final_candidate_snapshot.py','build',ep])
    if r.returncode!=0:return 'PAUSED','final candidate snapshot build failed:\n'+r.stdout[-2500:]
    r=run_cmd([sys.executable,SYSTEM/'final_candidate_snapshot.py','verify',ep])
    if r.returncode!=0:return 'PAUSED','final candidate snapshot verify failed:\n'+r.stdout[-2500:]
    # Release Lock must bind final release evidence before state transition.
    r=run_cmd([sys.executable,SYSTEM/'delegated_approval.py','record',ep,'release_lock','--note',f'Deterministic V{STORY_OS_VERSION} CODEX release evidence verified; ZIP delivery not required'])
    if r.returncode!=0:return 'BLOCKED','cannot record delegated release approval: '+r.stdout[-1500:]
    ok,reason=advance_to_publish_ready(ep)
    if not ok:return 'PAUSED','state could not advance to PUBLISH_READY: '+reason
    r=run_cmd([sys.executable,SYSTEM/'evidence_gate.py',ep,'--target','PUBLISH_READY'])
    if r.returncode!=0:return 'BLOCKED','PUBLISH_READY evidence gate failed: '+r.stdout[-2000:]
    return 'COMPLETE','PUBLISH_READY + deterministic evidence PASS; CODEX ZIP not required'
def run_worker(args,resume):
    ep=resolve_episode(args.episode_dir)
    pre=run_cmd([sys.executable,SYSTEM/'incremental_closure.py','plan',ep,'--json'])
    if pre.returncode==0:
        try: minimal=json.loads(pre.stdout)
        except Exception: minimal={}
        if minimal.get('action')=='POSTFLIGHT_ONLY':
            status,reason=postflight(ep)
            if status=='COMPLETE':
                update_checkpoint(ep,'MINIMAL_CLOSURE_COMPLETE','USER_MAY_PUBLISH',completion={'status':'COMPLETE','production_complete_at':'PUBLISH_READY','delivery_package_required':False,'verified_at':now(),'critic_calls_saved':True}); print('MINIMAL CLOSURE COMPLETE: PUBLISH_READY (CODEX ZIP not required)'); return 0
    codex=resolve_codex(args.codex); log=ep/'meta/codex-auto-run.jsonl'; log.parent.mkdir(parents=True,exist_ok=True)
    update_checkpoint(ep,'ORCHESTRATOR_STARTED','CODEX_WORKER_RUNNING')
    cmd=prefix(codex)+['exec','--skip-git-repo-check','--ephemeral','-s','workspace-write','-C',str(ROOT),'--json','-']
    with log.open('a',encoding='utf-8',newline='\n') as h:
        try: completed=subprocess.run(cmd,input=worker_instruction(ep,resume,args.runtime_request),text=True,stdout=h,stderr=subprocess.STDOUT,timeout=args.timeout,check=False)
        except subprocess.TimeoutExpired:
            update_checkpoint(ep,'ORCHESTRATOR_BLOCKED','RESUME_FULL_AUTO','worker timeout'); print('FULL-AUTO BLOCKED: worker timeout'); return 3
    if completed.returncode!=0:
        update_checkpoint(ep,'ORCHESTRATOR_BLOCKED','INSPECT_CODEX_LOG_AND_RESUME',f'codex rc={completed.returncode}; log={log}'); print(f'FULL-AUTO BLOCKED rc={completed.returncode}; log={log}'); return 3
    status,reason=postflight(ep)
    if status=='COMPLETE':
        update_checkpoint(ep,'FULL_AUTO_COMPLETE','USER_MAY_PUBLISH',completion={'status':'COMPLETE','production_complete_at':'PUBLISH_READY','delivery_package_required':False,'verified_at':now()}); print('FULL-AUTO COMPLETE: PUBLISH_READY (CODEX ZIP not required)'); return 0
    if status=='PAUSED':
        update_checkpoint(ep,'FULL_AUTO_PAUSED','RESUME_FULL_AUTO',reason,{'status':'PAUSED'}); print('FULL-AUTO PAUSED:',reason); return 4
    update_checkpoint(ep,'FULL_AUTO_BLOCKED','INSPECT_AND_RESUME',reason,{'status':'BLOCKED'}); print('FULL-AUTO BLOCKED:',reason); return 3
def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    for name in ('run','resume'):
        p=sub.add_parser(name); p.add_argument('episode_dir'); p.add_argument('--full-auto',action='store_true'); p.add_argument('--codex'); p.add_argument('--timeout',type=int,default=7200); p.add_argument('--runtime-request')
    p=sub.add_parser('status'); p.add_argument('episode_dir'); p=sub.add_parser('postflight'); p.add_argument('episode_dir'); sub.add_parser('self-test')
    a=ap.parse_args()
    if a.cmd=='self-test':
        assert STATES[4]=='PUBLISH_READY'; assert CHECKPOINT.as_posix()=='meta/runtime-checkpoint.json'; print('CODEX AUTO ORCHESTRATOR V2.1 ADAPTER SELF-TEST PASS'); return 0
    if a.cmd=='status':
        ep=resolve_episode(a.episode_dir); p=ep/CHECKPOINT; print(p.read_text(encoding='utf-8-sig') if p.exists() else 'NO CHECKPOINT'); return 0
    if a.cmd=='postflight':
        ep=resolve_episode(a.episode_dir); status,reason=postflight(ep); print(status,reason); return 0 if status=='COMPLETE' else 4 if status=='PAUSED' else 3
    if not a.full_auto: raise SystemExit('run/resume requires explicit --full-auto')
    return run_worker(a,a.cmd=='resume')
if __name__=='__main__': raise SystemExit(main())
