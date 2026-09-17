#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys, time, uuid
import codex_user_runner  # STORY_OS_V2_7_CODEX_USER_MODE_BRIDGE
import execution_capsule
import character_contract
import character_visual_contract
import world_identity_contract  # STORY_OS_V221_WORLD_IDENTITY
import character_appearance_anchor  # STORY_OS_V221_CHARACTER_CONTINUITY
import inflight_codex_task  # STORY_OS_V262_INFLIGHT_ATTACH
import resource_library
import intro_policy
import directing_quality
import episode_performance
import storyos_config
import runtime_router
import product_runtime_adapter
import runtime_timeout_policy
import runtime_request
import runtime_memory_advice
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

# The step's previous Codex task produced no usable result inside its own
# deadline. Technical, retryable: nothing about the content failed.
ATTACH_TIMEOUT_RC=26
ATTACH_POLL_SECONDS=5.0

# P0-D real fault injection (2026-09-15) proved that CREATIVE_STORY cannot use
# the rendered prompt as its attach identity: prompt() intentionally prepares
# character/resource/directing helper files before compiling the capsule, so a
# restarted Driver sees different prompt bytes even though the user's question
# did not change.  Keep this list to inputs that exist *before* CREATIVE_STORY and
# are not owned by that step.  Step outputs such as story-gates, concept rows,
# character-contract, resource-selection and directing-quality are deliberately
# absent.
CREATIVE_STORY_ATTACH_ROOT_INPUTS=(
    "config/storyos.yaml",
    "config/profiles/account_creative/default.json",
    "config/profiles/world_identity/default.json",
    "standards/directing_grammar_v1.json",
    "standards/character-pools.json",
    "standards/entry-motivation-pools.json",
    "standards/scene-pools.json",
    "standards/forbidden-character-roles.json",
    "story_os_manifest.json",
    "reports/account-learning-index.json",
)


def _sha_file(path:Path)->str|None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    except OSError:
        return None


def attach_source_sha256(ep:Path,step:str)->str:
    """Stable authority projection used only to decide whether an old task attaches.

    The exact submitted stdin is still pinned independently by the runner result's
    ``stdin_sha256``.  This projection answers the different question: "is the
    business input still the same after the Driver restarted?"  Returning an empty
    string keeps the older exact-prompt/fail-closed identity for steps that do not
    yet have an audited projection.
    """
    ep=Path(ep)
    if step=="CREATIVE_STORY":
        request_path=ep/"meta/runtime-request.json"
        if not request_path.is_file():
            return ""
        request=json.loads(request_path.read_text(encoding="utf-8-sig"))
        state_path=ep/"meta/episode-state.json"
        state=json.loads(state_path.read_text(encoding="utf-8-sig")) if state_path.is_file() else {}
        material={
            "identity_schema_version":2,
            "step":step,
            "current_state":state.get("current_state"),
            "creative_request":runtime_request.preimage_authority_projection(request),
            "directive_sha256":hashlib.sha256(STEP_DIRECTIVES[step].strip().encode("utf-8")).hexdigest(),
            "root_authority":{rel:_sha_file(ROOT/rel) for rel in CREATIVE_STORY_ATTACH_ROOT_INPUTS},
        }
        raw=json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
    return ""

def runtime_index_block(step):
    try:
        config=storyos_config.load_config()
        data=storyos_config.load_index()
        return json.dumps({
            "rules":{
                "read_index_first":storyos_config.get_path(config,"runtime.read_index_first"),
                "recursive_repository_scan_default":storyos_config.get_path(config,"runtime.recursive_repository_scan_default"),
            },
            "required_read":((data.get("stage_read_sets") or {}).get(step) or []),
            "entrypoints":data.get("entrypoints") or {},
        },ensure_ascii=False,indent=2)
    except Exception:return "{}"

