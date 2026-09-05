#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile a compact, SHA-bound runtime context capsule for one DAG step.

The capsule is a derived cache, never authority. It exists to avoid making every scoped
Codex worker reread the whole repository policy stack before doing bounded work.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
import runtime_execution
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/runtime/execution-capsules")
AUTHORITY_FILES=[
    "config/storyos.yaml","config/index.yaml","START_HERE.md","SKILL.md","AGENTS.md","standards/制作规范_正式版.md",
    "runtimes/workflow-contract.json",
    "standards/Character_And_Entry_Pool_V1.0.md",
    "standards/character-pools.json",
    "standards/entry-motivation-pools.json",
    "standards/scene-pools.json",
    "standards/forbidden-character-roles.json",
    "runtimes/runtime-mode-contract-r2.json",
    "runtimes/runtime-fast-path-v251.json",  # STORY_OS_V2_5_1_RUNTIME_FAST_PATH
    "library/catalog.json",
    "library/copy/intro-openers.json",
    "standards/AIGC_Directing_Quality_V1.0.md",
    "standards/Character_Visual_And_Wardrobe_V1.0.md",
    "standards/Character_Master_Final_Closure_V1.0.md",
    "standards/Human_Response_Interaction_V1.0.md",
    "standards/wardrobe-scenario-profiles.json",
    "config/profiles/account_creative/default.json",
    "standards/directing_grammar_v1.json",
]
STEP_EVIDENCE={
    "CREATIVE_STORY":["meta/runtime-request.json","meta/episode-state.json","meta/character-contract.json","meta/resource-selection.json","meta/story-gates.json","reports/account-learning-index.json"],
    "PREIMAGE_COMPILE":["meta/runtime-request.json","meta/episode-state.json","meta/character-contract.json","meta/resource-selection.json","meta/story-gates.json","meta/intro-policy.json"],
    "VISUAL_LOCK":["meta/runtime-request.json","meta/episode-state.json","meta/character-contract.json","meta/story-gates.json","meta/concept-ambition-review.json"],
    "PRODUCTION":["meta/runtime-request.json","meta/episode-state.json","meta/character-contract.json","meta/story-gates.json","meta/visual-lock-plan.json","meta/production-ledger.json"],
    "RELEASE":["meta/runtime-request.json","meta/episode-state.json","meta/character-contract.json","meta/resource-selection.json","meta/intro-policy.json","meta/story-gates.json","meta/production-ledger.json","meta/runtime/provisional-release.json"],
}
RULE_KEYS=[
    "zip_is_delivery_adapter_not_stage_gate","codex_production_complete_at_publish_ready",
    "concept_ambition_before_story_lock","image_first_propagation_gate",
    "reality_limits_capture_not_concept","environment_is_physics_not_filter",
    "resolved_frame_contract_is_derived_cache","generation_and_review_bind_same_frame_contract_sha",
    "visual_lock_four_admissions","max_parallel_image_workers","production_ledger_single_writer",
    "technical_failure_does_not_consume_content_repair","scheduler_fail_soft",
    "fast_scout_never_final_pass","final_candidate_snapshot_before_publish_ready",
    "delivery_consumes_verified_snapshot","runtime_request_immutable_after_bind",
    "auto_create_story_when_missing","user_seed_requires_strengthen_and_rewrite",
    "default_image_model","default_image_quality","explicit_image_model_no_silent_fallback",
    "current_visual_lock_calibration_count",
    "visual_lock_real_1_plus_3_barrier",
    "visual_lock_dependents_require_baseline_review_pass",
    "reference_arbitration_max_refs",
    "final_snapshot_locks_character_master_assets",
    "human_response_interaction_enabled",
    "emotion_intensity_max",
    "interaction_density_min_one_per_5_human_frames",
    "performance_telemetry_fail_soft",
]

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()
def file_row(path,base):
    if not path.is_file(): return {"path":path.relative_to(base).as_posix(),"exists":False}
    data=path.read_bytes()
    return {"path":path.relative_to(base).as_posix(),"exists":True,"sha256":sha_bytes(data),"bytes":len(data)}
def read_json(path):
    if not path.is_file(): return None
    try:
        data=json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data,dict) else None
    except Exception:
        return None
def current_state(ep):
    d=read_json(ep/"meta/episode-state.json") or {}
    return d.get("current_state")
