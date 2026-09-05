#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture diversity + anomaly logic + human action + restrained emotion/interaction."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import storyos_config

REL=Path("meta/shot-progression-review.json")
ANOMALY_STAGES={"ordinary","discovery","confirmation","spatial_contradiction","causal_contradiction","human_consequence","reversal","payoff"}
STRONG_LOGIC={"spatial_contradiction","causal_contradiction","human_consequence","reversal","payoff"}
HUMAN_STAGES={"ordinary","notice","observe","verify","discuss","move","act","fail","adapt","consequence"}
PASSIVE={"ordinary","notice","observe"}
EMOTION_STATES={"ordinary","relaxed","curious","alert","uneasy","urgent"}
RESPONSE_SYNC={"not_applicable","single_subject","asynchronous","shared_but_unsynchronized"}
INTERACTION_TYPES={"none","group_selfie","shared_attention","show_phone","point_out","hand_item","check_map",
                   "talk","tease","help_clothing","touch_support","pack_together","enter_vehicle","leave_vehicle","other"}
ROOT=Path(__file__).resolve().parents[2]

def _directing_grammar():
    cfg=storyos_config.load_config()
    rel=storyos_config.get_path(cfg,"directing.grammar_path")
    return read_json(ROOT/str(rel))

def _director_sets():
    g=_directing_grammar()
    refs={str(x.get("id")):x for x in (g.get("cinematic_references") or []) if isinstance(x,dict) and x.get("id")}
    lighting=g.get("lighting") or {}
    return {
      "shot_scales":set(g.get("shot_scales") or []),
      "genre_families":set(g.get("genre_families") or []),
      "reference_rows":refs,
      "practical_sources":set(lighting.get("practical_sources") or []),
      "contrast_modes":set(lighting.get("contrast_modes") or []),
      "suspense_functions":set(lighting.get("suspense_functions") or []),
      "concealment_carriers":set(g.get("concealment_carriers") or []),
    }

def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def frame_count(ep):
    d=read_json(Path(ep)/"meta/release-manifest.json")
    return int(((d.get("release") or {}).get("body_frame_count")) or 0)
def _multi_person(ep):
    p=Path(ep)/"meta/character-contract.json"
    if not p.is_file():return False
    try:return len((((read_json(p).get("cast") or {}).get("members")) or []))>=2
    except Exception:return False
def _opening_applicable(ep):
    p=Path(ep)/"meta/opening-social-anchor.json"
    if not p.is_file():return False
    try:return read_json(p).get("applicable") is True
    except Exception:return False

def prepare(ep,force=False):
    ep=Path(ep).resolve();target=ep/REL
    if target.is_file() and not force:return read_json(target)
    total=frame_count(ep);multi=_multi_person(ep);rows=[]
    for n in range(1,total+1):
        rows.append({
          "frame":f"{n:02d}","camera_position":"","subject_distance":"","primary_subject":"",
          "action":"","visual_function":"","capture_purpose":"","pov_mode":"","location_zone":"",
          "shot_scale":"","scene_position_id":"",
          "cinematic_reference":{"reference_id":"","technique_translation":"","exact_shot_recreation":False},
          "lighting_design":{"practical_source":"","contrast_mode":"","suspense_function":"none","physically_motivated":True,"invented_cinematic_light":False},
          "anomaly_concealment":{"carrier":"none","purpose":"","physical_anchor":"","adds_information":False},
          "anomaly_logic_stage":"ordinary","human_action_stage":"ordinary","human_present":False,
          "emotion":{"state":"ordinary","intensity":0,"trigger":"","response_sync":"not_applicable"},
          "interaction":{"type":"none","actor":"","target":"","action":"","meaningful":False},
          "new_information":False,"continuity_exception_reason":""
        })
    d={
      "schema_version":3,"status":"DRAFT","genre_family":"general_reality_crack",
      "anomaly_applicable":True,"anomaly_exception_reason":"",
      "interaction_applicable":multi,
      "interaction_exception_reason":"" if multi else "single-person or non-group story",
      "rules":{
        "max_identical_setup_consecutive":2,"min_unique_setups_in_5_frames":3,
        "frame10_requires_new_question_or_evidence":True,
        "scale_only_escalation_is_not_enough":True,"max_passive_human_frames_after_confirmation":2,
        "emotion_intensity_range":[0,4],"emotion_trigger_required_at_intensity_gte":2,
        "synchronized_theatrical_reaction_forbidden":True,
        "max_consecutive_urgent_frames":2,
        "min_meaningful_interaction_per_5_human_frames":1,
        "max_meaningful_interaction_ratio":0.75,
        "opening_social_natural_interaction_required":True,
        "require_large_and_small_scene":True,
        "exact_scene_position_reuse_forbidden":True,
        "min_cinematic_reference_frames":2,
        "practical_lighting_required":True,
        "suspense_genre_requires_concealed_anomaly":True
      },
      "frames":rows
    }
    write_json(target,d);return d