STEP_DIRECTIVES={
"CREATIVE_STORY":"""
TARGET: reach STORYBOARD_LOCKED and stop there.
- honor meta/runtime-request.json when present.
- BEFORE concept/story work, read meta/character-contract.json as the Character/Entry/Scene Story Build Input Contract.
- Story OS 2.2.1 World Identity: read the effective default/override through `python episodes/_system/world_identity_contract.py show "<episode>"`. Default is Mainland China + ordinary Chinese young adults. Do not randomly introduce foreign characters/architecture/cultural context. If the Story explicitly specifies another country/culture, author meta/world-identity.json as an explicit override instead of fighting the default.
- default protagonists are ordinary young people from the 2004-2010 or modern-2020s pools; first-person POV still requires a stable character anchor.
- default 4-5 person groups must keep stable member IDs, ages, genders and clothing anchors.
- prefer life-like entry motives: travel, return home, friends hangout, games/drinking, challenge, abandoned place, outdoor trip, casual work, research/expedition, accidental detour.
- NEVER replace the protagonist with a repair worker, electrician, police officer, journalist, investigator, professional ghost hunter or another occupational tool invented to solve the anomaly.
- casual work / research / expedition may explain why the young people arrived, but professional skill must not become the shortcut that solves the anomaly.
- BEFORE STORYBOARD_LOCKED, update meta/character-contract.json to match the final Story, set status=LOCKED, recheck NO-ANOMALY TEST, and run character_contract.py validate --require-locked. Do not advance if it fails.
- auto_create: author the complete story yourself via recent5/account evidence -> 8-12 concepts -> Concept Ambition -> image-first propagation -> Story/Storyboard.
- user_seed: preserve core intent but strengthen/rewrite mechanism, logic, escalation, climax and ending; never mechanically split the seed.
- core_constraints: preserve every hard constraint.
- locked_story: only logic/polish repairs.
- run Story critics/verifiers and honest delegated approval evidence.
- Directing Quality: author and LOCK meta/voice-contract.json; author and LOCK meta/storyboard-density-review.json; run voice_contract.py validate and storyboard_density_gate.py validate. Every frame must pass the delete-frame test and 5-frame progress window.
- Opening Social Anchor: for multi-person travel / return-home / outing stories, strongly prefer Frame 01-02 to show the group in realistic selfie perspective: either vehicle/departure/transit selfie or destination/scenic check-in selfie. Use at least 2 visible people (prefer 3-4), establish relationship/clothing anchors, keep capture casual and imperfect rather than commercial/staged, and keep anomaly absent or only micro-background. Author+LOCK meta/opening-social-anchor.json and run opening_social_anchor.py validate. Solo or structurally incompatible stories may set applicable=false only with a concrete exception_reason.
- Camera-Friendly Ordinary Cast + Anti-Likeness: author+LOCK meta/character-visual-contract.json as IDENTITY SPEC only. Set each locked member face_identity.identity_spec_locked=true; preproduction_only must NOT claim a pixel/image master. Primary leads should be moderately-above-average but believable real young adults; female lead defaults slim/proportionate/natural unless Story requires another build. Keep natural skin texture/asymmetry and explicit original haircut anchors. Real-person references may guide age vibe, attractiveness range, realism, capture style and clothing direction ONLY; never copy exact face geometry, feature combination, personal markers or exact hairstyle. Run character_visual_contract.py validate.
- After Character Visual Contract is LOCKED, build+verify `meta/runtime/contracts/character-appearance-anchor.json` with character_appearance_anchor.py. This is a derived textual identity anchor; it does not replace the later Visual Lock pixel master.
- Account Creative Profile: read config/profiles/account_creative/default.json before concept selection. Treat it as the account's default subject/style memory: ordinary young-adult reality cracks, old-device mysteries, travel/return-home anomalies, mountain mockumentary, folk/archive rules and world-scale anomalies; M00 reality-first visual identity remains default. It guides candidate generation but never overrides an explicit Runtime Request or recent-5 anti-homogeneity evidence.
- Capture Setup + Directing Grammar + Anomaly Logic + Human Response: author+LOCK meta/shot-progression-review.json schema_version=3 for new/unlocked episodes and run shot_progression_gate.py validate. Read standards/directing_grammar_v1.json. Every frame must declare shot_scale + globally unique scene_position_id; the episode needs at least one wide/extreme-wide and one close/detail, at least three shot scales overall, and the same exact capture position may not be reused. Translate at least two suitable classic-cinema shot-structure techniques into diegetic casual capture; never recreate an exact film frame. Every frame declares practical lighting source/contrast/suspense function; no invented cinematic key/rim light. Suspense/strange stories must hide at least one meaningful anomaly through a physically valid mirror, water/glass/wet reflection, fog/mist, light-shadow boundary, screen reflection, foreground occlusion, doorway/window or silhouette before/alongside direct reveal. Same capture setup max 2 consecutive; every 5-frame window needs >=3 setup signatures; anomaly escalation must gain spatial/causal contradiction, human consequence or reversal rather than only more/bigger lights; after confirmation people must progress from observing into verify/discuss/move/act/fail/adapt; Frame 10 must open new evidence/question rather than recap. For every human-present frame, author restrained emotion state/intensity 0..4/causal trigger/response_sync plus interaction type/actor/target/action/meaningful. intensity>=2 needs a real trigger. Multi-person reactions should normally be asynchronous or shared-but-unsynchronized, never theatrical synchronized screaming. For multi-person stories, each run of 5 human-present frames needs at least one meaningful interaction, but interactions must not dominate the whole story. Opening Frame 01/02 social anchor needs at least one natural interaction (selfie, someone talking, adjusting seatbelt/bag/hat, showing a phone, etc.). Wardrobe may participate in causal actions such as pulling a shell zipper, holding a hat in wind, adjusting a backpack or handing a wet jacket.
- advance only to STORYBOARD_LOCKED.
DO NOT create Environment/Impact Contract, Visual Lock images, Batch, subtitles or Release.
""",
"PREIMAGE_COMPILE":"""
TARGET: keep STORYBOARD_LOCKED and finish every non-image asset required for a clean image handoff.
- Story/Storyboard/Character Contract are already locked authority. DO NOT rewrite them.
- resolve shared Resource Library references into meta/resource-selection.json.
- create/verify Environment + Impact Contract and all frame directives.
- compile/verify all Resolved Frame Contracts.
- Before Frame Contract compile, run `python episodes/_system/production_readiness_v221.py "<episode>" --stage preimage` for V2.2.1+ Episodes. World Identity + Character Appearance Anchor must PASS; never weaken the default merely to make generation easier.
- Directing Quality: before Frame Contract compile, author+LOCK meta/capture-event-contract.json and meta/world-state.json. Every frame must explain why it is captured now; sensitive identity/recorder state changes need a story_event. Run capture_event_contract.py validate and world_state.py validate.
- Temporal Continuity: after world-state is authored, author+LOCK meta/temporal-continuity.json bound to world-state SHA. Track elapsed minutes/daypart/weather/precipitation/ambient light. Night↔day or major weather/light jumps require explicit elapsed time + transition_reason. Run temporal_continuity_gate.py validate.
- Scene-Aware Wardrobe: then author+LOCK meta/wardrobe-contract.json bound to temporal continuity. Clothing must follow altitude/temperature/weather/daypart/activity. Sichuan-Tibet/high-altitude cool-cold outdoor defaults shell/fleece/warm trousers/hat; low-altitude warm, vehicle, lodging or county-town scenes may use attractive camisoles/skirts/light layers. Cold outdoor skirt requires thick/thermal tights + warm outer layer; cold high-altitude camisole without warm outer layer is FAIL. Every look_id change needs a believable change_reason. Run wardrobe_contract.py validate.
- STORY_OS_V211_PERF_FINAL_R2: when authoring frame directives, keep `escalation_from` as narrative continuity only. Add `generation_depends_on` only when the current image literally requires a prior generated pixel asset; otherwise use an empty list.
- author concise per-frame production prompt source files required by the existing image scheduler / prompt-package compiler.
- resolve intro policy and allow provisional text-only release drafts.
- DO NOT invoke image_generation, DO NOT create Visual Lock images, DO NOT advance the Episode stage.
Stop only when environment/frame contracts are machine-verifiable and image production can start without story work.
""",
"VISUAL_LOCK":"""
TARGET: reach VISUAL_CALIBRATED and stop there.
- create/verify Environment + Impact Contract.
- compile/verify Resolved Frame Contracts.
- Directing Quality: before Frame Contract compile, author+LOCK meta/capture-event-contract.json and meta/world-state.json. Every frame must explain why it is captured now; sensitive identity/recorder state changes need a story_event. Run capture_event_contract.py validate and world_state.py validate.
- Temporal Continuity: after world-state is authored, author+LOCK meta/temporal-continuity.json bound to world-state SHA. Track elapsed minutes/daypart/weather/precipitation/ambient light. Night↔day or major weather/light jumps require explicit elapsed time + transition_reason. Run temporal_continuity_gate.py validate.
- Scene-Aware Wardrobe: then author+LOCK meta/wardrobe-contract.json bound to temporal continuity. Clothing must follow altitude/temperature/weather/daypart/activity. Sichuan-Tibet/high-altitude cool-cold outdoor defaults shell/fleece/warm trousers/hat; low-altitude warm, vehicle, lodging or county-town scenes may use attractive camisoles/skirts/light layers. Cold outdoor skirt requires thick/thermal tights + warm outer layer; cold high-altitude camisole without warm outer layer is FAIL. Every look_id change needs a believable change_reason. Run wardrobe_contract.py validate.
- use exactly four current V2.1 Visual Lock admissions: ordinary_baseline, worst_capture_condition, first_major_anomaly, high_impact_admission.
- For multi-person travel/return-home/outing stories, the Visual Lock planner machine-prioritizes the valid Frame 01/02 selfie declared by meta/opening-social-anchor.json as ordinary_baseline, with legacy ordinary-frame fallback only when no valid anchor exists.
- execute Visual Lock as a REAL 1+3 barrier: import the four admissions, run the scheduler once so ONLY ordinary_baseline can generate, then inspect that actual baseline image before any other admission is allowed to start.
- After baseline generation, run visual_lock_baseline_gate.py prepare-review. Inspect actual pixels and honestly fill meta/visual-lock-baseline-review.json: all required checks plus normalized primary-character face_boxes. Run visual_lock_baseline_gate.py approve. A PASS creates a PROVISIONAL SHA-bound character pixel master and deterministic individual crops; a FAIL must repair/review baseline and MUST NOT release the parallel three.
- Re-run the scheduler only after baseline approval. The scheduler re-arbitrates references at execution time, and worst_capture_condition / first_major_anomaly / high_impact_admission may then run in parallel with the approved PROVISIONAL baseline identity reference.
- After all four admissions exist, run the normal bind/critic/final Visual Lock review. FOUR-admission PASS promotes the same baseline image from PROVISIONAL to LOCKED pixel master. Real-person style references never become identity masters.
- STORY_OS_V211_PERF_RECOVERY: if the unified critic reports technical infrastructure failure (for example INPUT_IMAGES_UNAVAILABLE / Windows sandbox 1385 / critic return code 11), DO NOT convert that into content failure, DO NOT loop content repairs, and DO NOT mutate candidate decisions to failed. Stop this bounded step promptly and preserve meta/visual-critic-runtime.json; the parent DAG may run bounded speculative production.
- generate/review/repair only those admissions as required.
- use image model policy from meta/runtime-request.json; the default comes from config/storyos.yaml.
- record honest delegated visual approval only after evidence passes.
- advance only to VISUAL_CALIBRATED.
DO NOT run full Batch or release.
""",
"PRODUCTION":"""
TARGET: reach PRODUCTION_PASSED and stop there.
- author concise per-frame prompts for remaining frames.
- STORY_OS_V211_PERF_FINAL_R2: `escalation_from` is narrative-only and MUST NOT serialize image generation. Use `generation_depends_on` only for a true pixel prerequisite (image edit, required prior generated asset, or an explicit locked visual state that cannot be represented by contracts); default it to empty.
- import/run bounded image scheduler, max 3 image jobs. Reference arbitration remains max 2 refs: use locked identity only on character frames, then choose prop/location/capture_style by frame function; individual derived crop is preferred for an explicit single-character subject.
- reuse clean SHA-bound PASS evidence.
- technical failures are retryable and do not consume content repair.
- Fast Scout is triage only; run final incremental semantic review/audit.
- repair only failed dirty frames.
- If Execution Capsule effective_execution_mode=repair_only: override the normal target; process ONLY Repair Queue / dirty / failed frames, never generate untouched originals, never rewrite Story/Storyboard, and do not require state advancement when unrelated originals are still pending.
- advance only to PRODUCTION_PASSED.
DO NOT do subtitles or Release.
""",
"RELEASE":"""
TARGET: reach PUBLISH_READY and stop there.
- resolve meta/intro-policy.json before final copy. The intro opening must use one of the four approved reference families but be naturally rewritten for the actual Story; never mechanically substitute XXX.
- generate exactly one title as an internal candidate only. Title is not required for PUBLISH_READY and is not included in final delivery by default.
- create/audit captions and publish copy/assets from PASS production frames.
- Subtitle placement: inspect each approved base before rendering and author meta/subtitle-layout.json. Prefer the LEFT-MIDDLE safe zone (roughly 42%-62% image height, x=72) and move away only when faces, anomaly evidence, hands/actions, props, native text or causal clues occupy that zone; every outside-zone override needs a concrete safe_zone_override_reason. Never place text over key information.
- Caption writing: first-person conversational immediate-record language, short and eye-catching without clickbait boilerplate; one function per frame; canonical renderer still caps at two lines (stricter than the requested three).
- Use meta/voice-contract.json as narrator authority. Run text_audit.py, then write meta/subtitle-voice-review.json bound to Voice Contract SHA and caption source SHA. continuous-three-frame, read-aloud, delete-subtitle, knowledge-boundary and clue-payoff tests must all PASS.
- complete release/compliance checks.
- build+verify Final Candidate Snapshot. When character master evidence exists, Snapshot must lock master metadata, master image, crop manifest and every derived crop SHA.
- record honest delegated release approval.
- transition only to PUBLISH_READY.
- ZIP is a delivery adapter, not CODEX completion.
DO NOT mark PUBLISHED or fabricate metrics.
"""}

