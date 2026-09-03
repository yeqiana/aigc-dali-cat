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
import storyos_config

_CONFIG=storyos_config.load_config()
DEFAULT_MODEL=str(storyos_config.get_path(_CONFIG,"image.model"))
DEFAULT_QUALITY=str(storyos_config.get_path(_CONFIG,"image.quality"))
REPRODUCIBLE_SNAPSHOT="gpt-image-2-2026-04-21"
MODEL_UNAVAILABLE="MODEL_UNAVAILABLE"
MODEL_UNAVAILABLE_PATTERNS=("model_unavailable","model unavailable","model is not available","requested model is not available","unknown model","unsupported model","model not found","does not exist","cannot honor the requested model")

def classify_backend_error(text):
    low=str(text or "").lower()
    if any(x in low for x in MODEL_UNAVAILABLE_PATTERNS): return MODEL_UNAVAILABLE
    return None

def resolve_model(*,request=None,explicit=None,explicit_quality=None,reproducible=False):
    quality=str(explicit_quality or (request or {}).get("image_quality") or ((request or {}).get("image") or {}).get("quality") or DEFAULT_QUALITY).strip().lower()
    if quality != DEFAULT_QUALITY:
        raise ValueError(f"formal image quality must be {DEFAULT_QUALITY!r}; got {quality!r}")
    if explicit:
        return {"provider":"openai","model":explicit,"quality":quality,"source":"user_explicit","strict_model":True,"reproducible_snapshot":explicit==REPRODUCIBLE_SNAPSHOT}
    if request:
        image=request.get("image") or {}; model=str(request.get("image_model") or image.get("model") or "").strip()
        if model:
            return {"provider":str(image.get("provider") or "openai"),"model":model,"quality":quality,"source":str(image.get("source") or "runtime_request"),"strict_model":bool(image.get("strict_model")),"reproducible_snapshot":model==REPRODUCIBLE_SNAPSHOT}
    model=REPRODUCIBLE_SNAPSHOT if reproducible else DEFAULT_MODEL
    return {"provider":"openai","model":model,"quality":quality,"source":"system_default_reproducible" if reproducible else "system_default","strict_model":False,"reproducible_snapshot":reproducible}

def for_episode(ep,*,explicit=None,explicit_quality=None,reproducible=False):
    return resolve_model(request=runtime_request.effective_for_episode(ep.resolve()),explicit=explicit,explicit_quality=explicit_quality,reproducible=reproducible)

def self_test():
    assert resolve_model()["model"]=="gpt-image-2"
    assert resolve_model()["quality"]=="high"
    assert resolve_model(reproducible=True)["model"]=="gpt-image-2-2026-04-21"
    assert resolve_model(explicit="gpt-image-2")["strict_model"] is True
    assert classify_backend_error("unknown model")=="MODEL_UNAVAILABLE"
    print("IMAGE MODEL POLICY V2.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("resolve");p.add_argument("--episode-dir",type=Path);p.add_argument("--image-model");p.add_argument("--image-quality",choices=["high"]);p.add_argument("--reproducible",action="store_true")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    data=for_episode(a.episode_dir,explicit=a.image_model,explicit_quality=a.image_quality,reproducible=a.reproducible) if a.episode_dir else resolve_model(explicit=a.image_model,explicit_quality=a.image_quality,reproducible=a.reproducible)
    print(json.dumps(data,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
