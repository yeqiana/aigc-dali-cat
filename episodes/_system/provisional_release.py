#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a provisional release draft while image production is still running.

This file is runtime-only draft evidence. It never mutates release-manifest, snapshot or stage.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
import execution_capsule
import intro_policy

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/provisional-release.json")
def resolve_codex(raw):
    v=raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not v: raise RuntimeError("Codex CLI not found")
    return Path(v).expanduser().resolve()
def prefix(p):
    if p.suffix.lower()==".py": return [sys.executable,str(p)]
    if os.name=="nt" and p.suffix.lower() in {".cmd",".bat"}: return ["cmd.exe","/d","/c",str(p)]
    return [str(p)]
def build(ep,codex_raw=None,timeout=900):
    intro=intro_policy.resolve(ep,write=True)
    capsule=execution_capsule.compile_capsule(ep,"RELEASE",write=True)
    out=ep/REL; out.parent.mkdir(parents=True,exist_ok=True)
    prompt=f"""You are preparing PROVISIONAL text-only release material for a Story OS episode.
This runs before Production PASS to overlap work. Do NOT alter any story, images, release-manifest, final snapshot or episode state.
Use the locked Story/Storyboard and this derived execution capsule:
{json.dumps(capsule,ensure_ascii=False,indent=2)}
Intro opening policy:
{json.dumps(intro,ensure_ascii=False,indent=2)}
The intro family is a structural reference. Rewrite naturally for the actual story. Generate only one internal title candidate.
Read only the Story/Storyboard files you need.
Write UTF-8 JSON to exactly: {out}
Schema:
{{
  "schema_version":1,
  "status":"PROVISIONAL",
  "title_candidates":["..."],
  "intro_candidates":["..."],
  "cover_copy_candidates":["..."],
  "caption_semantic_drafts":[{{"frame":"01","text":"..."}}],
  "topic_candidates":["..."],
  "warnings":["Must be finalized against actual PASS images"]
}}
Do not claim final approval. Stop after this file exists.
"""
    codex=resolve_codex(codex_raw)
    cmd=prefix(codex)+["exec","--skip-git-repo-check","--ephemeral","-s","workspace-write","-C",str(ROOT),"--json","-"]
    log=ep/"meta/scoped-workers/provisional-release.jsonl"; log.parent.mkdir(parents=True,exist_ok=True)
    with log.open("a",encoding="utf-8",newline="\n") as h:
        try: cp=subprocess.run(cmd,input=prompt,text=True,stdout=h,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        except subprocess.TimeoutExpired: return {"ok":False,"returncode":124,"log":str(log)}
    ok=cp.returncode==0 and out.is_file()
    if ok:
        try:
            d=json.loads(out.read_text(encoding="utf-8-sig"))
            ok=isinstance(d,dict) and d.get("status")=="PROVISIONAL"
        except Exception: ok=False
    return {"ok":ok,"returncode":cp.returncode,"path":str(out) if out.is_file() else None,"log":str(log)}
def self_test():
    assert REL.as_posix()=="meta/runtime/provisional-release.json"
    print("PROVISIONAL RELEASE SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("build"); p.add_argument("episode_dir"); p.add_argument("--codex"); p.add_argument("--timeout",type=int,default=900)
    p=sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="show":
        p=ep/REL; print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}"); return 0
    print(json.dumps(build(ep,a.codex,a.timeout),ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