def _sig(row):
    return tuple(str(row.get(k) or "").strip() for k in
                 ("camera_position","subject_distance","primary_subject","action","capture_purpose","pov_mode","location_zone"))

def _validate_response(ep,d,normalized,e):
    interaction_applicable=d.get("interaction_applicable") is True
    if _multi_person(ep) and not interaction_applicable:
        e.append("MULTI_PERSON_INTERACTION_REQUIRED:multi-person story must set interaction_applicable=true")
    if not interaction_applicable and not str(d.get("interaction_exception_reason") or "").strip():
        e.append("interaction_applicable=false requires interaction_exception_reason")
    human=[];urgent_run=0
    for n,row,_ in normalized:
        if not isinstance(row.get("human_present"),bool):
            e.append(f"frame {n:02d} human_present must be boolean");continue
        emotion=row.get("emotion") or {};interaction=row.get("interaction") or {}
        state=str(emotion.get("state") or "");intensity=emotion.get("intensity")
        sync=str(emotion.get("response_sync") or "")
        if state not in EMOTION_STATES:e.append(f"frame {n:02d} invalid emotion state")
        if not isinstance(intensity,int) or isinstance(intensity,bool) or not 0<=intensity<=4:
            e.append(f"frame {n:02d} emotion intensity must be integer 0..4");intensity=0
        if intensity>=2 and not str(emotion.get("trigger") or "").strip():
            e.append(f"EMOTION_CAUSALITY_FAIL:{n:02d}:intensity>=2 requires trigger")
        if sync not in RESPONSE_SYNC:e.append(f"frame {n:02d} invalid response_sync")
        if row.get("human_present") is True and sync=="not_applicable":
            e.append(f"frame {n:02d} human-present response_sync cannot be not_applicable")
        if state=="ordinary" and intensity>1:e.append(f"frame {n:02d} ordinary emotion intensity should be <=1")
        if state=="urgent" and intensity<3:e.append(f"frame {n:02d} urgent emotion intensity should be >=3")
        if intensity==4:
            urgent_run+=1
            if urgent_run>2 and not str(row.get("continuity_exception_reason") or "").strip():
                e.append(f"EMOTION_OVERPLAY:{n:02d}:urgent >2 consecutive")
        else:urgent_run=0
        itype=str(interaction.get("type") or "")
        meaningful=interaction.get("meaningful")
        if itype not in INTERACTION_TYPES:e.append(f"frame {n:02d} invalid interaction type")
        if not isinstance(meaningful,bool):e.append(f"frame {n:02d} interaction.meaningful must be boolean")
        if meaningful:
            if not row.get("human_present"):e.append(f"frame {n:02d} meaningful interaction requires human_present")
            if itype=="none":e.append(f"frame {n:02d} meaningful interaction cannot use type=none")
            if not str(interaction.get("actor") or "").strip():e.append(f"frame {n:02d} meaningful interaction actor missing")
            if not str(interaction.get("action") or "").strip():e.append(f"frame {n:02d} meaningful interaction action missing")
        elif itype!="none":
            e.append(f"frame {n:02d} non-none interaction should be meaningful=true")
        if row.get("human_present") is True:human.append((n,row))
    if interaction_applicable and len(human)>=5:
        for i in range(0,len(human)-4):
            win=human[i:i+5]
            if not any(((r.get("interaction") or {}).get("meaningful") is True) for _,r in win):
                e.append(f"INTERACTION_DENSITY_FAIL:{win[0][0]:02d}-{win[-1][0]:02d}:5 human frames without meaningful interaction")
                break
        meaningful_count=sum(1 for _,r in human if ((r.get("interaction") or {}).get("meaningful") is True))
        if len(human)>=8 and meaningful_count/len(human)>0.75:
            e.append("INTERACTION_OVERUSE:meaningful interaction ratio >0.75; avoid relationship-photo feel")
    if interaction_applicable and _opening_applicable(ep):
        opening=[r for n,r in human if n in {1,2}]
        if not opening:
            e.append("OPENING_INTERACTION_FAIL:opening social anchor Frame 01/02 must mark human_present=true")
        elif not any(((r.get("interaction") or {}).get("meaningful") is True) for r in opening):
            e.append("OPENING_INTERACTION_FAIL:opening social anchor needs at least one natural meaningful interaction in Frame 01/02")

