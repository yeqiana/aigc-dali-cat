#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Runtime Request compiler.

Natural-language input -> immutable runtime request.
This module captures user intent and execution parameters only.
It MUST NOT invent creative decisions such as climax frame, weather physics or frame directives.
"""
from __future__ import annotations

import argparse, datetime as dt, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUESTS_DIR = ROOT / "runtime" / "requests"
EPISODE_REL = Path("meta/runtime-request.json")
SCHEMA_VERSION = 1
DEFAULT_BRANCH = "story"
STORY_MODES = {"auto_create", "user_seed", "core_constraints", "locked_story"}
LOCKED_SIGNALS = ("不要改剧情","剧情已锁定","剧情已经定了","严格按这个剧情","严格按这个故事","只能润色","故事结构不要动","不要改故事")
CONSTRAINT_SIGNALS = ("必须保留","不能改","一定要有","核心设定","结尾必须","必须有")
SEED_SIGNALS = ("剧情大概是","剧情大概","大概剧情","大概讲","故事大概是","我有个想法","我想的是","故事可以是","差不多是")
FULL_AUTO_SIGNALS = ("全自动","做到最终交付","不要每一步问","不用每一步问","一路做下去","直接做完")
RESUME_SIGNALS = ("使用 resume 模式","resume 模式","从上次验证通过的断点继续","从上次断点继续","从断点继续","继续上次断点","resume")
REPAIR_ONLY_SIGNALS = ("只修","只返修","repair only","repair_only")
RELEASE_ONLY_SIGNALS = ("只做发布","只做release","release only","release_only")
DATA_REVIEW_SIGNALS = ("只做复盘","数据复盘","data review","data_review")
PREPRODUCTION_SIGNALS = ("只做前期资产","只做前期","不要生成图片","不生图","做到可以正式生图的交接状态","做到生图交接状态","preproduction only","preproduction_only")
IMAGE_CONTINUE_SIGNALS = ("从生图开始","从图片开始","接管前期资产","接管已经完成的前期资产","不要重写剧情","image continue","image_continue")

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_text(path): return path.read_text(encoding="utf-8-sig")
def read_json(path):
    data=json.loads(read_text(path))
    if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
    return data
def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def contains_any(text,signals):
    low=text.lower(); return any(s.lower() in low for s in signals)
def request_id(text):
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")+"_"+hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]

def parse_topic(text):
    for left,right in (("「","」"),("《","》"),("『","』"),('"','"'),("“","”")):
        if left in text and right in text:
            start=text.find(left)+len(left); end=text.find(right,start)
            if end>start:
                title=text[start:end].strip()
                if title:return title,title
    for pattern in (r"(?:做一篇|制作一篇|全自动做一篇|写一篇)\s*[：:]?\s*([^\n，。,.]{2,40})",r"(?:题目|主题|题材)\s*[：:]\s*([^\n]{2,60})"):
        m=re.search(pattern,text,flags=re.I)
        if m:
            title=m.group(1).strip(" \t。,.，")
            if title:return title,title
    return None,None

def parse_branch(text):
    m=re.search(r"(?:读取|使用|切到|切换到)?\s*([A-Za-z0-9._/-]+)\s*分支",text,flags=re.I)
    return (m.group(1),"user_explicit") if m else (DEFAULT_BRANCH,"system_default")

def parse_image_model(text):
    patterns=(r"\bimage\s*[:=]\s*([A-Za-z0-9._-]+)",r"图片模型\s*(?:用|使用|[:=])\s*([A-Za-z0-9._-]+)",r"图像模型\s*(?:用|使用|[:=])\s*([A-Za-z0-9._-]+)",r"(?:用|使用)\s+(gpt-image-[A-Za-z0-9._-]+)")
    for pattern in patterns:
        m=re.search(pattern,text,flags=re.I)
        if m:return {"provider":"openai","model":m.group(1),"source":"user_explicit","strict_model":True}
    return {"provider":"openai","model":"gpt-image-2","source":"system_default","strict_model":False}

def split_after_marker(text,markers):
    low=text.lower()
    for marker in markers:
        idx=low.find(marker.lower())
        if idx>=0:
            tail=text[idx+len(marker):].lstrip(" ：:\t\r\n")
            return tail.strip() or None
    return None

def extract_constraints(text):
    tail=split_after_marker(text,CONSTRAINT_SIGNALS)
    if not tail:return []
    rows=[]
    for raw in tail.splitlines():
        line=re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*","",raw).strip()
        if line and len(line)<=160: rows.append(line.rstrip("。；;"))
    if not rows:
        rows=[x.strip() for x in re.split(r"[；;]",tail) if x.strip()]
    return rows[:20]

def story_input(text):
    if contains_any(text,LOCKED_SIGNALS):
        return {"mode":"locked_story","raw":split_after_marker(text,LOCKED_SIGNALS) or text.strip(),"constraints":[],"rewrite_policy":"logic_polish_only","preserve_core_intent":True,"allow_structure_rewrite":False}
    if contains_any(text,CONSTRAINT_SIGNALS):
        return {"mode":"core_constraints","raw":text.strip(),"constraints":extract_constraints(text),"rewrite_policy":"preserve_constraints_optimize_rest","preserve_core_intent":True,"allow_structure_rewrite":True}
    if contains_any(text,SEED_SIGNALS):
        return {"mode":"user_seed","raw":split_after_marker(text,SEED_SIGNALS) or text.strip(),"constraints":[],"rewrite_policy":"strengthen_and_rewrite","preserve_core_intent":True,"allow_structure_rewrite":True}
    return {"mode":"auto_create","raw":None,"constraints":[],"rewrite_policy":"auto_create","preserve_core_intent":True,"allow_structure_rewrite":True}

def parse_mode(text):
    if contains_any(text,RESUME_SIGNALS):return "resume"
    if contains_any(text,IMAGE_CONTINUE_SIGNALS):return "image_continue"
    if contains_any(text,PREPRODUCTION_SIGNALS):return "preproduction_only"
    if contains_any(text,REPAIR_ONLY_SIGNALS):return "repair_only"
    if contains_any(text,RELEASE_ONLY_SIGNALS):return "release_only"
    if contains_any(text,DATA_REVIEW_SIGNALS):return "data_review"
    return "full_auto"

def creative_hints(text):
    out=[]
    for line in text.splitlines():
        s=line.strip()
        if s and len(s)<=160 and any(x in s for x in ("希望","不要太","画风","质感","天气","炎热","下雨","下雪","冲击力","第一视角")):out.append(s)
    return out[:20]

def compile_request(text):
    if not isinstance(text,str) or not text.strip():raise ValueError("EMPTY_REQUEST")
    title,raw_topic=parse_topic(text); story=story_input(text); mode=parse_mode(text)
    if mode=="image_continue" and story.get("mode")=="auto_create":
        story={"mode":"locked_story","raw":None,"constraints":[],"rewrite_policy":"logic_polish_only","preserve_core_intent":True,"allow_structure_rewrite":False}
    if not title:
        if story["mode"]=="auto_create":raise ValueError("EMPTY_REQUEST: no topic/title/story seed found")
        title="AUTO_TITLE"; raw_topic=None
    branch,branch_source=parse_branch(text)
    full_auto=contains_any(text,FULL_AUTO_SIGNALS) or mode in {"full_auto","preproduction_only","image_continue","resume","repair_only","release_only","data_review"}
    image=parse_image_model(text)
    data={
        "schema_version":1,"request_id":request_id(text),"created_at":now(),"mode":mode,
        "repository":{"branch":branch,"source":branch_source},
        "topic":{"title":title,"raw":raw_topic},
        "story_input":story,
        "creative_hints":creative_hints(text),
        "image_model":image["model"],
        "image_quality":"high",
        "image":{**image,"quality":"high"},
        "runtime":{"execution_mode":"dag","continuous_execution":bool(full_auto),"resume":True,"max_image_workers":3,"fail_soft":True,"incremental_reuse":True},
        "delivery":{"mode":"auto","zip_required_for_completion":False},
        "user_intent":{"full_auto_authorized":bool(full_auto),"allow_story_strengthening":story["mode"]!="locked_story","allow_story_rewrite":story["mode"] in {"auto_create","user_seed","core_constraints"},"ask_before_each_step":not bool(full_auto)},
        "provenance":{"source":"natural_language","original_request":text.strip()},
    }
    errors=validate_request(data)
    if errors:raise ValueError("; ".join(errors))
    return data

def validate_request(data):
    errors=[]
    if data.get("schema_version")!=1:errors.append("schema_version must be 1")
    if data.get("mode") not in {"full_auto","preproduction_only","image_continue","resume","repair_only","release_only","data_review"}:errors.append("invalid mode")
    story=data.get("story_input") or {}
    if story.get("mode") not in STORY_MODES:errors.append("invalid story_input.mode")
    if story.get("mode")=="user_seed" and not str(story.get("raw") or "").strip():errors.append("user_seed requires raw story seed")
    if story.get("mode")=="core_constraints" and not isinstance(story.get("constraints"),list):errors.append("core_constraints requires constraints list")
    image=data.get("image") or {}
    model=str(data.get("image_model") or image.get("model") or "").strip()
    quality=str(data.get("image_quality") or image.get("quality") or "high").strip().lower()
    if not model:errors.append("image model missing")
    if quality!="high":errors.append("image_quality must be high for formal production")
    if data.get("image_model") is not None and image.get("model") is not None and str(data["image_model"])!=str(image["model"]):errors.append("image_model must match image.model")
    if data.get("image_quality") is not None and image.get("quality") is not None and str(data["image_quality"]).lower()!=str(image["quality"]).lower():errors.append("image_quality must match image.quality")
    if image.get("source")=="user_explicit" and image.get("strict_model") is not True:errors.append("user_explicit image model requires strict_model=true")
    workers=(data.get("runtime") or {}).get("max_image_workers")
    if not isinstance(workers,int) or not 1<=workers<=3:errors.append("runtime.max_image_workers must be 1..3")
    if not str((data.get("topic") or {}).get("title") or "").strip():errors.append("topic.title missing")
    return errors

def write_compiled(data,output=None):
    target=output.resolve() if output else REQUESTS_DIR/f"{data['request_id']}.json"; write_json(target,data); return target
def bind_request(request_path,episode_dir,force=False):
    request_path=request_path.resolve(); episode_dir=episode_dir.resolve()
    if not request_path.is_file():raise ValueError(f"request file missing: {request_path}")
    try:episode_dir.relative_to(ROOT.resolve())
    except ValueError as exc:raise ValueError("episode must be inside repository") from exc
    data=read_json(request_path); errors=validate_request(data)
    if errors:raise ValueError("; ".join(errors))
    target=episode_dir/EPISODE_REL
    if target.is_file() and not force:
        existing=read_json(target)
        if existing!=data:raise ValueError("episode already has a different immutable runtime-request; use --force only for explicit correction")
        return target
    write_json(target,data); return target
def effective_for_episode(episode_dir):
    p=episode_dir/EPISODE_REL
    if not p.is_file():return None
    data=read_json(p); errors=validate_request(data)
    if errors:raise ValueError("; ".join(errors))
    return data

def self_test():
    a=compile_request("读取 story 分支。全自动做一篇「仲夏夜惊魂」。")
    assert a["story_input"]["mode"]=="auto_create" and a["image_model"]=="gpt-image-2" and a["image_quality"]=="high"
    b=compile_request("读取 story 分支。全自动做一篇「仲夏夜惊魂」。剧情大概是：几个人住进山里民宿。")
    assert b["story_input"]["mode"]=="user_seed" and "山里民宿" in b["story_input"]["raw"]
    c=compile_request("全自动做一篇「仲夏夜惊魂」，image=gpt-image-2。必须保留：\n1. 山里民宿\n2. 最后进入旧照片")
    assert c["story_input"]["mode"]=="core_constraints" and c["image"]["strict_model"] is True
    d=compile_request("全自动做一篇「仲夏夜惊魂」。剧情已经定了，不要改剧情：主角最后回家。")
    assert d["story_input"]["mode"]=="locked_story" and d["story_input"]["allow_structure_rewrite"] is False
    e=compile_request("读取 story 分支。制作「仲夏夜惊魂」的全部前期资产，做到可以正式生图的交接状态，不要生成图片。")
    assert e["mode"]=="preproduction_only"
    f=compile_request("读取 story 分支。接管「仲夏夜惊魂」已经完成的前期资产，不要重写剧情，从生图开始继续做到最终交付。")
    assert f["mode"]=="image_continue" and f["story_input"]["allow_structure_rewrite"] is False
    g=compile_request("继续「仲夏夜惊魂」，使用 resume 模式，从上次验证通过的断点继续。")
    assert g["mode"]=="resume"
    print("RUNTIME REQUEST V2.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("compile");g=p.add_mutually_exclusive_group(required=True);g.add_argument("--text");g.add_argument("--text-file",type=Path);p.add_argument("--output",type=Path)
    p=sub.add_parser("validate");p.add_argument("request_file",type=Path)
    p=sub.add_parser("bind");p.add_argument("request_file",type=Path);p.add_argument("episode_dir",type=Path);p.add_argument("--force",action="store_true")
    p=sub.add_parser("show");p.add_argument("request_file",type=Path)
    p=sub.add_parser("show-episode");p.add_argument("episode_dir",type=Path)
    sub.add_parser("self-test");a=ap.parse_args()
    try:
        if a.cmd=="self-test":self_test();return 0
        if a.cmd=="compile":
            text=a.text if a.text is not None else read_text(a.text_file);data=compile_request(text);target=write_compiled(data,a.output)
            print(json.dumps({"ok":True,"request_path":str(target),"request":data},ensure_ascii=False,indent=2));return 0
        if a.cmd=="validate":
            errors=validate_request(read_json(a.request_file.resolve()))
            if errors:[print("FAIL:",e) for e in errors];return 2
            print("RUNTIME REQUEST VALID");return 0
        if a.cmd=="bind":
            print(f"RUNTIME REQUEST BOUND: {bind_request(a.request_file,a.episode_dir,force=a.force)}");return 0
        if a.cmd=="show":print(a.request_file.resolve().read_text(encoding="utf-8-sig"));return 0
        print(json.dumps(effective_for_episode(a.episode_dir.resolve()) or {},ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        print("RUNTIME REQUEST ERROR:",exc);return 3
if __name__=="__main__":raise SystemExit(main())
