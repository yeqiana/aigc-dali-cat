#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile stable per-frame generation prompt packages as derived cache."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import frame_contract
import image_model_policy

REL=Path("meta/runtime/prompt-packages")
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def h(data): return hashlib.sha256(data).hexdigest()
def compile_frame(ep,frame,prompt_file,write=True):
    prompt_file=Path(prompt_file).resolve()
    scene=prompt_file.read_text(encoding="utf-8-sig").strip()
    contract=frame_contract.compile_frame(ep,int(frame),write_cache=True)
    model=image_model_policy.for_episode(ep)
    material={
      "schema_version":1,"frame":f"{int(frame):02d}","scene_prompt":scene,
      "scene_prompt_sha256":h(scene.encode("utf-8")),
      "frame_contract_sha256":contract["contract_sha256"],
      "image_model":model,
      "source_prompt":str(prompt_file),
    }
    raw=json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    data={**material,"package_sha256":h(raw),"compiled_at":now()}
    if write:
        p=ep/REL/f"{int(frame):02d}.json"; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    return data
def self_test():
    assert REL.as_posix()=="meta/runtime/prompt-packages"
    print("PROMPT PACKAGE SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("compile"); p.add_argument("episode_dir"); p.add_argument("--frame",type=int,required=True); p.add_argument("--prompt-file",required=True)
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    print(json.dumps(compile_frame(ep,a.frame,a.prompt_file),ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