def _validate_directing(d,normalized,e):
    sets=_director_sets();genre=str(d.get("genre_family") or "")
    if genre not in sets["genre_families"]:e.append("genre_family invalid for directing grammar")
    positions=set();scales=[];ref_frames=0;concealed_frames=0;prev_scale=None;same_scale_run=0;prev_carrier=None;same_carrier_run=0
    large={"extreme_wide","wide"};small={"close","detail"}
    for n,row,_ in normalized:
        scale=str(row.get("shot_scale") or "")
        if scale not in sets["shot_scales"]:e.append(f"frame {n:02d} invalid shot_scale")
        else:
            scales.append(scale);same_scale_run=same_scale_run+1 if scale==prev_scale else 1
            if same_scale_run>2:e.append(f"SHOT_SCALE_REPEAT:{n:02d}:same shot scale >2 consecutive")
            prev_scale=scale
        pos=str(row.get("scene_position_id") or "").strip()
        if not pos:e.append(f"frame {n:02d} scene_position_id missing")
        elif pos in positions:e.append(f"SCENE_POSITION_REUSE:{n:02d}:{pos}")
        else:positions.add(pos)
        cref=row.get("cinematic_reference") or {}
        if not isinstance(cref,dict):e.append(f"frame {n:02d} cinematic_reference must be object");cref={}
        rid=str(cref.get("reference_id") or "").strip()
        if rid:
            ref=sets["reference_rows"].get(rid)
            if not ref:e.append(f"frame {n:02d} invalid cinematic reference id: {rid}")
            else:
                fits=set(ref.get("genre_fit") or [])
                if genre and fits and genre not in fits:e.append(f"frame {n:02d} cinematic reference {rid} not suited to genre {genre}")
            if not str(cref.get("technique_translation") or "").strip():e.append(f"frame {n:02d} cinematic technique_translation missing")
            if cref.get("exact_shot_recreation") is not False:e.append(f"frame {n:02d} exact film-shot recreation forbidden")
            ref_frames+=1
        light=row.get("lighting_design") or {}
        if not isinstance(light,dict):e.append(f"frame {n:02d} lighting_design must be object");light={}
        if str(light.get("practical_source") or "") not in sets["practical_sources"]:e.append(f"frame {n:02d} invalid practical light source")
        if str(light.get("contrast_mode") or "") not in sets["contrast_modes"]:e.append(f"frame {n:02d} invalid lighting contrast_mode")
        sf=str(light.get("suspense_function") or "")
        if sf not in sets["suspense_functions"]:e.append(f"frame {n:02d} invalid lighting suspense_function")
        if light.get("physically_motivated") is not True:e.append(f"frame {n:02d} lighting must be physically_motivated=true")
        if light.get("invented_cinematic_light") is not False:e.append(f"frame {n:02d} invented cinematic light forbidden")
        stage=str(row.get("anomaly_logic_stage") or "")
        if stage != "ordinary" and sf=="none":
            e.append(f"LIGHTING_NARRATIVE_MISSING:{n:02d}:anomaly frame needs a real-light narrative function")
        conceal=row.get("anomaly_concealment") or {}
        if not isinstance(conceal,dict):e.append(f"frame {n:02d} anomaly_concealment must be object");conceal={}
        carrier=str(conceal.get("carrier") or "")
        if carrier not in sets["concealment_carriers"]:e.append(f"frame {n:02d} invalid anomaly concealment carrier")
        non_direct=carrier not in {"none","direct_visible",""}
        if non_direct:
            concealed_frames+=1
            if not str(conceal.get("purpose") or "").strip():e.append(f"frame {n:02d} concealed anomaly purpose missing")
            if not str(conceal.get("physical_anchor") or "").strip():e.append(f"frame {n:02d} concealed anomaly physical_anchor missing")
            if conceal.get("adds_information") is not True:e.append(f"frame {n:02d} concealed anomaly must add information")
            same_carrier_run=same_carrier_run+1 if carrier==prev_carrier else 1
            if same_carrier_run>2:e.append(f"CONCEALMENT_CARRIER_REPEAT:{n:02d}:{carrier}")
            prev_carrier=carrier
        else:
            same_carrier_run=0;prev_carrier=None
    if scales and not any(x in large for x in scales):e.append("SHOT_SCALE_COVERAGE_FAIL:episode requires at least one large/establishing scene")
    if scales and not any(x in small for x in scales):e.append("SHOT_SCALE_COVERAGE_FAIL:episode requires at least one close/detail small scene")
    if len(set(scales))<3:e.append("SHOT_SCALE_COVERAGE_FAIL:episode requires at least three shot scales")
    if len(normalized)>=8 and ref_frames<2:e.append("CINEMATIC_REFERENCE_COVERAGE_FAIL:at least two frames must translate a classic shot structure")
    suspense={"suspense_strange","folk_horror","travel_anomaly","mountain_mockumentary","old_device_mystery","general_reality_crack"}
    if genre in suspense and d.get("anomaly_applicable") is True and concealed_frames<1:
        e.append("ANOMALY_CONCEALMENT_MISSING:suspense genre requires at least one mirror/reflection/fog/light/occlusion carrier")