# PREIMAGE protocol split: each invocation is forbidden from writing authority.
# The parent single-writer commit validates the returned candidate separately.
STEP_DIRECTIVES.update({
"PREIMAGE_CHARACTER_FINALIZE": """TARGET: produce only the CHARACTER_FINALIZE Candidate declared by the execution capsule/request. Read the locked Story and Character Seed Contract. Validate final identity, wardrobe baseline, POV and textual appearance anchor. Do not rewrite Story or create pixel masters. Write only the declared candidate JSON; never modify shared authority, episode-state or gates.""",
"PREIMAGE_ENVIRONMENT": """TARGET: produce only the ENVIRONMENT_PREPARE Candidate declared by the execution capsule/request. Cover physical environment, weather, impact and environment frame directives. The candidate must satisfy the Phase-3 Environment Contract before commit: whenever a segment condition implies a different daypart (morning/midday/afternoon/dusk/night), that segment must carry a matching time_of_day instead of inheriting an incompatible baseline. Provide directives for every frame and keep condition/time_of_day physically consistent. Do not change Character, Story, World or other visual authority. Write only the declared candidate JSON; never modify shared authority, episode-state or gates.""",
"PREIMAGE_WORLD": """TARGET: produce only the WORLD_PREPARE Candidate declared by the execution capsule/request. Cover world identity/state, capture-event physical continuity, temporal continuity and wardrobe constraints. Do not rewrite Story or generate images. Write only the declared candidate JSON; never modify shared authority, episode-state or gates.""",
"PREIMAGE_VISUAL_NARRATIVE": """TARGET: produce only the VISUAL_NARRATIVE_PREPARE Candidate declared by the execution capsule/request. Cover visual narrative core, shot progression, capture grammar and anomaly progression. Do not own environment physics or character identity. Write only the declared candidate JSON; never modify shared authority, episode-state or gates.""",
})

