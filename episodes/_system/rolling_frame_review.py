#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rolling actual-pixel pre-final review.

PASS_PREVIEW is never final PASS. REPAIR_NOW may be used to surface an obvious defect early.
UNCERTAIN always defers to the formal final frame review.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
import frame_contract
import runtime_capability_cache  # STORY_OS_V2_5_1_RUNTIME_FAST_PATH
import runtime_router
# STORY_OS_V22_VISUAL_NARRATIVE_CORE

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/rolling-reviews")
VALID={"PASS_PREVIEW","REPAIR_NOW","UNCERTAIN"}

def resolve_codex(raw):
    v=raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not v: raise RuntimeError("Codex CLI not found")
    return Path(v).expanduser().resolve()
def prefix(p):
    if p.suffix.lower()==".py": return [sys.executable,str(p)]
    if os.name=="nt" and p.suffix.lower() in {".cmd",".bat"}: return ["cmd.exe","/d","/c",str(p)]
    return [str(p)]
def review(ep,frame,image,codex_raw=None,timeout=240):
    image=Path(image).resolve()
    # STORY_OS_V2_5_1_RUNTIME_FAST_PATH: a reviewer without verified pixel vision cannot safely trigger a repair.
    caps=runtime_capability_cache.load(ep,create=False)
    if not runtime_capability_cache.vision_verified(caps):
        return {"decision":"UNCERTAIN","reason":"vision_capability_not_verified","fast_path_deferred":True,"final_pass_authority":False,"returncode":0}
    active_runtime,_=runtime_router.detect()
    if active_runtime in {"WORK","WEB"} and not codex_raw:
        return {
            "decision":"UNCERTAIN",
            "reason":"product_runtime_defers_to_final_review_without_local_codex",
            "runtime":active_runtime,
            "final_pass_authority":False,
            "returncode":0,
        }
    contract=frame_contract.compile_frame(ep,int(frame),write_cache=True)
    out=ep/REL/f"{int(frame):02d}-{int(time.time())}.json"; out.parent.mkdir(parents=True,exist_ok=True)
    prompt=f"""Review the attached generated frame as an actual-pixel PRE-FINAL Story OS review.
Frame contract:
{contract["prompt_contract"]}
Only detect obvious semantic/continuity/capture failures that are useful to catch while later images are still generating.
Also catch Visual Narrative Core failures visible in pixels: ghost/impossible camera authorship, staged/result-only moments, lack of new narrative evidence versus the previous beat, repeated shot-template behavior, camera blur/noise/reflection with no physical cause, and impossible phone/map/dashboard/camera-UI physics.
For Story OS >=2.2.1 also catch WORLD_IDENTITY_DRIFT and CHARACTER_APPEARANCE_DRIFT: default episodes must read as Mainland China with Chinese local young adults unless their World Identity Contract explicitly overrides it; character face/age/hair/body/national context must remain consistent with the Character Appearance Anchor.
This review NEVER grants final PASS.
Write JSON to exactly {out}:
{{"frame":"{int(frame):02d}","decision":"PASS_PREVIEW|REPAIR_NOW|UNCERTAIN","reasons":["..."],"confidence":0.0}}
REPAIR_NOW only for clear visible defects. UNCERTAIN if evidence is ambiguous.
"""
    codex=resolve_codex(codex_raw)
    # Codex's image sidecar can fail to resolve Windows paths containing Chinese
    # characters. Stage a byte-identical ASCII-only temporary attachment.
    staging=Path(tempfile.mkdtemp(prefix="story-os-rolling-"))
    staged_image=staging/("frame-"+f"{int(frame):02d}"+image.suffix.lower())
    shutil.copy2(image,staged_image)
    cmd=prefix(codex)+["exec","--skip-git-repo-check","--ephemeral","-s","workspace-write","-C",str(ROOT),"-i",str(staged_image),"--json","-"]
    log=ep/"meta/rolling-review-workers"/f"{int(frame):02d}-{int(time.time())}.jsonl"; log.parent.mkdir(parents=True,exist_ok=True)
    try:
        with log.open("w",encoding="utf-8",newline="\n") as h:
            try:
                # On Windows, text=True encodes stdin through the active console code page.
                # Codex expects UTF-8, and frame contracts routinely contain Chinese text.
                cp=subprocess.run(cmd,input=prompt.encode("utf-8"),stdout=h,stderr=subprocess.STDOUT,timeout=timeout,check=False)
            except subprocess.TimeoutExpired: return {"decision":"UNCERTAIN","reason":"timeout","returncode":124}
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    if cp.returncode!=0 or not out.is_file(): return {"decision":"UNCERTAIN","reason":"worker_failed","returncode":cp.returncode}
    try: data=json.loads(out.read_text(encoding="utf-8-sig"))
    except Exception: return {"decision":"UNCERTAIN","reason":"invalid_json","returncode":cp.returncode}
    if data.get("decision") not in VALID: data["decision"]="UNCERTAIN"
    data["final_pass_authority"]=False
    return data
def self_test():
    assert "PASS_PREVIEW" in VALID
    print("ROLLING FRAME REVIEW SELF-TEST PASS")
if __name__=="__main__": self_test()