def validate(ep,require_locked=True):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["meta/shot-progression-review.json missing"]
    d=read_json(p);e=[];total=frame_count(ep);version=int(d.get("schema_version") or 1)
    if version not in {1,2,3}:e.append("shot progression schema_version must be 1, 2 or 3")
    if require_locked and d.get("status")!="LOCKED":e.append("shot progression review must be LOCKED")
    rows=d.get("frames") or []
    if len(rows)!=total:e.append(f"shot progression frame count mismatch {len(rows)} != {total}")
    normalized=[];same_run=0;prev_sig=None
    for row in rows:
        try:n=int(row.get("frame"))
        except Exception:e.append("invalid frame id");continue
        for k in ("camera_position","subject_distance","primary_subject","action","visual_function","capture_purpose","pov_mode","location_zone"):
            if not str(row.get(k) or "").strip():e.append(f"frame {n:02d} {k} missing")
        if str(row.get("anomaly_logic_stage") or "") not in ANOMALY_STAGES:e.append(f"frame {n:02d} invalid anomaly stage")
        if str(row.get("human_action_stage") or "") not in HUMAN_STAGES:e.append(f"frame {n:02d} invalid human action stage")
        if not isinstance(row.get("new_information"),bool):e.append(f"frame {n:02d} new_information must be boolean")
        sig=_sig(row);same_run=same_run+1 if sig==prev_sig else 1
        if same_run>2 and not str(row.get("continuity_exception_reason") or "").strip():
            e.append(f"CAPTURE_SETUP_REPEAT:{n:02d}:same setup >2 consecutive")
        prev_sig=sig;normalized.append((n,row,sig))
    normalized.sort()
    for i in range(0,max(0,len(normalized)-4)):
        win=normalized[i:i+5]
        if len({x[2] for x in win})<3:e.append(f"CAPTURE_DIVERSITY_FAIL:{win[0][0]:02d}-{win[-1][0]:02d}")
    applicable=d.get("anomaly_applicable") is True
    if not applicable:
        if not str(d.get("anomaly_exception_reason") or "").strip():e.append("anomaly_applicable=false requires anomaly_exception_reason")
    else:
        stages=[str(r.get("anomaly_logic_stage")) for _,r,_ in normalized]
        if "discovery" not in stages:e.append("anomaly progression requires discovery")
        if "confirmation" not in stages:e.append("anomaly progression requires confirmation")
        if total>=8 and not any(s in STRONG_LOGIC for s in stages):e.append("ANOMALY_LOGIC_FAIL:scale/count escalation alone is insufficient")
        try:conf=stages.index("confirmation")
        except ValueError:conf=-1
        if conf>=0:
            after=stages[conf+1:min(len(stages),conf+6)]
            if len(after)>=3 and not any(s in STRONG_LOGIC for s in after):e.append(f"ANOMALY_LOGIC_STALL:after confirmation frame {normalized[conf][0]:02d}")
            passive_run=0
            for idx in range(conf+1,len(normalized)):
                hs=str(normalized[idx][1].get("human_action_stage"))
                passive_run=passive_run+1 if hs in PASSIVE else 0
                if passive_run>2:
                    e.append(f"HUMAN_ACTION_STALL:{normalized[idx][0]:02d}");break
    if total>=10:
        row10=next((r for n,r,_ in normalized if n==10),None)
        if row10 and (row10.get("new_information") is not True or str(row10.get("visual_function") or "").lower() in {"recap","bridge","repeat"}):
            e.append("FRAME10_MUST_OPEN_NEW_QUESTION_OR_EVIDENCE")
    if version>=2:_validate_response(ep,d,normalized,e)
    if version>=3:_validate_directing(d,normalized,e)
    return e

