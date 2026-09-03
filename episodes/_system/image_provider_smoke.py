#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

import image_provider_runtime
import openai_images_provider

def main() -> int:
    ap=argparse.ArgumentParser(description="Story OS V2.4.1 Image Provider smoke utility")
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("capability")
    p=sub.add_parser("native-n")
    p.add_argument("--prompt",required=True)
    p.add_argument("--count",type=int,default=5)
    p.add_argument("--out-dir",required=True,type=Path)
    p.add_argument("--width",type=int,default=1080)
    p.add_argument("--height",type=int,default=1350)
    p.add_argument("--quality",choices=["low","medium","high"],default="high")
    p.add_argument("--model",default="gpt-image-2")
    p.add_argument("--timeout",type=int,default=900)
    a=ap.parse_args()
    if a.cmd=="capability":
        print(json.dumps(image_provider_runtime.capability_snapshot(),ensure_ascii=False,indent=2))
        return 0
    if not 1<=a.count<=10:
        raise SystemExit("--count must be 1..10")
    a.out_dir.mkdir(parents=True,exist_ok=True)
    paths=[a.out_dir/f"out-{i:02d}.png" for i in range(1,a.count+1)]
    result=openai_images_provider.generate_native_batch(
        prompt=a.prompt,references=[],count=a.count,model=a.model,quality=a.quality,
        release_width=a.width,release_height=a.height,timeout=a.timeout,raw_paths=paths)
    safe={k:v for k,v in result.items() if k!="artifacts"}
    safe["artifacts"]=result["artifacts"]
    print(json.dumps(safe,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