def resolve_codex(raw):
    import codex_cli_contract
    return codex_cli_contract.resolve_path(raw)

def prefix(codex):
    import codex_cli_contract
    return codex_cli_contract.command_prefix(codex)

def request_block(ep,step):
    p=ep/"meta/runtime-request.json"
    if not p.is_file(): return "<runtime_request>ABSENT</runtime_request>"
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    if step=="CREATIVE_STORY":
        payload={"creative_request":runtime_request.creative_request_view(data)}
    else:
        payload=runtime_request.partitioned_view(data)
    return "<runtime_request>\n"+json.dumps(payload,ensure_ascii=False,indent=2)+"\n</runtime_request>"

def prompt(ep,step):
    rel=ep.relative_to(ROOT).as_posix()
    if step=="CREATIVE_STORY":
        directing_quality.enable(ep)
        character_contract.prepare(ep,force=False)
        character_visual_contract.prepare(ep,force=False)
        resource_library.resolve(ep,write=True)
    if step in {"PREIMAGE_COMPILE","VISUAL_LOCK"}:
        resource_library.resolve(ep,write=True)
    if step=="RELEASE":
        intro_policy.resolve(ep,write=True)
    capsule=execution_capsule.compile_capsule(ep,step,write=True)
    return f"""You are a bounded Story OS V2.1 scoped worker for exactly {rel}.
Use the derived Execution Capsule first; do NOT reread the entire repository policy stack by default.
Open authoritative source files listed by the capsule only when details are missing or a conflict must be resolved.
Do not spawn another full-auto supervisor. Do not perform downstream work beyond this step.
Reuse valid SHA-bound evidence. Never fabricate PASS/review/user approval.
Reality constrains capture behavior, not concept ambition.
Read the embedded FAST_RUNTIME_INDEX first. Do NOT recursively scan the repository while its declared read set + Execution Capsule are sufficient. Broaden only for a missing dependency or real conflict.

<FAST_RUNTIME_INDEX>
{runtime_index_block(step)}
</FAST_RUNTIME_INDEX>

<EXECUTION_CAPSULE>
{json.dumps(capsule,ensure_ascii=False,indent=2)}
</EXECUTION_CAPSULE>

{request_block(ep,step)}

{runtime_memory_advice.prompt_block(ep) if step=="CREATIVE_STORY" else ""}

<SCOPED_STEP id="{step}">
{STEP_DIRECTIVES[step].strip()}
</SCOPED_STEP>

Stop when the bounded target is reached. The parent runtime independently verifies all gates.
"""