def resolve_frame(ep,frame):
    d=read_json(Path(ep).resolve()/REL);key=f"{int(frame):02d}"
    row=next((x for x in (d.get("frames") or []) if str(x.get("frame")).zfill(2)==key),None)
    return {"frame":key,"shot_progression":row or {}}

def self_test():
    sets=_director_sets()
    assert "wide" in sets["shot_scales"] and "detail" in sets["shot_scales"]
    assert "REFLECTION_SECOND_LAYER" in sets["reference_rows"]
    assert "glass_reflection" in sets["concealment_carriers"]
    assert "spatial_contradiction" in STRONG_LOGIC
    assert "urgent" in EMOTION_STATES
    assert "group_selfie" in INTERACTION_TYPES
    assert 4==max(range(5))
    print("SHOT PROGRESSION V3 DIRECTING SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("validate");p.add_argument("episode_dir");p.add_argument("--allow-draft",action="store_true")
    p=sub.add_parser("resolve-frame");p.add_argument("episode_dir");p.add_argument("frame",type=int)
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.force),ensure_ascii=False,indent=2));return 0
    if a.cmd=="validate":
        e=validate(ep,not a.allow_draft)
        if e:[print("FAIL:",x) for x in e];return 2
        print("SHOT PROGRESSION VERIFIED");return 0
    if a.cmd=="resolve-frame":print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
