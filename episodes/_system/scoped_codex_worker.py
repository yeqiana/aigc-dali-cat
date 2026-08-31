#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
import execution_capsule
import character_contract
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

STEP_DIRECTIVES={
"CREATIVE_STORY":"""
TARGET: reach STORYBOARD_LOCKED and stop there.
- honor meta/runtime-request.json when present.
- BEFORE concept/story work, read meta/character-contract.json as the Character/Entry/Scene Story Build Input Contract.
- default protagonists are ordinary young people from the 2004-2010 or modern-2020s pools; first-person POV still requires a stable character anchor.
- default 4-5 person groups must keep stable member IDs, ages, genders and clothing anchors.
- prefer life-like entry motives: travel, return home, friends hangout, games/drinking, challenge, abandoned place, outdoor trip, casual work, research/expedition, accidental detour.
- NEVER replace the protagonist with a repair worker, electrician, police officer, journalist, investigator, professional ghost hunter or another occupational tool invented to solve the anomaly.
- casual work / research / expedition may explain why the young people arrived, but professional skill must not become the shortcut that solves the anomaly.
- BEFORE STORYBOARD_LOCKED, update meta/character-contract.json to match the final Story, set status=LOCKED, recheck NO-ANOMALY TEST, and run character_contract.py validate --require-locked. Do not advance if it fails.
- auto_create: author the complete story yourself via recent5/account evidence -> 8-12 concepts -> Concept Ambition -> image-first propagation -> Story/Storyboard.
- user_seed: preserve core intent but strengthen/rewrite mechanism, logic, escalation, climax and ending; never mechanically split the seed.
- core_constraints: preserve every hard constraint.
- locked_story: only logic/polish repairs.
- run Story critics/verifiers and honest delegated approval evidence.
- advance only to STORYBOARD_LOCKED.
DO NOT create Environment/Impact Contract, Visual Lock images, Batch, subtitles or Release.
""",
"VISUAL_LOCK":"""
TARGET: reach VISUAL_CALIBRATED and stop there.
- create/verify Environment + Impact Contract.
- compile/verify Resolved Frame Contracts.
- use exactly four current V2.1 Visual Lock admissions: ordinary_baseline, worst_capture_condition, first_major_anomaly, high_impact_admission.
- generate/review/repair only those admissions as required.
- use image model policy from meta/runtime-request.json; default gpt-image-2.
- record honest delegated visual approval only after evidence passes.
- advance only to VISUAL_CALIBRATED.
DO NOT run full Batch or release.
""",
"PRODUCTION":"""
TARGET: reach PRODUCTION_PASSED and stop there.
- author concise per-frame prompts for remaining frames.
- import/run bounded image scheduler, max 3 image jobs.
- reuse clean SHA-bound PASS evidence.
- technical failures are retryable and do not consume content repair.
- Fast Scout is triage only; run final incremental semantic review/audit.
- repair only failed dirty frames.
- advance only to PRODUCTION_PASSED.
DO NOT do subtitles or Release.
""",
"RELEASE":"""
TARGET: reach PUBLISH_READY and stop there.
- create/audit captions and publish copy/assets from PASS production frames.
- complete release/compliance checks.
- build+verify Final Candidate Snapshot.
- record honest delegated release approval.
- transition only to PUBLISH_READY.
- ZIP is a delivery adapter, not CODEX completion.
DO NOT mark PUBLISHED or fabricate metrics.
"""}

def resolve_codex(raw):
    value=raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value: raise RuntimeError("Codex CLI not found on PATH")
    p=Path(value).expanduser().resolve()
    if not p.exists(): raise RuntimeError(f"Codex CLI not found: {p}")
    return p

def prefix(codex):
    if codex.suffix.lower()==".py": return [sys.executable,str(codex)]
    if os.name=="nt" and codex.suffix.lower() in {".cmd",".bat"}: return ["cmd.exe","/d","/c",str(codex)]
    return [str(codex)]

def request_block(ep):
    p=ep/"meta/runtime-request.json"
    if not p.is_file(): return "<runtime_request>ABSENT</runtime_request>"
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    return "<runtime_request>\n"+json.dumps(data,ensure_ascii=False,indent=2)+"\n</runtime_request>"

def prompt(ep,step):
    rel=ep.relative_to(ROOT).as_posix()
    if step=="CREATIVE_STORY":
        character_contract.prepare(ep,force=False)
    capsule=execution_capsule.compile_capsule(ep,step,write=True)
    return f"""You are a bounded Story OS V2.1 scoped worker for exactly {rel}.
Use the derived Execution Capsule first; do NOT reread the entire repository policy stack by default.
Open authoritative source files listed by the capsule only when details are missing or a conflict must be resolved.
Do not spawn another full-auto supervisor. Do not perform downstream work beyond this step.
Reuse valid SHA-bound evidence. Never fabricate PASS/review/user approval.
Reality constrains capture behavior, not concept ambition.

<EXECUTION_CAPSULE>
{json.dumps(capsule,ensure_ascii=False,indent=2)}
</EXECUTION_CAPSULE>

{request_block(ep)}

<SCOPED_STEP id="{step}">
{STEP_DIRECTIVES[step].strip()}
</SCOPED_STEP>

Stop when the bounded target is reached. The parent runtime independently verifies all gates.
"""

def run_step(ep,step,codex_raw=None,timeout=3600):
    if step not in STEP_DIRECTIVES: raise ValueError(f"unknown scoped step: {step}")
    codex=resolve_codex(codex_raw)
    log=ep/"meta/scoped-workers"/f"{step.lower()}.jsonl"; log.parent.mkdir(parents=True,exist_ok=True)
    cmd=prefix(codex)+["exec","--skip-git-repo-check","--ephemeral","-s","workspace-write","-C",str(ROOT),"--json","-"]
    with log.open("a",encoding="utf-8",newline="\n") as h:
        try:
            cp=subprocess.run(cmd,input=prompt(ep,step),text=True,stdout=h,stderr=subprocess.STDOUT,timeout=timeout,check=False)
            return cp.returncode,str(log)
        except subprocess.TimeoutExpired:
            return 124,str(log)

def self_test():
    assert set(STEP_DIRECTIVES)=={"CREATIVE_STORY","VISUAL_LOCK","PRODUCTION","RELEASE"}
    print("SCOPED CODEX WORKER SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("run"); p.add_argument("episode_dir"); p.add_argument("step",choices=sorted(STEP_DIRECTIVES)); p.add_argument("--codex"); p.add_argument("--timeout",type=int,default=3600)
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve(); rc,log=run_step(ep,a.step,codex_raw=a.codex,timeout=a.timeout)
    print(json.dumps({"step":a.step,"returncode":rc,"log":log},ensure_ascii=False)); return rc

if __name__=="__main__": raise SystemExit(main())