def compile_capsule(ep,step,write=True):
    if step not in STEP_EVIDENCE: raise ValueError(f"unsupported step: {step}")
    wf=read_json(ROOT/"runtimes/workflow-contract.json") or {}
    rules=wf.get("rules") or {}
    request=read_json(ep/"meta/runtime-request.json")
    execution=read_json(ep/"meta/runtime-execution.json")
    effective_mode=runtime_execution.effective_mode(ep)
    # STORY_OS_V2_5_1_RUNTIME_FAST_PATH
    runtime_fast_path=read_json(ROOT/"runtimes/runtime-fast-path-v251.json")
    runtime_capabilities=read_json(ep/"meta/runtime/runtime-capabilities.json")
    resume_capsule=read_json(ep/"meta/runtime/resume-capsule.json")
    authority=[file_row(ROOT/x,ROOT) for x in AUTHORITY_FILES]
    evidence=[]
    evidence_paths=list(STEP_EVIDENCE[step])
    if "meta/runtime-execution.json" not in evidence_paths: evidence_paths.insert(1,"meta/runtime-execution.json")
    quality_evidence={"CREATIVE_STORY":["meta/directing-quality.json","meta/voice-contract.json","meta/storyboard-density-review.json","meta/opening-social-anchor.json","meta/character-visual-contract.json","meta/shot-progression-review.json"],"PREIMAGE_COMPILE":["meta/directing-quality.json","meta/voice-contract.json","meta/storyboard-density-review.json","meta/opening-social-anchor.json","meta/character-visual-contract.json","meta/shot-progression-review.json","meta/capture-event-contract.json","meta/world-state.json","meta/temporal-continuity.json","meta/wardrobe-contract.json"],"VISUAL_LOCK":["meta/directing-quality.json","meta/character-visual-contract.json","meta/visual-lock-baseline-review.json","meta/character-pixel-master.json","meta/character-master-crops.json","meta/shot-progression-review.json","meta/capture-event-contract.json","meta/world-state.json","meta/temporal-continuity.json","meta/wardrobe-contract.json"],"PRODUCTION":["meta/character-visual-contract.json","meta/visual-lock-baseline-review.json","meta/character-pixel-master.json","meta/character-master-crops.json","meta/shot-progression-review.json","meta/capture-event-contract.json","meta/world-state.json","meta/temporal-continuity.json","meta/wardrobe-contract.json","meta/asset-lineage.json"],"RELEASE":["meta/voice-contract.json","meta/text-audit.json","meta/subtitle-voice-review.json","meta/visual-lock-baseline-review.json","meta/character-pixel-master.json","meta/character-master-crops.json","meta/asset-lineage.json"]}.get(step,[])
    for qrel in quality_evidence:
        if qrel not in evidence_paths:evidence_paths.append(qrel)
    for rel in evidence_paths:
        p=(ROOT/rel) if rel.startswith("reports/") else (ep/rel)
        base=ROOT if rel.startswith("reports/") else ep
        evidence.append(file_row(p,base))
    material={
      "schema_version":1,"story_os":"2.1","step":step,"current_state":current_state(ep),
      "runtime_request":request,
      "runtime_execution":execution,
      "effective_execution_mode":effective_mode,
      "runtime_fast_path":runtime_fast_path,
      "runtime_capabilities":runtime_capabilities,
      "resume_capsule":resume_capsule,
      "character_contract":read_json(ep/"meta/character-contract.json"),
      "invariants":{k:rules.get(k) for k in RULE_KEYS if k in rules},
      "authority_files":authority,
      "evidence_files":evidence,
      "authority_policy":"Derived cache only. If capsule conflicts with source authority, source authority wins.",
      "read_policy":"Fast Path: consume resume_capsule + runtime_capabilities + this step capsule first. Do not broad-rescan repository files while source SHA is unchanged; open source authority only for missing details, SHA drift, or conflict resolution.",
    }
    raw=json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    data={**material,"source_sha256":sha_bytes(raw),"compiled_at":now()}
    if write:
        out=ep/REL/f"{step.lower()}.json"; out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    return data
def self_test():
    assert "default_image_model" in RULE_KEYS
    assert "default_image_quality" in RULE_KEYS
    print("EXECUTION CAPSULE SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("compile"); p.add_argument("episode_dir"); p.add_argument("step",choices=sorted(STEP_EVIDENCE))
    p=sub.add_parser("show"); p.add_argument("episode_dir"); p.add_argument("step",choices=sorted(STEP_EVIDENCE))
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    data=compile_capsule(ep,a.step,write=a.cmd=="compile")
    print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
