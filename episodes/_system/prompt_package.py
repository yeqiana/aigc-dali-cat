#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile stable per-frame generation prompt packages as derived cache."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import frame_contract
import image_model_policy
import story_json

REL=Path("meta/runtime/prompt-packages")
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def h(data): return hashlib.sha256(data).hexdigest()
def compile_frame(ep,frame,prompt_file,write=True):
    prompt_file=Path(prompt_file).resolve()
    scene=prompt_file.read_text(encoding="utf-8-sig").strip()
    if not scene:
        raise ValueError(f"frame {int(frame):02d} prompt empty")
    contract=frame_contract.compile_frame(ep,int(frame),write_cache=write)
    previous=story_json.read_json(ep/REL/f"{int(frame):02d}.json",default={})
    scene_sha=h(scene.encode("utf-8"))
    if (previous.get("scene_prompt_sha256")==scene_sha
            and previous.get("frame_contract_sha256")
            and previous["frame_contract_sha256"]!=contract["contract_sha256"]):
        raise ValueError("PROMPT_SOURCE_DRIFT: unchanged scene prompt belongs to an older Frame Contract; rebuild scene from current storyboard before generation")
    model=image_model_policy.for_episode(ep)
    material={
      "schema_version":1,"frame":f"{int(frame):02d}","scene_prompt":scene,
      "scene_prompt_sha256":scene_sha,
      "storyboard_source":contract.get("storyboard_frame") or {},
      "frame_contract_sha256":contract["contract_sha256"],
      "frame_prompt_contract":contract.get("prompt_contract", ""),
      "image_model":model,
      "source_prompt":str(prompt_file),
    }
    raw=json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    data={**material,"package_sha256":h(raw),"compiled_at":now()}
    if write:
        story_json.write_json(ep/REL/f"{int(frame):02d}.json",data)
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