def _attach(ep,step,text,timeout,log,poll_seconds=None):
    """Claim a Codex result a dead Driver already paid for, or wait for it.

    Returns (rc, handled). ``handled`` is False when there is nothing to attach
    to and the caller should submit a new task.

    A result is only ever adopted through inflight_codex_task.validate_result,
    which requires rc=0, matching request_id, matching stdin SHA and an output
    that hashes to its own recorded digest. Anything else is treated as no result
    at all, so a half-written or drifted file cannot close a step.
    """
    if not codex_user_runner.bridge_required():
        return None,False
    source_sha=attach_source_sha256(ep,step)
    fp=inflight_codex_task.fingerprint(step=step,prompt=text,source_sha256=source_sha)
    verdict=inflight_codex_task.classify(ep,step=step,fingerprint_value=fp)
    if verdict["decision"]==inflight_codex_task.ADOPT:
        with log.open("ab") as h:
            h.write(verdict["output"])
        # The paid task is no longer in-flight once its durable result has been
        # adopted.  Leaving the record behind makes a later Driver cycle adopt
        # the same business result forever, so a downstream gate failure can
        # never progress into a real repair submission.
        inflight_codex_task.clear(ep,step)
        return int(verdict["returncode"]),True
    if verdict["decision"]!=inflight_codex_task.WAIT:
        return None,False
    # The task is still running under the resident user-mode runner. Submitting
    # the same step again would run it twice, so wait for the result the dead
    # Driver's call would have received instead.
    record=verdict.get("record") or {}
    deadline=_deadline_epoch(record)
    poll=ATTACH_POLL_SECONDS if poll_seconds is None else max(0.0,float(poll_seconds))
    print(f"ATTACH {step} request_id={record.get('request_id')} "
          f"reason={verdict['reason']} validation={verdict.get('validation')}",flush=True)
    while True:
        if deadline is not None and time.time()>=deadline:
            return ATTACH_TIMEOUT_RC,True
        if poll:
            time.sleep(poll)
        again=inflight_codex_task.classify(ep,step=step,fingerprint_value=fp)
        if again["decision"]==inflight_codex_task.ADOPT:
            with log.open("ab") as h:
                h.write(again["output"])
            inflight_codex_task.clear(ep,step)
            return int(again["returncode"]),True
        if again["decision"]==inflight_codex_task.RESUBMIT and again.get("reason")!="WITHIN_TASK_DEADLINE":
            # The task is provably gone and left nothing usable behind.
            return None,False
        if not poll:
            return ATTACH_TIMEOUT_RC,True


