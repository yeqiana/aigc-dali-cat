#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS image model policy.

Default production alias: gpt-image-2.
Optional reproducible snapshot: gpt-image-2-2026-04-21.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import runtime_request

DEFAULT_MODEL="gpt-image-2"
REPRODUCIBLE_SNAPSHOT="gpt-image-2-2026-04-21"

def resolve_model(*,request=None,explicit=None,reproducible=False):
    if explicit:
        return {"provider":"openai","model":explicit,"source":"user_explicit","strict_model":True,"reproducible_snapshot":explicit==REPRODUCIBLE_SNAPSHOT}
    if request:
        image=request.get("image") or {}; model=str(image.get("model") or "").strip()
        if model:
            return {"provider":str(image.get("provider") or "openai"),"model":model,"source":str(image.get("source") or "runtime_request"),"strict_model":bool(image.get("strict_model")),"reproducible_snapshot":model==REPRODUCIBLE_SNAPSHOT}
    model=REPRODUCIBLE_SNAPSHOT if reproducible else DEFAULT_MODEL
    return {"provider":"openai","model":model,"source":"system_default_reproducible" if reproducible else "system_default","strict_model":False,"reproducible_snapshot":reproducible}

def for_episode(ep,*,explicit=None,reproducible=False):
    return resolve_model(request=runtime_request.effective_for_episode(ep.resolve()),explicit=explicit,reproducible=reproducible)

def self_test():
    assert resolve_model()["model"]=="gpt-image-2"
    assert resolve_model(reproducible=True)["model"]=="gpt-image-2-2026-04-21"
    assert resolve_model(explicit="gpt-image-2")["strict_model"] is True
    print("IMAGE MODEL POLICY V2.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("resolve");p.add_argument("--episode-dir",type=Path);p.add_argument("--image-model");p.add_argument("--reproducible",action="store_true")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    data=for_episode(a.episode_dir,explicit=a.image_model,reproducible=a.reproducible) if a.episode_dir else resolve_model(explicit=a.image_model,reproducible=a.reproducible)
    print(json.dumps(data,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
