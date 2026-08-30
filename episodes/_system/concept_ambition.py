#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Concept Ambition + Image-first Propagation Gate."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
from story_os_contract import story_os_version

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_REL = Path("meta/concept-candidates.json")
REVIEW_REL = Path("meta/concept-ambition-review.json")
CANDIDATE_REVIEW_REL = Path("meta/.concept-ambition-review.candidate.json")
MIN_VERSION = (2, 1, 0)
SCORE_LIMITS = {
    "one_line_hook": 20, "hero_frame": 20, "escalation_ceiling": 20,
    "climax_visual_payoff": 15, "mechanism_novelty": 15, "discussion_space": 10,
}
WORDLESS_KEYS = ("stop_scroll", "escalation_readable", "curiosity_gap")
VIRAL_KEYS = ("cover", "mid", "climax")
BANDS = {"A1", "A2", "A3", "A4", "A5"}

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_json(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict): raise ValueError(f"JSON root must be object: {path}")
    return data

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def version_tuple(raw):
    try: return tuple(int(x) for x in str(raw or "").split("."))
    except Exception: return (0,)

def episode_contract_version(ep):
    versions = []
    for rel in ("meta/episode-state.json", "meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file(): continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,): versions.append((vt, raw))
        except Exception: pass
    return max(versions, key=lambda x:x[0])[1] if versions else story_os_version()

def required(ep):
    return version_tuple(episode_contract_version(ep)) >= MIN_VERSION

def resolve_ep(raw):
    ep = Path(raw).resolve()
    if not ep.is_dir(): raise SystemExit(f"episode directory not found: {ep}")
    try: ep.relative_to(ROOT.resolve())
    except ValueError: raise SystemExit("episode must be inside repository")
    return ep

def text(v): return str(v or "").strip()

def validate_candidates(data):
    errors = []
    rows = data.get("candidates")
    if not isinstance(rows, list) or not 8 <= len(rows) <= 12:
        return ["concept-candidates.json must contain 8-12 candidates"]
    ids = set()
    for i,row in enumerate(rows):
        where=f"candidates[{i}]"
        if not isinstance(row,dict):
            errors.append(f"{where} must be object"); continue
        cid=text(row.get("id"))
        if not cid: errors.append(f"{where}.id missing")
        elif cid in ids: errors.append(f"duplicate candidate id: {cid}")
        ids.add(cid)
        for key in ("title","one_line_hook","concept_class","discussion_question"):
            if not text(row.get(key)): errors.append(f"{where}.{key} missing")
        ceiling=row.get("anomaly_ceiling")
        if not isinstance(ceiling,dict): errors.append(f"{where}.anomaly_ceiling must be object")
        else:
            for key in ("initial","middle","climax"):
                if not text(ceiling.get(key)): errors.append(f"{where}.anomaly_ceiling.{key} missing")
        frames=row.get("viral_frames")
        if not isinstance(frames,dict): errors.append(f"{where}.viral_frames must be object")
        else:
            for key in VIRAL_KEYS:
                item=frames.get(key)
                if not isinstance(item,dict):
                    errors.append(f"{where}.viral_frames.{key} must be object"); continue
                if not text(item.get("visual")): errors.append(f"{where}.viral_frames.{key}.visual missing")
                if not text(item.get("why_stop")): errors.append(f"{where}.viral_frames.{key}.why_stop missing")
    return errors

def score_row(row, errors, where):
    scores=row.get("scores")
    if not isinstance(scores,dict):
        errors.append(f"{where}.scores must be object"); return -1
    total=0
    for key,maxv in SCORE_LIMITS.items():
        val=scores.get(key)
        if isinstance(val,bool) or not isinstance(val,(int,float)) or not 0 <= float(val) <= maxv:
            errors.append(f"{where}.scores.{key} must be 0..{maxv}"); continue
        total += int(val)
    if row.get("concept_voltage") != total:
        errors.append(f"{where}.concept_voltage must equal score sum {total}")
    return total

def validate_review(ep, review):
    if not required(ep): return []
    errors=[]
    cp=ep/CANDIDATES_REL
    if not cp.is_file(): return ["meta/concept-candidates.json missing"]
    candidates=read_json(cp)
    errors += validate_candidates(candidates)
    if errors: return errors
    if str(review.get("candidates_sha256") or "").lower() != sha256_file(cp).lower():
        errors.append("concept ambition review candidates_sha256 drift")
    if review.get("schema_version") != 1: errors.append("concept ambition review schema_version must be 1")
    prov=review.get("critic_provenance") or {}
    if prov.get("runtime")!="CODEX_ISOLATED" or prov.get("isolated_session") is not True:
        errors.append("concept ambition critic must be fresh CODEX_ISOLATED")
    if prov.get("attempt") not in {1,2}: errors.append("concept ambition critic attempt must be 1 or 2")
    expected_ids=[str(x.get("id") or "") for x in candidates["candidates"]]
    rows=review.get("candidates")
    if not isinstance(rows,list) or len(rows)!=len(expected_ids):
        errors.append("concept ambition review must return one row per candidate"); rows=[]
    seen=set(); high=0; by_id={}
    for i,row in enumerate(rows):
        where=f"review.candidates[{i}]"
        if not isinstance(row,dict): errors.append(f"{where} must be object"); continue
        cid=text(row.get("id")); seen.add(cid); by_id[cid]=row
        band=text(row.get("ambition_band"))
        if band not in BANDS: errors.append(f"{where}.ambition_band must be A1..A5")
        if band in {"A4","A5"}: high += 1
        score_row(row,errors,where)
        wt=row.get("wordless_test")
        if not isinstance(wt,dict): errors.append(f"{where}.wordless_test must be object")
        else:
            for key in WORDLESS_KEYS:
                if not isinstance(wt.get(key),bool): errors.append(f"{where}.wordless_test.{key} must be boolean")
    if seen != set(expected_ids): errors.append("concept ambition review ids do not match candidate ids")
    if high < 3: errors.append("candidate pool must contain at least 3 A4/A5 high-ambition concepts")
    selected=text(review.get("selected_id"))
    if selected not in by_id: errors.append("selected_id must reference a reviewed candidate")
    else:
        row=by_id[selected]
        if not isinstance(row.get("concept_voltage"),(int,float)) or float(row["concept_voltage"]) < 80:
            errors.append("selected concept_voltage must be >= 80")
        if row.get("ambition_band") not in {"A3","A4","A5"}:
            errors.append("selected ambition band must be A3/A4/A5")
        wt=row.get("wordless_test") or {}
        if not all(wt.get(k) is True for k in WORDLESS_KEYS):
            errors.append("selected concept must pass all three wordless tests")
    if not text(review.get("selection_reason")): errors.append("selection_reason missing")
    if review.get("issue_codes") not in ([],None): errors.append("issue_codes must be empty for PASS")
    if (review.get("summary") or {}).get("passed") is not True: errors.append("summary.passed must be true")
    return errors

def verify(ep):
    if not required(ep): return []
    p=ep/REVIEW_REL
    if not p.is_file(): return ["meta/concept-ambition-review.json missing"]
    try: return validate_review(ep,read_json(p))
    except Exception as exc: return [str(exc)]

def resolve_codex(raw):
    value=raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value: raise RuntimeError("Codex CLI not found")
    p=Path(value).expanduser().resolve()
    if not p.exists(): raise RuntimeError(f"Codex CLI not found: {p}")
    return p

def prefix(codex):
    if codex.suffix.lower()==".py": return [sys.executable,str(codex)]
    if os.name=="nt" and codex.suffix.lower() in {".cmd",".bat"}: return ["cmd.exe","/d","/c",str(codex)]
    return [str(codex)]

def critic_prompt(ep, cp, out, attempt):
    rel_ep=ep.relative_to(ROOT).as_posix()
    rel_cp=cp.relative_to(ROOT).as_posix()
    rel_out=out.relative_to(ROOT).as_posix()
    return f"""You are the independent Story OS V2.1 Concept Ambition + Image-first Propagation Critic.
Review ALL 8-12 concepts in {rel_cp}. This is a fresh isolated review.

DOCTRINE:
- Concept ambition comes BEFORE capture realism.
- Do NOT lower a concept because its place, creature, ruin, dream-space, anomaly scale, case phenomenon, geography or world rule cannot exist in reality.
- Reality-first constrains HOW the later image is captured, not WHAT may happen.
- Reward concepts whose Cover/Mid/Climax images work before captions.
- Penalize generic unease, text-dependent reveals, tiny escalation, discovery-only climaxes and visually ordinary payoffs.
- Fictional cases, impossible ruins, dream intrusion, cosmic anomalies, giant-scale anomalies and surreal geography are valid.
- The pool must include at least 3 genuinely high-ambition A4/A5 directions.

Bands: A1 restrained oddity; A2 clear anomaly; A3 strong anomaly; A4 large/high-impact anomaly; A5 world-rule loss/overwhelming anomaly.

Scores: one_line_hook 0-20; hero_frame 0-20; escalation_ceiling 0-20; climax_visual_payoff 0-15; mechanism_novelty 0-15; discussion_space 0-10.
concept_voltage = exact sum.

Wordless test: stop_scroll, escalation_readable, curiosity_gap.
Select exactly ONE concept. Winner must score >=80 and pass all 3 wordless checks.
If no valid winner exists, summary.passed=false.

Write ONLY JSON to {rel_out}:
{{
  "candidates":[{{
    "id":"C01","ambition_band":"A4",
    "scores":{{"one_line_hook":18,"hero_frame":19,"escalation_ceiling":18,"climax_visual_payoff":14,"mechanism_novelty":13,"discussion_space":9}},
    "concept_voltage":91,
    "wordless_test":{{"stop_scroll":true,"escalation_readable":true,"curiosity_gap":true}},
    "strengths":["..."],"risks":["..."]
  }}],
  "selected_id":"C01",
  "selection_reason":"...",
  "issue_codes":[],
  "summary":{{"passed":true}}
}}
Episode: {rel_ep}
Attempt: {attempt}
"""

def run_critic(ep, attempt, codex_raw, timeout):
    if not required(ep):
        print("CONCEPT AMBITION: NOT REQUIRED FOR LEGACY EPISODE"); return 0
    if attempt not in {1,2}: raise RuntimeError("attempt must be 1 or 2")
    cp=ep/CANDIDATES_REL
    if not cp.is_file(): raise RuntimeError("meta/concept-candidates.json missing")
    errs=validate_candidates(read_json(cp))
    if errs:
        [print("FAIL:",e) for e in errs]; return 2
    before=sha256_file(cp)
    candidate=ep/CANDIDATE_REVIEW_REL; candidate.unlink(missing_ok=True)
    codex=resolve_codex(codex_raw)
    cmd=prefix(codex)+["exec","--skip-git-repo-check","--ephemeral","-c",'model_reasoning_effort="medium"'," -s".strip(),"workspace-write","-C",str(ROOT),"--json","-"]
    log=ep/"meta"/f"concept-ambition-critic-attempt-{attempt}.jsonl"
    with log.open("w",encoding="utf-8",newline="\n") as h:
        done=subprocess.run(cmd,input=critic_prompt(ep,cp,candidate,attempt),text=True,stdout=h,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    if done.returncode != 0: raise RuntimeError(f"concept critic failed rc={done.returncode}; log={log}")
    if sha256_file(cp) != before: raise RuntimeError("concept critic modified candidate pool")
    if not candidate.is_file(): raise RuntimeError("concept critic did not produce candidate JSON")
    review=read_json(candidate)
    review["schema_version"]=1
    review["story_os_version"]=episode_contract_version(ep)
    review["candidates_sha256"]=before
    review["critic_provenance"]={"runtime":"CODEX_ISOLATED","isolated_session":True,"attempt":attempt,"reviewed_at":now(),"log":log.relative_to(ROOT).as_posix()}
    write_json(ep/REVIEW_REL,review); candidate.unlink(missing_ok=True)
    errs=validate_review(ep,review)
    if errs:
        print("CONCEPT AMBITION REVIEW FAIL")
        [print("FAIL:",e) for e in errs]; return 2
    print("CONCEPT AMBITION REVIEW PASS"); return 0

def init_candidates(ep):
    p=ep/CANDIDATES_REL
    if p.exists(): print(p); return 0
    rows=[]
    for i in range(1,9):
        rows.append({"id":f"C{i:02d}","title":"","one_line_hook":"","concept_class":"",
                     "anomaly_ceiling":{"initial":"","middle":"","climax":""},
                     "viral_frames":{"cover":{"visual":"","why_stop":""},"mid":{"visual":"","why_stop":""},"climax":{"visual":"","why_stop":""}},
                     "discussion_question":""})
    write_json(p,{"schema_version":1,"story_os_version":episode_contract_version(ep),
                  "creative_doctrine":"概念不要克制，镜头必须真实；真实性约束怎么拍，不限制发生什么。","candidates":rows})
    print(p); return 0

def self_test():
    rows=[]
    for i in range(8):
        rows.append({"id":f"C{i+1:02d}","title":"x","one_line_hook":"x","concept_class":"x",
                     "anomaly_ceiling":{"initial":"x","middle":"x","climax":"x"},
                     "viral_frames":{"cover":{"visual":"x","why_stop":"x"},"mid":{"visual":"x","why_stop":"x"},"climax":{"visual":"x","why_stop":"x"}},
                     "discussion_question":"x"})
    assert validate_candidates({"candidates":rows}) == []
    assert validate_candidates({"candidates":rows[:7]})
    print("CONCEPT AMBITION V2.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init"); p.add_argument("episode_dir")
    p=sub.add_parser("run-critic"); p.add_argument("episode_dir"); p.add_argument("--attempt",type=int,default=1); p.add_argument("--codex"); p.add_argument("--timeout",type=int,default=900)
    p=sub.add_parser("verify"); p.add_argument("episode_dir")
    p=sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=resolve_ep(a.episode_dir)
    if a.cmd=="init": return init_candidates(ep)
    if a.cmd=="show":
        for rel in (CANDIDATES_REL,REVIEW_REL):
            p=ep/rel; print(f"--- {rel} ---"); print(p.read_text(encoding="utf-8") if p.is_file() else "{}")
        return 0
    if a.cmd=="run-critic":
        try: return run_critic(ep,a.attempt,a.codex,a.timeout)
        except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as exc:
            print("CONCEPT AMBITION ERROR:",exc); return 3
    errs=verify(ep)
    if errs:
        [print("FAIL:",e) for e in errs]; return 2
    print("CONCEPT AMBITION VERIFIED"); return 0

if __name__=="__main__": raise SystemExit(main())