def _deadline_epoch(record):
    raw=str(record.get("deadline_at") or "")
    if not raw:
        return None
    try:
        return datetime.datetime.fromisoformat(raw).timestamp()
    except (TypeError,ValueError):
        return None


def run_step(ep,step,codex_raw=None,timeout=None,attach_poll_seconds=None):
    if step not in STEP_DIRECTIVES: raise ValueError(f"unknown scoped step: {step}")
    if timeout is None:
        timeout = runtime_timeout_policy.seconds("codex_scoped_step")
    perf_run=episode_performance.safe_begin_stage(ep,step,source="scoped_codex_worker")
    rc=99;log=ep/"meta/scoped-workers"/f"{step.lower()}.jsonl";log.parent.mkdir(parents=True,exist_ok=True)
    text=prompt(ep,step)
    if not runtime_router.local_codex_allowed(explicit=bool(codex_raw)):
        runtime,_=runtime_router.detect()
        request=product_runtime_adapter.build_request(
            ep,runtime=runtime,mode="full_auto",resume=True,source=f"scoped_codex_worker:{step}")
        log.write_text(json.dumps({"status":"HOST_ACTION_REQUIRED","request":request},ensure_ascii=False)+"\n",encoding="utf-8")
        episode_performance.safe_end_stage(ep,step,perf_run,status="HOST_ACTION_REQUIRED",
                                           metadata={"timeout_seconds":timeout,"log":str(log)})
        return product_runtime_adapter.HOST_ACTION_REQUIRED_RC,str(log)
    attached,handled=_attach(ep,step,text,timeout,log,poll_seconds=attach_poll_seconds)
    if handled:
        rc=int(attached)
        episode_performance.safe_end_stage(ep,step,perf_run,status="PASS" if rc==0 else f"RC_{rc}",
                                           metadata={"timeout_seconds":timeout,"log":str(log),"attached":True})
        return rc,str(log)
    request_id=None
    collected=False
    try:
        codex=resolve_codex(codex_raw)
        cmd=prefix(codex)+["exec","--skip-git-repo-check","--ephemeral","-s","workspace-write","-C",str(ROOT),"--json","-"]
        request_id=uuid.uuid4().hex if codex_user_runner.bridge_required() else None
        if request_id:
            # Written before submission on purpose: a record written afterwards
            # would be missing in exactly the case it exists for.
            inflight_codex_task.begin(
                ep,step=step,request_id=request_id,
                fingerprint_value=inflight_codex_task.fingerprint(
                    step=step,prompt=text,source_sha256=attach_source_sha256(ep,step)),
                stdin_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                timeout_seconds=int(timeout),
                source_sha256=attach_source_sha256(ep,step))
        with log.open("a",encoding="utf-8",newline="\n") as h:
            try:
                cp=codex_user_runner.run_codex(cmd,input=text,text=True,encoding="utf-8",stdout=h,stderr=subprocess.STDOUT,timeout=timeout,check=False,task_type="scoped_step",request_id=request_id)
                rc=cp.returncode; collected=True
            except subprocess.TimeoutExpired:
                rc=124; collected=True
        return rc,str(log)
    finally:
        # Only a collected outcome clears the record. If this process dies while
        # the task runs, the record stays and the next Driver attaches instead of
        # paying for the step again.
        if collected and request_id:
            inflight_codex_task.clear(ep,step)
        episode_performance.safe_end_stage(ep,step,perf_run,status="PASS" if rc==0 else f"RC_{rc}",
                                           metadata={"timeout_seconds":timeout,"log":str(log)})

def self_test():
    assert {"CREATIVE_STORY","PREIMAGE_COMPILE","PREIMAGE_ENVIRONMENT","PREIMAGE_WORLD","PREIMAGE_CHARACTER_FINALIZE","PREIMAGE_VISUAL_NARRATIVE","VISUAL_LOCK","PRODUCTION","RELEASE"}.issubset(STEP_DIRECTIVES)
    print("SCOPED CODEX WORKER SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("run"); p.add_argument("episode_dir"); p.add_argument("step",choices=sorted(STEP_DIRECTIVES)); p.add_argument("--codex"); p.add_argument("--timeout",type=int,default=None)
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve(); rc,log=run_step(ep,a.step,codex_raw=a.codex,timeout=runtime_timeout_policy.resolve("codex_scoped_step", a.timeout))
    print(json.dumps({"step":a.step,"returncode":rc,"log":log},ensure_ascii=False)); return rc

if __name__=="__main__": raise SystemExit(main())

# STORY_OS_V211_RUNTIME_CLOSURE_R31
