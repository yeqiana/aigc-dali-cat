#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch a repository-native Codex worker to continue Story OS end-to-end."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = Path('meta/runtime-checkpoint.json')

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def resolve_episode(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit('episode must be inside repository')
    return ep

def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    if not value:
        raise SystemExit('Codex CLI not found. Install/login Codex, then retry.')
    return Path(value).resolve()

def command_prefix(codex: Path) -> list[str]:
    if os.name == 'nt' and codex.suffix.lower() in {'.cmd', '.bat'}:
        return ['cmd.exe', '/d', '/c', str(codex)]
    return [str(codex)]

def update_checkpoint(ep: Path, *, state: str, next_action: str, error: str | None = None) -> None:
    path = ep / CHECKPOINT
    data = read_json(path) if path.exists() else {
        'schema_version': 1,
        'story_os_version': '2.0.1',
        'runtime': 'CODEX',
        'locked_frames': [],
        'failed_frames': [],
    }
    data.update({
        'story_os_version': '2.0.1',
        'runtime': 'CODEX',
        'continuous_execution_authorized': True,
        'approval_basis': 'delegated_continuous_execution',
        'last_completed': state,
        'next_action': next_action,
        'updated_at': now(),
    })
    if error:
        data['last_error'] = error
    write_json(path, data)

def worker_instruction(ep: Path, resume: bool) -> str:
    rel = ep.relative_to(ROOT).as_posix()
    mode = 'resume from the existing checkpoint first' if resume else 'start from the real current repository state'
    return f"""You are the Story OS V2.0.1 autonomous CODEX runtime worker for exactly this episode: {rel}.

The user already authorized continuous full-auto execution. {mode}. Do not ask “continue?” at normal Golden Path gates. Read START_HERE.md, SKILL.md, AGENTS.md, runtimes/CODEX.md, standards/AUTHORITY_INDEX.json, the target episode, episode-state, gates, production ledger, reviews and runtime checkpoint.

Hard rules:
1. Do NOT call story_os.py run, codex_auto_orchestrator.py run, or spawn another full-auto supervisor. You are already the supervisor worker.
2. Preserve the seven-stage episode-state as the only stage source. runtime-checkpoint is recovery evidence only.
3. delegated_auto_review is not direct_user_review. Never fabricate --user-approved Story/Visual/Release approval when direct approval evidence does not exist.
4. You MAY continue production under continuous execution authorization, self-review images, and authorize the one permitted repair using production_ledger.py authorize-repair --delegated-auto.
5. For new or repaired images use episodes/_system/codex_subscription_image.py generate so every candidate becomes a real file. Keep originals/repairs/approved/publish separate and record SHA with existing tools.
6. Do the three authenticity calibration frames before broad batch work and the four visual-admission frames before the remainder unless already completed and locked.
7. Reuse every locked asset whose SHA still matches. Never regenerate an approved unrelated frame for convenience.
8. Technical failures do not consume content repair. One content repair max. A second content failure becomes NEEDS_USER and stops final-release claims.
9. Use evidence_gate.py as the stable evidence gate name.
10. Finish as far as current tools honestly allow: captions/text audit, publish assets, Final Checklist, SHA verification, and a clearly labeled delegated-auto delivery ZIP when actual files can be collected. Do not claim PUBLISH_READY if direct Release Lock evidence is absent.
11. Continuously update {rel}/meta/runtime-checkpoint.json with last_completed, next_action, locked_frames and failed_frames.
"""

def run_worker(args: argparse.Namespace, resume: bool) -> int:
    ep = resolve_episode(args.episode_dir)
    codex = resolve_codex(args.codex)
    log = ep / 'meta' / 'codex-auto-run.jsonl'
    log.parent.mkdir(parents=True, exist_ok=True)
    update_checkpoint(ep, state='ORCHESTRATOR_STARTED', next_action='CODEX_WORKER_RUNNING')
    cmd = command_prefix(codex) + [
        'exec', '--skip-git-repo-check', '--ephemeral', '-s', 'workspace-write',
        '-C', str(ROOT), '--json', '-'
    ]
    started = time.monotonic()
    with log.open('a', encoding='utf-8', newline='\n') as handle:
        try:
            completed = subprocess.run(
                cmd,
                input=worker_instruction(ep, resume),
                text=True,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            update_checkpoint(ep, state='ORCHESTRATOR_BLOCKED', next_action='RESUME_FULL_AUTO', error=f'worker timeout after {args.timeout}s')
            print(f'FULL-AUTO BLOCKED: timeout; resume with story_os.py run "{ep}" --full-auto --resume')
            return 3
    if completed.returncode != 0:
        update_checkpoint(ep, state='ORCHESTRATOR_BLOCKED', next_action='INSPECT_CODEX_LOG_AND_RESUME', error=f'codex rc={completed.returncode}; log={log}')
        print(f'FULL-AUTO BLOCKED rc={completed.returncode}; log={log}')
        return 3
    update_checkpoint(ep, state='ORCHESTRATOR_WORKER_RETURNED', next_action='VERIFY_CHECKPOINT_AND_DELIVERY')
    print(f'FULL-AUTO WORKER RETURNED in {round(time.monotonic()-started,1)}s; log={log}')
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('run', 'resume'):
        p = sub.add_parser(name)
        p.add_argument('episode_dir')
        p.add_argument('--full-auto', action='store_true')
        p.add_argument('--codex')
        p.add_argument('--timeout', type=int, default=7200)
    p = sub.add_parser('status'); p.add_argument('episode_dir')
    sub.add_parser('self-test')
    args = ap.parse_args()
    if args.cmd == 'self-test':
        assert CHECKPOINT.as_posix() == 'meta/runtime-checkpoint.json'
        print('CODEX AUTO ORCHESTRATOR SELF-TEST PASS')
        return 0
    if args.cmd == 'status':
        ep = resolve_episode(args.episode_dir)
        path = ep / CHECKPOINT
        print(path.read_text(encoding='utf-8') if path.exists() else 'NO CHECKPOINT')
        return 0
    if not args.full_auto:
        raise SystemExit('run/resume requires explicit --full-auto')
    return run_worker(args, resume=args.cmd == 'resume')

if __name__ == '__main__':
    raise SystemExit(main())
