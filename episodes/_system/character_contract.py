#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Character Contract.

Character/entry/scene selection is a Story Build Input Contract, not a new Episode stage.
"""
from __future__ import annotations

import argparse, datetime as dt, hashlib, json, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STD = ROOT / "standards"
REL = Path("meta/character-contract.json")
POOL_FILES = {
    "characters": STD / "character-pools.json",
    "entries": STD / "entry-motivation-pools.json",
    "scenes": STD / "scene-pools.json",
    "forbidden": STD / "forbidden-character-roles.json",
}

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_json(path):
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
    return data

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def pools():
    return {k:read_json(v) for k,v in POOL_FILES.items()}

def request(ep):
    p=ep/"meta/runtime-request.json"
    return read_json(p) if p.is_file() else {}

def source_text(ep):
    r=request(ep)
    bits=[
        str(((r.get("topic") or {}).get("title")) or ""),
        str(((r.get("story_input") or {}).get("raw")) or ""),
        str(((r.get("provenance") or {}).get("original_request")) or ""),
        " ".join(str(x) for x in (r.get("creative_hints") or [])),
    ]
    return "\n".join(x for x in bits if x)

def seed_for(ep):
    r=request(ep)
    raw=str(r.get("request_id") or "")+"|"+str(((r.get("topic") or {}).get("title")) or "")+"|"+ep.as_posix()
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],16)

def weighted_choice(rng,weights):
    items=list(weights.items()); total=sum(float(v) for _,v in items)
    point=rng.random()*total; acc=0.0
    for key,value in items:
        acc+=float(value)
        if point<=acc:return key
    return items[-1][0]

def explicit_year(text):
    years=[int(x) for x in re.findall(r"\b(20\d{2})\b",text)]
    for y in years:
        if 2004<=y<=2010 or 2019<=y<=2026:return y
    return None

def choose_era(text,rng,p):
    y=explicit_year(text)
    if y is not None:return ("2004_2010" if y<=2010 else "modern_2020s"),y,"user_text"
    if any(x in text for x in ("2004","2005","2006","2007","2008","2009","2010","MP3","MP4","功能机","翻盖手机")):
        era="2004_2010"
    elif any(x in text for x in ("2020","2021","2022","2023","2024","2025","2026","智能手机","直播")):
        era="modern_2020s"
    else:
        era=weighted_choice(rng,p["characters"]["era_weights_when_unspecified"])
    year=rng.choice(p["characters"]["eras"][era]["default_years"])
    return era,year,"explicit_hint_or_weighted"

def choose_cast(text,rng,p):
    group=any(x in text for x in ("四五个","4-5","4—5","四个人","五个人","小团体","小团伙","一群朋友","几个朋友"))
    pair=any(x in text for x in ("两个人","情侣","两名","俩人"))
    female=("女生" in text or "女孩" in text) and not ("男生" in text or "男女" in text)
    male=("男生" in text or "男孩" in text) and not ("女生" in text or "男女" in text)
    if group:
        size=5 if "五" in text else 4
        return "mixed_friend_group_4_5",size
    if pair:return "pair",2
    if female:return "single_female",1
    if male:return "single_male",1
    bucket=weighted_choice(rng,p["characters"]["cast_size_weights"])
    if bucket=="small_group_4_5":return "mixed_friend_group_4_5",rng.choice([4,5])
    if bucket=="pair":return "pair",2
    return rng.choice(["single_male","single_female"]),1

def choose_entry(text,rng,p):
    for keyword,entry in p["entries"]["keyword_map"].items():
        if keyword in text:return entry,"user_hint"
    return weighted_choice(rng,p["entries"]["default_weights"]),"weighted"

def choose_scene(entry,rng,p):
    cat=rng.choice(p["scenes"]["entry_to_scene_preferences"][entry])
    place=rng.choice(p["scenes"]["scenes"][cat])
    return cat,place

def member_rows(era,cast_type,size,rng,p):
    era_cfg=p["characters"]["eras"][era]
    age_lo,age_hi=era_cfg["core_age_range"]
    if size==1:
        genders=["female" if cast_type=="single_female" else "male"]
    elif size>=4:
        patterns=p["characters"]["group_gender_patterns"][str(size)]
        genders=list(rng.choice(patterns))
    else:
        genders=["male","female"][:size]
    rows=[]
    for i,g in enumerate(genders,1):
        wardrobe=rng.choice(era_cfg["wardrobe_female" if g=="female" else "wardrobe_male"])
        rows.append({
            "id":f"P{i:02d}",
            "pov":i==1,
            "gender":g,
            "age":rng.randint(age_lo,age_hi),
            "build":"普通年轻人体型",
            "hair":"普通黑色日常发型",
            "clothing_anchor":wardrobe,
            "device_anchor":rng.choice(era_cfg["devices"]) if i==1 else None
        })
    return rows

def prepare(ep,force=False):
    ep=Path(ep).resolve()
    target=ep/REL
    if target.is_file() and not force:return read_json(target)
    p=pools(); text=source_text(ep); rng=random.Random(seed_for(ep))
    era,year,era_source=choose_era(text,rng,p)
    cast_type,size=choose_cast(text,rng,p)
    entry,entry_source=choose_entry(text,rng,p)
    scene_cat,scene_place=choose_scene(entry,rng,p)
    rel=rng.choice(p["characters"]["relationship_pool"]) if size>1 else "单人"
    members=member_rows(era,cast_type,size,rng,p)
    no_plan=p["entries"]["entries"][entry]["no_anomaly_plan"]
    data={
        "schema_version":1,
        "status":"DRAFT",
        "derived_from_pools":True,
        "not_episode_stage":True,
        "created_at":now(),
        "selection_seed":seed_for(ep),
        "era":{"bucket":era,"year":year,"source":era_source},
        "cast":{"type":cast_type,"size":size,"relationship":rel,"members":members},
        "pov":{"character_id":"P01","first_person":True},
        "entry":{"type":entry,"label":p["entries"]["entries"][entry]["label"],"source":entry_source,"reason":"由 Story Build 基于该生活化动机具体化"},
        "scene":{"primary_category":scene_cat,"primary_place":scene_place},
        "role_policy":{
            "protagonist_role":"普通年轻人/普通朋友小团体",
            "career_function":"arrival_only",
            "solves_anomaly_professionally":False
        },
        "no_anomaly_test":{
            "question":"如果删掉所有异常，这一天是否仍像真实生活？",
            "ordinary_day_plan":no_plan,
            "pass":True,
            "must_be_rechecked_before_story_lock":True,
            "rechecked_against_final_story":False
        },
        "continuity_policy":{
            "member_count_changes_require_story_event":True,
            "pov_character_id_stable":True,
            "clothing_and_device_anchors_propagate_to_frame_contract":True
        },
        "ordinary_person_score":100,
        "forbidden_role_check":{"pass":True,"hits":[]},
        "story_build_note":"这是 Story Build Input Contract。可以在同一母池边界内细化，但不得换成抢修/调查等功能型职业主角。Story Lock 前将 status 改为 LOCKED 并复核字段。"
    }
    write_json(target,data)
    return data

def forbidden_hits(data,p):
    raw=json.dumps(data,ensure_ascii=False)
    hits=[x for x in p["forbidden"]["forbidden_cn"] if x in raw]
    hits += [x for x in p["forbidden"]["forbidden_entry_patterns_cn"] if x in raw]
    return sorted(set(hits))

def score(data,p):
    s=100
    cast=data.get("cast") or {}
    members=cast.get("members") or []
    if not isinstance(members,list) or not members:s-=40
    if int(cast.get("size") or 0)!=len(members):s-=20
    for m in members:
        age=int(m.get("age") or 0)
        if not 19<=age<=30:s-=10
        if not str(m.get("clothing_anchor") or "").strip():s-=5
    if forbidden_hits(data,p):s-=70
    role=data.get("role_policy") or {}
    if role.get("solves_anomaly_professionally") is True:s-=40
    if role.get("career_function") not in {"arrival_only","none",None}:s-=20
    entry=((data.get("entry") or {}).get("type"))
    if entry not in (p["entries"]["entries"] or {}):s-=25
    no=data.get("no_anomaly_test") or {}
    if no.get("pass") is not True:s-=25
    if not str(no.get("ordinary_day_plan") or "").strip():s-=15
    return max(0,s)

def validate(ep,require_locked=False):
    ep=Path(ep).resolve(); target=ep/REL
    if not target.is_file():return ["meta/character-contract.json missing; run prepare"]
    p=pools(); data=read_json(target); errors=[]
    if data.get("schema_version")!=1:errors.append("schema_version must be 1")
    if require_locked and data.get("status")!="LOCKED":errors.append("character contract status must be LOCKED before Story Lock")
    hits=forbidden_hits(data,p)
    if hits:errors.append("forbidden protagonist/entry role detected: "+", ".join(hits))
    cast=data.get("cast") or {}; members=cast.get("members") or []
    size=cast.get("size")
    if not isinstance(size,int) or not 1<=size<=5:errors.append("cast.size must be 1..5")
    if not isinstance(members,list) or len(members)!=size:errors.append("cast.members must match cast.size")
    if size>=4:
        genders={m.get("gender") for m in members}
        if not {"male","female"}.issubset(genders):errors.append("4-5 person default friend group must be mixed gender")
    era=(data.get("era") or {}).get("bucket")
    if era not in p["characters"]["eras"]:errors.append("invalid era bucket")
    role=data.get("role_policy") or {}
    if role.get("solves_anomaly_professionally") is True:errors.append("protagonist must not professionally solve anomaly")
    if role.get("career_function") not in {"arrival_only","none",None}:errors.append("career function must be arrival_only/none")
    no=data.get("no_anomaly_test") or {}
    if no.get("pass") is not True:errors.append("NO-ANOMALY TEST must PASS")
    if require_locked and no.get("rechecked_against_final_story") is not True:
        errors.append("NO-ANOMALY TEST must be rechecked_against_final_story=true before Story Lock")
    computed=score(data,p)
    if computed<75:errors.append(f"ORDINARY_PERSON_SCORE too low: {computed} < 75")
    return errors

def lock(ep):
    ep=Path(ep).resolve()
    data=prepare(ep)
    data["status"]="LOCKED"
    data["locked_at"]=now()
    # Do not auto-set rechecked_against_final_story; the Story worker must explicitly recheck it.
    p=pools()
    data["forbidden_role_check"]={"pass":not bool(forbidden_hits(data,p)),"hits":forbidden_hits(data,p)}
    data["ordinary_person_score"]=score(data,p)
    write_json(ep/REL,data)
    return data

def prompt_block(ep):
    p=Path(ep).resolve()/REL
    if not p.is_file():return ""
    d=read_json(p)
    return json.dumps(d,ensure_ascii=False,sort_keys=True)

def self_test():
    p=pools()
    assert "2004_2010" in p["characters"]["eras"]
    assert "modern_2020s" in p["characters"]["eras"]
    assert "repair_worker" in p["forbidden"]["forbidden_ids"]
    assert "casual_work" in p["entries"]["entries"]
    print("CHARACTER CONTRACT SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("lock");p.add_argument("episode_dir")
    p=sub.add_parser("validate");p.add_argument("episode_dir");p.add_argument("--require-locked",action="store_true")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":
        print(json.dumps(prepare(ep,a.force),ensure_ascii=False,indent=2));return 0
    if a.cmd=="lock":
        print(json.dumps(lock(ep),ensure_ascii=False,indent=2));return 0
    if a.cmd=="validate":
        errors=validate(ep,a.require_locked)
        if errors:
            [print("FAIL:",x) for x in errors];return 2
        print("CHARACTER CONTRACT VERIFIED");return 0
    p=ep/REL
    print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0

if __name__=="__main__": raise SystemExit(main())
