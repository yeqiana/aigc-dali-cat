#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Production Orchestrator (Autonomous Production Pipeline Phase 5.2 + 5.5 + 5.6).

Purpose:
    One sentence story request -> a Production Plan that wires the existing
    modules together:

        story_intent_parser      one sentence -> Story Intent Contract
        visual_profile_selector  Story Intent -> registered profile + evidence
        story_creator            Episode skeleton + Visual Lock draft
        visual_profile_lock_*    human confirmation (later, by a person)
        frame_contract           per frame contracts (later)
        image_scheduler          production (later, not started here)
        auto_review_loop         rule review of evidence (later)
        repair_engine            repair tasks from review issues (later)

Two entry points, one chain
---------------------------
``plan``           reports what would happen and stops at the human gates. This stays the
                   debug / dry-run / planning view.
``run_full_auto``  is the wiring behind ``story_os.py create "..." --full-auto``: Story Intent
                   -> Episode -> Visual Lock -> the canonical Runtime DAG (workflow_runner +
                   runtime_dag + image_scheduler) -> auto_review_loop -> repair_engine -> the
                   canonical repair lane -> Release Candidate. It is deliberately the only
                   production orchestrator: there is no second runtime, scheduler, ledger,
                   Review/Repair rule set or episode state machine behind it.

Boundaries
----------
- ``run_full_auto`` never produces an image itself, never writes episode-state.json,
  production-ledger.json, the Visual Lock, the Frame Contracts or the Story Lock, and it never
  records an approval. Success is the canonical stage reaching PUBLISH_READY, not a worker
  exit code.
- Orchestration only. This module composes existing modules; it never replaces
  Runtime DAG, workflow_runner or story_os.py, and it does not reimplement any
  selection, contract or gate rule.
- No image production, no scheduler run, no batch run.
- The plan always stops at two human gates: the Visual Lock confirmation and the
  Story Lock. An Episode is never treated as production ready by this module.
- Selection failure fails closed: an unregistered forced profile or an invalid
  selector input raises instead of creating a half planned Episode.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    # Repo convention is script execution (python episodes/_system/x.py). The same
    # module is also runnable as python -m episodes._system.x, which puts the
    # repository root on sys.path instead, so both entry points are kept working.
    sys.path.insert(0, str(_HERE))

import auto_review_loop  # noqa: E402
import repair_engine  # noqa: E402
import story_creator  # noqa: E402
import story_intent_parser  # noqa: E402
import story_json  # noqa: E402
import runtime_request as runtime_request_contract  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_lock_lifecycle as lifecycle  # noqa: E402
import visual_profile_selector  # noqa: E402
from story_os_contract import canonical_stages  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

ORCHESTRATOR_VERSION = "1.0"
DEFAULT_FRAME_COUNT = 20

STATUS_PLANNED = "planned"
STATUS_NEEDS_CONFIRMATION = "needs_confirmation"
STATUS_REJECTED = "rejected"

ERROR_SELECTION_REJECTED = "ORCHESTRATOR_SELECTION_REJECTED"
ERROR_PLAN_INVALID = "ORCHESTRATOR_PLAN_INVALID"

EPISODE_STATE_REL = Path("meta/episode-state.json")
LOCK_REL = adapter.LOCK_REL

# Declared pipeline, in execution order. "later" stages are owned by other
# modules and are deliberately not started by Phase 5.
PIPELINE = (
    ("story_intent", "done", "story_intent_parser"),
    ("episode_bootstrap", "done", "story_creator"),
    ("visual_profile_selection", "done", "visual_profile_selector"),
    ("visual_lock_confirmation", "human_gate", "visual_profile_lock_lifecycle"),
    ("story_lock", "human_gate", None),
    ("frame_planning", "not_started", "frame_contract"),
    ("image_production", "not_started", "image_scheduler"),
    ("review", "not_started", "auto_review_loop"),
    ("repair", "not_started", "repair_engine"),
    ("release", "not_started", "release_package"),
)

# --------------------------------------------------------------------------- #
# Phase 5.6: canonical one sentence full-auto integration
# --------------------------------------------------------------------------- #

FULL_AUTO_VERSION = "1.0"
STATUS_DOC_REL = Path("meta/runtime/full-auto-status.json")
WORKFLOW_SCRIPT = "workflow_runner.py"
CHECKPOINT_SCRIPT = "runtime_checkpoint.py"
FRAME_CONTRACT_SCRIPT = "frame_contract.py"

# The one status vocabulary the full-auto entry reports. Success is STATUS_PUBLISH_READY
# and nothing else; RUNNING only means the canonical host still owns pending work.
FULL_AUTO_STATUS_PLANNED = "PLANNED"
FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED = "HUMAN_GATE_REQUIRED"
FULL_AUTO_STATUS_RUNNING = "RUNNING"
FULL_AUTO_STATUS_REPAIRING = "REPAIRING"
FULL_AUTO_STATUS_NEEDS_USER = "NEEDS_USER"
FULL_AUTO_STATUS_PUBLISH_READY = "PUBLISH_READY"
FULL_AUTO_STATUS_FAILED = "FAILED"
FULL_AUTO_STATUSES = (
    FULL_AUTO_STATUS_PLANNED,
    FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED,
    FULL_AUTO_STATUS_RUNNING,
    FULL_AUTO_STATUS_REPAIRING,
    FULL_AUTO_STATUS_NEEDS_USER,
    FULL_AUTO_STATUS_PUBLISH_READY,
    FULL_AUTO_STATUS_FAILED,
)

# Delegated confirmation is only the Phase 4.2 mode vocabulary applied to the Selector's
# already deterministic choice. It is never a fabricated direct user approval.
DELEGATED_CONFIRMATION_ACTOR = "story_os:full-auto"
DELEGATED_CONFIRMATION_REASON = (
    "story_os.py create --full-auto: delegated auto confirmation of the Selector's Visual Profile")

# Runtime owned repair tasks that map onto an existing canonical repair lane.
REPAIR_DISPATCH_ACTIONS = (
    repair_engine.ACTION_REGENERATE_FRAME,
    repair_engine.ACTION_REBIND_FRAME_CONTRACT,
)


class ProductionOrchestratorError(SystemExit):
    """Fail-fast orchestrator error (shares the registry SystemExit convention)."""

    code = ERROR_PLAN_INVALID

    def __init__(self, message, code=None):
        self.code = code or self.code
        super().__init__(self.code + ": " + str(message))


def _root(story_root=None) -> Path:
    return Path(story_root) if story_root else ROOT


def _rel(path: Path, root: Path):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def plan(
    root,
    idea,
    *,
    title=None,
    frames: int = DEFAULT_FRAME_COUNT,
    forced_profile_id=None,
    episode_context=None,
    dry_run: bool = False,
    story_root=None,
) -> dict:
    """Compile a one sentence request into a Production Plan.

    dry_run=True stops after selection: the intent and the Selector decision are
    computed but nothing is written, which is the review mode for this phase.
    Otherwise the Episode skeleton and its Visual Lock *draft* are written exactly
    the way Phase 4.1 writes them; a plan is never a lock and never a render.
    """
    repo = _root(story_root or root)
    intent = story_intent_parser.parse(idea, story_root=repo)
    payload = story_intent_parser.selector_input(
        intent, forced_profile_id=forced_profile_id, episode_context=episode_context)
    output = visual_profile_selector.select(payload, story_root=repo, strict=True)

    if output["status"] == visual_profile_selector.STATUS_REJECTED:
        raise ProductionOrchestratorError(
            "the Selector rejected this request; no plan may be produced: "
            + json.dumps(output.get("evidence", {}), ensure_ascii=False),
            ERROR_SELECTION_REJECTED,
        )

    episode_title = str(title or idea).strip() or intent["source_text"]
    episode_id = story_creator.slugify(episode_title)
    episode_rel = (Path("episodes") / episode_id).as_posix()

    candidates = [
        str(candidate.get("profile"))
        for candidate in (output.get("candidates") or [])
        if isinstance(candidate, dict) and candidate.get("profile")
    ]

    created = False
    if dry_run:
        draft = adapter.create_visual_lock_draft(payload, output, story_root=repo)
        profile_id = str(draft.get("profile_id") or "")
        lifecycle_state = str(draft.get("lifecycle_state") or "")
        lock_path = None
    else:
        episode_dir = story_creator.create_episode(root, episode_title, selector_input=payload)
        episode_rel = _rel(Path(episode_dir), Path(root))
        lock, _source = adapter.read_lock(episode_dir)
        profile_id = str((lock or {}).get("profile_id") or "")
        lifecycle_state = str(adapter.lifecycle_of_lock(lock) or "")
        lock_path = LOCK_REL.as_posix()
        created = True

    needs_confirmation = lifecycle_state == adapter.LIFECYCLE_NEEDS_CONFIRMATION
    status = STATUS_NEEDS_CONFIRMATION if needs_confirmation else STATUS_PLANNED

    actions = []
    if needs_confirmation:
        actions.append({
            "step": "adjudicate_visual_profile",
            "owner": "human",
            "candidates": candidates,
            "api": "visual_profile_lock_lifecycle.confirm_visual_lock"
                   "(<episode_dir>, confirmed_by=<name>, confirmed_at=<iso>, "
                   "profile_id=<one of the candidates>, reason=<why>)",
            "reason": "the Selector found more than one eligible profile and never guesses",
        })
    actions.append({
        "step": "confirm_visual_lock",
        "owner": "human",
        "api": "visual_profile_lock_lifecycle.confirm_visual_lock"
               "(<episode_dir>, confirmed_by=<name>, confirmed_at=<iso>, reason=<why>)",
        "reason": "a Visual Lock draft never enters production unconfirmed",
    })
    actions.append({
        "step": "story_lock",
        "owner": "human",
        "api": None,
        "reason": "the Story Lock is human owned; this orchestrator never writes it",
    })
    actions.append({
        "step": "frame_planning",
        "owner": "runtime",
        "api": "frame_contract",
        "reason": "per frame contracts are compiled from the locked story",
    })
    actions.append({
        "step": "production",
        "owner": "runtime",
        "api": "image_scheduler",
        "reason": "out of scope for Phase 5: the plan stops at the human gates",
    })
    actions.append({
        "step": "review_then_repair",
        "owner": "runtime",
        "api": "auto_review_loop.review -> repair_engine.plan_repairs",
        "reason": "review reports evidence gaps; repair only proposes tasks",
    })

    plan_doc = {
        "schema_version": 1,
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "status": status,
        "idea": intent["source_text"],
        "title": episode_title,
        "episode_id": episode_id,
        "episode_dir": episode_rel,
        "created": created,
        "dry_run": bool(dry_run),
        "story_intent": intent,
        "visual_profile": {
            "status": output["status"],
            "profile_id": profile_id or None,
            "candidates": candidates,
            "lifecycle_state": lifecycle_state or None,
            "lock_path": lock_path,
            "confirmed": False,
            "locked": False,
            "selection_evidence_digest": (output.get("evidence") or {}).get("inputs_digest"),
        },
        "story_lock": {"state": "IDEA_LOCKED", "path": None, "status": "pending_confirmation"},
        "frames": {"count": int(frames), "planned": False, "source": "orchestrator_default"},
        "pipeline": [
            {"stage": stage, "status": state, "module": module}
            for stage, state, module in PIPELINE
        ],
        "next_actions": actions,
        "guards": {
            "human_confirmation_required": True,
            "unattended_production": False,
            "mutates_runtime": False,
            "mutates_episode_state_machine": False,
        },
        "notes": [
            "report only: this plan does not start image production",
            "the Visual Lock is a draft until a person confirms it",
        ],
    }
    if needs_confirmation:
        plan_doc["notes"].append(
            "the Selector returned needs_confirmation; no profile is named until a person adjudicates")
    return plan_doc


def format_plan(plan_doc: dict) -> str:
    """Human readable summary used by the CLI (and by the phase report)."""
    visual = plan_doc.get("visual_profile") or {}
    lines = [
        "Production Plan Created",
        "",
        "Episode:        " + str(plan_doc.get("episode_id"))
        + ("   (" + str(plan_doc.get("episode_dir")) + ")" if plan_doc.get("created") else ""),
        "Status:         " + str(plan_doc.get("status")),
        "Visual Profile: " + str(visual.get("profile_id") or "(not selected)")
        + "   draft=" + str(visual.get("lifecycle_state") or "?")
        + "   locked=False",
        "Candidates:     " + (", ".join(visual.get("candidates") or []) or "-"),
        "Frames:         " + str((plan_doc.get("frames") or {}).get("count"))
        + " (not planned yet)",
        "Story Lock:     " + str((plan_doc.get("story_lock") or {}).get("status")),
    ]
    if plan_doc.get("dry_run"):
        lines.append("Mode:           dry run (nothing written)")
    lines.append("")
    lines.append("Next Step: " + ("Adjudicate / Confirm"
                                  if plan_doc.get("status") == STATUS_NEEDS_CONFIRMATION
                                  else "Review / Confirm"))
    lines.append("")
    for index, action in enumerate(plan_doc.get("next_actions") or [], start=1):
        detail = action.get("api") or "-"
        lines.append("  " + str(index) + ". " + str(action.get("step"))
                     + " [" + str(action.get("owner")) + "] " + str(detail))
        if action.get("candidates"):
            lines.append("     candidates: " + ", ".join(action["candidates"]))
    lines.append("")
    lines.append("  unattended production: not enabled (human gates stay in place)")
    return chr(10).join(lines)


# --------------------------------------------------------------------------- #
# Phase 5.6: the canonical one sentence full-auto run
# --------------------------------------------------------------------------- #

def _stage_index(stage):
    """Index of a canonical stage, or None when the Episode declares no legal stage."""
    stages = canonical_stages()
    value = str(stage or "").strip()
    return stages.index(value) if value in stages else None


def _read_stage(episode):
    """Read the only stage authority: meta/episode-state.json."""
    data = story_json.read_json(Path(episode) / EPISODE_STATE_REL, default={})
    return str((data or {}).get("current_state") or "").strip() or None


def _profile_id_of(lock) -> str:
    return str((lock or {}).get("profile_id") or "").strip()


def _ensure_canonical_runtime_request(episode, idea, episode_title) -> dict:
    """Ensure the one-sentence full-auto Episode carries the canonical Runtime Request.

    story_creator historically wrote a small bootstrap request containing only the
    Episode intent and visual-profile metadata. workflow_runner consumes the canonical
    runtime_request contract instead. A valid existing request is immutable and reused;
    only a missing/invalid bootstrap document is replaced before the first workflow
    execution. Visual-profile provenance already written by the bootstrap is preserved.
    """
    episode = Path(episode)
    path = episode / "meta/runtime-request.json"
    existing = story_json.read_json(path, default={})
    if isinstance(existing, dict) and existing:
        try:
            if not runtime_request_contract.validate_request(existing):
                return existing
        except Exception:
            pass

    compile_text = "全自动做一篇「" + str(episode_title) + "」。"
    canonical = runtime_request_contract.compile_request(compile_text)
    canonical["topic"]["title"] = str(episode_title)
    canonical["provenance"]["original_request"] = str(idea).strip()
    if isinstance(existing, dict):
        for key in ("visual_profile", "visual_profile_resolution", "visual_profile_selection"):
            if key in existing:
                canonical[key] = existing[key]
    errors = runtime_request_contract.validate_request(canonical)
    if errors:
        raise ProductionOrchestratorError(
            "canonical Runtime Request correction failed: " + "; ".join(errors),
            ERROR_PLAN_INVALID,
        )
    story_json.write_json(path, canonical)
    return canonical


def _run_canonical_workflow(episode, *, resume: bool, timeout=None) -> int:
    """Forward the Episode to the canonical Runtime DAG and return its exit code.

    A thin hand-off to workflow_runner.py (Runtime DAG -> image_scheduler). No second
    runtime, scheduler or host loop lives here; this single function is what a test
    replaces when it needs to observe the hand-off without a model host.
    """
    mode = "resume" if resume else "run"
    cmd = [sys.executable, str(_HERE / WORKFLOW_SCRIPT), mode, str(episode), "--full-auto"]
    if timeout is not None:
        cmd += ["--timeout", str(int(timeout))]
    return subprocess.call(cmd, cwd=ROOT)


def _authorize_full_auto(episode, *, runtime=None) -> tuple:
    """Record, then read back, the canonical delegated execution authorization.

    Reuses runtime_checkpoint.py init --full-auto -- the very record
    delegated_approval.authorized and evidence_gate already consume. A Visual Lock is
    never confirmed on the strength of a CLI flag alone, and no approval document is
    written here: this only states that continuous execution was explicitly authorized.
    """
    episode = Path(episode)
    resolved = str(runtime or "").strip()
    if not resolved:
        try:
            import runtime_router  # local: keep the module import light

            resolved, _reason = runtime_router.detect()
        except Exception:
            resolved = ""
    resolved = resolved if resolved in {"CODEX", "WORK", "WEB"} else "WORK"
    cmd = [sys.executable, str(_HERE / CHECKPOINT_SCRIPT), "init", str(episode),
           "--runtime", resolved, "--full-auto"]
    completed = subprocess.run(cmd, cwd=ROOT, check=False, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    if completed.returncode != 0:
        return False, "runtime checkpoint init failed rc=" + str(completed.returncode)
    import delegated_approval  # local: keep the module import light

    return delegated_approval.authorized(episode)


def _repair_budget(root, override=None) -> int:
    """Repair rounds the full-auto loop may spend, from the canonical production config."""
    if override is not None:
        return max(0, int(override))
    try:
        import storyos_config  # local: keep the module import light

        config = storyos_config.load_config()
        return max(1, int(storyos_config.get_path(
            config, "production.max_content_repairs_per_frame", 1)))
    except Exception:
        return 1


def _run_frame_contract_compile_all(episode) -> int:
    """Rebuild the derived Frame Contract cache through the canonical script."""
    return subprocess.call([sys.executable, str(_HERE / FRAME_CONTRACT_SCRIPT), "compile-all",
                            str(episode)], cwd=ROOT)


def _dispatch_repairs(episode, tasks) -> dict:
    """Send runtime owned repair tasks down the existing canonical repair lanes.

    regenerate_frame reuses the production ledger single content-repair authorization
    (batch_repair_arbiter -> production_ledger.py review --decision repair), the same gate
    image_scheduler.py already obeys. rebind_frame_contract rebuilds the derived Frame
    Contract cache with the canonical script. Nothing here writes an authority document.
    """
    import batch_repair_arbiter  # local: keep the module import light

    dispatched = []
    blocked = []
    for task in tasks:
        action = str(task.get("action") or "")
        frame = str(task.get("target") or "")
        reason = "; ".join(str(item) for item in (task.get("reasons") or [])) or action
        if action == repair_engine.ACTION_REGENERATE_FRAME and frame.isdigit():
            ok, message = batch_repair_arbiter.authorize_single_repair(
                Path(episode), int(frame), reason)
            row = {"task_id": task.get("task_id"), "action": action, "frame": frame,
                   "authorized": bool(ok), "message": str(message)[-400:]}
            (dispatched if ok else blocked).append(row)
        elif action == repair_engine.ACTION_REBIND_FRAME_CONTRACT:
            rc = _run_frame_contract_compile_all(episode)
            row = {"task_id": task.get("task_id"), "action": action, "frame": frame,
                   "authorized": rc == 0, "rc": rc}
            (dispatched if rc == 0 else blocked).append(row)
        else:
            blocked.append({"task_id": task.get("task_id"), "action": action, "frame": frame,
                            "authorized": False, "message": "no canonical automatic lane"})
    return {"dispatched": dispatched, "blocked": blocked}


def _next_action(episode) -> dict:
    """Read the canonical derived next action; an unavailable derivation is empty."""
    try:
        import next_action  # local: keep the module import light

        return next_action.write(Path(episode))
    except Exception:
        return {}


def _final_gate(episode, target) -> list:
    """Canonical machine_gate verdict for the stage the Episode claims.

    meta/episode-state.json holds the stage, but only the canonical machine_gate
    decides whether that claim is backed by evidence. Only FAIL findings count, the
    same rule machine_gate's own CLI uses; a non-empty list means the orchestrator
    must not report success.
    """
    try:
        import machine_gate  # local: keep the module import light

        findings = machine_gate.validate(Path(episode), str(target))
    except Exception as exc:
        return ["machine_gate_error:" + type(exc).__name__]
    return [str(getattr(item, "code", item)) for item in findings or []
            if str(getattr(item, "level", "FAIL")).upper() == "FAIL"]


def _intent_summary(intent) -> str:
    parts = []
    for key in ("world", "era", "location", "theme", "fantasy_level", "experience_type"):
        value = str((intent or {}).get(key) or "").strip()
        if value:
            parts.append(key + "=" + value)
    return " ".join(parts) or "unspecified"


def _profile_summary(selection, lifecycle_state, profile_id) -> str:
    named = str(profile_id or "").strip() or "(not selected)"
    status = str((selection or {}).get("status") or "").strip() or "unknown"
    state = str(lifecycle_state or "").strip() or "unmanaged"
    return named + " (" + status + "/" + state + ")"


def _story_lock_summary(stage_index) -> str:
    if stage_index is None:
        return "unknown"
    locked = _stage_index("STORYBOARD_LOCKED")
    return "locked" if locked is not None and stage_index >= locked else "pending_confirmation"


def _release_summary(stage_index) -> str:
    if stage_index is None:
        return "unknown"
    ready = _stage_index("PUBLISH_READY")
    return "reached" if ready is not None and stage_index >= ready else "not_reached"


def _candidates(selection) -> list:
    return [str(item.get("profile")) for item in (selection or {}).get("candidates") or []
            if isinstance(item, dict) and item.get("profile")]


def _emit(root, episode_dir, *, status, intent, selection, profile_id, lifecycle_state,
          stage, created, production, review, repair, workflow=None, repair_tasks=None,
          repair_rounds=0, dry_run=False, notes=None) -> dict:
    """Build (and, for a real run, persist) the structured full-auto status document."""
    index = _stage_index(stage)
    document = {
        "schema_version": 1,
        "full_auto_version": FULL_AUTO_VERSION,
        "status": status,
        "episode_dir": _rel(Path(episode_dir), Path(root)),
        "story_intent": _intent_summary(intent),
        "visual_profile": _profile_summary(selection, lifecycle_state, profile_id),
        "visual_lock": str(lifecycle_state or "").strip() or "unmanaged",
        "story_lock": _story_lock_summary(index),
        "current_stage": str(stage or "").strip() or "NO_STATE",
        "production": production,
        "review": review,
        "repair": repair,
        "release": _release_summary(index),
        "created": bool(created),
        "dry_run": bool(dry_run),
        "written": False,
        "story_intent_detail": intent,
        "visual_profile_selection": {
            "status": (selection or {}).get("status"),
            "profile_id": profile_id or None,
            "candidates": _candidates(selection),
            "evidence_digest": ((selection or {}).get("evidence") or {}).get("inputs_digest"),
        },
        "workflow": workflow or {"invoked": False},
        "repair_tasks": list(repair_tasks or []),
        "repair_rounds": int(repair_rounds),
        "authority": {
            "stage_source": EPISODE_STATE_REL.as_posix(),
            "derived": True,
            "mutates_episode_state_machine": False,
            "success_condition": "canonical stage == PUBLISH_READY",
        },
        "notes": list(notes or []),
    }
    if dry_run:
        document["written"] = False
        return document
    try:
        story_json.write_json(Path(episode_dir) / STATUS_DOC_REL, document)
    except Exception as exc:  # a reporting failure never changes the production outcome
        document["notes"].append("status document not written: " + type(exc).__name__)
        return document
    document["written"] = True
    return document


def run_full_auto(root, idea, *, title=None, frames: int = DEFAULT_FRAME_COUNT,
                  forced_profile_id=None, episode_context=None, full_auto: bool = False,
                  resume: bool = False, dry_run: bool = False, story_root=None,
                  timeout=None, max_repair_rounds=None, runtime=None) -> dict:
    """One sentence -> the canonical chain, reusing the existing modules end to end.

    Story Intent -> Episode -> Visual Lock -> workflow_runner (Runtime DAG +
    image_scheduler) -> auto_review_loop -> repair_engine -> the canonical repair lane ->
    Release Candidate. It never produces an image, never writes episode-state.json, the
    production ledger, the Visual Lock, the Frame Contracts or the Story Lock, and it never
    records an approval. It stops when the canonical stage is PUBLISH_READY, when a human
    decision is genuinely required, or when the configured repair budget is exhausted.
    """
    repo = _root(story_root or root)
    intent = story_intent_parser.parse(idea, story_root=repo)
    payload = story_intent_parser.selector_input(
        intent, forced_profile_id=forced_profile_id, episode_context=episode_context)
    selection = visual_profile_selector.select(payload, story_root=repo, strict=True)
    if selection["status"] == visual_profile_selector.STATUS_REJECTED:
        raise ProductionOrchestratorError(
            "the Selector rejected this request; nothing may be produced: "
            + json.dumps(selection.get("evidence", {}), ensure_ascii=False),
            ERROR_SELECTION_REJECTED,
        )

    episode_title = str(title or idea).strip() or intent["source_text"]
    episode_dir = Path(root) / "episodes" / story_creator.slugify(episode_title)

    if dry_run:
        draft = adapter.create_visual_lock_draft(payload, selection, story_root=repo)
        draft_state = str(draft.get("lifecycle_state") or "")
        notes = [
            "dry run: the Episode, the Visual Lock and the status document were not written",
            "workflow.command is the exact canonical call the real run would forward to",
        ]
        if draft_state == adapter.LIFECYCLE_NEEDS_CONFIRMATION:
            # A dry run still tells the truth about the gate: a real run would stop here.
            notes.append("the Selector returned needs_confirmation; a real run would stop at "
                         "HUMAN_GATE_REQUIRED and start no production")
        return _emit(
            root, episode_dir,
            status=(FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED
                    if draft_state == adapter.LIFECYCLE_NEEDS_CONFIRMATION
                    else FULL_AUTO_STATUS_PLANNED),
            intent=intent, selection=selection,
            profile_id=str(draft.get("profile_id") or ""),
            lifecycle_state=draft_state, stage=None, created=False,
            production="not_started", review="not_run", repair="not_run", dry_run=True,
            workflow={"invoked": False, "script": WORKFLOW_SCRIPT,
                      "command": [sys.executable, WORKFLOW_SCRIPT, "run",
                                  episode_dir.as_posix(), "--full-auto"]},
            notes=notes,
        )

    created = False
    if not (episode_dir / EPISODE_STATE_REL).is_file():
        if resume:
            raise ProductionOrchestratorError(
                "resume requested but no Episode state exists at " + episode_dir.as_posix(),
                ERROR_PLAN_INVALID)
        story_creator.create_episode(root, episode_title, selector_input=payload)
        created = True

    story_creator.ensure_episode_core_documents(
        Path(root), episode_dir, episode_title,
        profile_id=str(selection.get("selected_profile") or "") or None,
        frame_count=frames,
    )
    _ensure_canonical_runtime_request(episode_dir, idea, episode_title)

    lock, _lock_source = adapter.read_lock(episode_dir)
    lock_state = str(adapter.lifecycle_of_lock(lock) or "")
    stage = _read_stage(episode_dir)

    def halted(status, note, extra_notes=None):
        return _emit(
            root, episode_dir, status=status, intent=intent, selection=selection,
            profile_id=_profile_id_of(lock), lifecycle_state=lock_state, stage=stage,
            created=created, production="not_started", review="not_run", repair="not_run",
            notes=[note] + list(extra_notes or []))

    if lock_state == adapter.LIFECYCLE_NEEDS_CONFIRMATION:
        return halted(
            FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED,
            "the Selector returned needs_confirmation; no profile is guessed and no production "
            "is started",
            ["candidates: " + ", ".join(_candidates(selection))],
        )

    if lock_state == adapter.LIFECYCLE_SELECTED:
        if not full_auto:
            return halted(
                FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED,
                "the Visual Lock draft is unconfirmed and this call was not authorized as "
                "full-auto; confirm it (human or delegated) before production",
            )
        authorized, reason = _authorize_full_auto(episode_dir, runtime=runtime)
        if not authorized:
            return halted(
                FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED,
                "delegated Visual Lock confirmation refused: " + str(reason),
                ["continuous execution authorization must exist before a delegated confirmation"],
            )
        report = lifecycle.transition_lock_state(
            episode_dir, lifecycle.LIFECYCLE_LOCKED, actor=DELEGATED_CONFIRMATION_ACTOR,
            mode="delegated_auto", reason=DELEGATED_CONFIRMATION_REASON, story_root=repo)
        lock_state = str(report.get("to") or lock_state)
    elif lock_state in (adapter.LIFECYCLE_LOCKED, adapter.LIFECYCLE_FROZEN):
        pass
    else:
        return halted(
            FULL_AUTO_STATUS_NEEDS_USER,
            "the Visual Lock declares no legal lifecycle state (" + str(lock_state)
            + "); a person must resolve it",
        )

    try:
        import product_runtime_adapter  # local: keep the module import light

        host_wait_rc = int(product_runtime_adapter.HOST_ACTION_REQUIRED_RC)
    except Exception:
        host_wait_rc = 20

    workflow = {"invoked": True, "script": WORKFLOW_SCRIPT, "resume": bool(resume),
                "invocations": 1, "rc": None}
    rc = _run_canonical_workflow(episode_dir, resume=resume, timeout=timeout)
    workflow["rc"] = rc
    production = "workflow rc=" + str(rc)
    review_status = "not_run"
    repair_status = "not_run"
    repair_tasks = []
    repair_rounds = 0
    budget = _repair_budget(root, override=max_repair_rounds)
    notes = []
    status = FULL_AUTO_STATUS_RUNNING

    while True:
        stage = _read_stage(episode_dir)
        index = _stage_index(stage)
        if index is not None and index >= _stage_index("PUBLISH_READY"):
            gate_findings = _final_gate(episode_dir, stage)
            if gate_findings:
                # The stage authority claims readiness; the canonical gate disagrees, so
                # this is never reported as success.
                status = FULL_AUTO_STATUS_NEEDS_USER
                notes.append("the canonical stage declares " + str(stage)
                             + " but machine_gate reported " + str(len(gate_findings))
                             + " FAIL finding(s): " + ", ".join(gate_findings[:5]))
            else:
                status = FULL_AUTO_STATUS_PUBLISH_READY
                notes.append("canonical stage " + str(stage)
                             + " reached, machine_gate clean")
            break
        report = auto_review_loop.review(episode_dir, story_root=repo)
        review_status = report["status"]
        if report["status"] == auto_review_loop.STATUS_PASS:
            action = _next_action(episode_dir)
            if action.get("hard_stop"):
                status = FULL_AUTO_STATUS_NEEDS_USER
                notes.append("next action " + str(action.get("action"))
                             + " requires a human decision")
            elif rc in (0, host_wait_rc):
                status = FULL_AUTO_STATUS_RUNNING
                notes.append("host action pending: " + str(action.get("action")))
            else:
                status = FULL_AUTO_STATUS_FAILED
                notes.append("canonical workflow rc=" + str(rc) + " is not a host wait")
            break
        plan_doc = repair_engine.plan_repairs(report)
        repair_status = plan_doc["status"]
        repair_tasks = plan_doc["tasks"]
        auto = [task for task in repair_tasks
                if task["repairable"] and task["owner"] == repair_engine.OWNER_RUNTIME
                and task["category"] != repair_engine.CATEGORY_VISUAL_PROFILE
                and task["action"] in REPAIR_DISPATCH_ACTIONS]
        keys = {(task["action"], task["target"]) for task in auto}
        held = [task for task in repair_tasks if (task["action"], task["target"]) not in keys]
        if held:
            status = FULL_AUTO_STATUS_NEEDS_USER
            notes.append("repair tasks without a canonical automatic lane stay human owned: "
                         + ", ".join(sorted({str(task["action"]) for task in held})))
            break
        if not auto:
            status = FULL_AUTO_STATUS_NEEDS_USER
            notes.append("the review found nothing this orchestrator may repair automatically")
            break
        if repair_rounds >= budget:
            status = FULL_AUTO_STATUS_NEEDS_USER
            notes.append("repair budget exhausted (" + str(repair_rounds) + "/" + str(budget) + ")")
            break
        outcome = _dispatch_repairs(episode_dir, auto)
        if not outcome["dispatched"]:
            status = FULL_AUTO_STATUS_NEEDS_USER
            notes.append("no repair task could be authorized on a canonical lane: "
                         + json.dumps(outcome["blocked"], ensure_ascii=False))
            break
        repair_rounds += 1
        status = FULL_AUTO_STATUS_REPAIRING
        rc = _run_canonical_workflow(episode_dir, resume=True, timeout=timeout)
        workflow["invocations"] += 1
        workflow["rc"] = rc
        production = ("workflow rc=" + str(rc) + " after repair round " + str(repair_rounds))
        if rc == host_wait_rc:
            # The canonical lane authorized the repair, but the host still owns the pixels
            # (WORK/WEB runtime). Continuing here would spend the repair budget on work nobody
            # did yet, or report a failure for a repair that is legitimately in flight, so the
            # honest status is REPAIRING: the authorized task belongs to the host until it
            # resumes with the new pixels.
            notes.append("repair round " + str(repair_rounds) + " authorized on the canonical "
                         "lane; the host must execute it and resume")
            break

    lock, _lock_source = adapter.read_lock(episode_dir)
    lock_state = str(adapter.lifecycle_of_lock(lock) or "") or lock_state
    return _emit(
        root, episode_dir, status=status, intent=intent, selection=selection,
        profile_id=_profile_id_of(lock), lifecycle_state=lock_state,
        stage=_read_stage(episode_dir), created=created, production=production,
        review=review_status, repair=repair_status, workflow=workflow,
        repair_tasks=repair_tasks, repair_rounds=repair_rounds, notes=notes)


FULL_AUTO_EXIT_CODES = {
    FULL_AUTO_STATUS_PUBLISH_READY: 0,
    FULL_AUTO_STATUS_PLANNED: 2,
    FULL_AUTO_STATUS_RUNNING: 20,
    FULL_AUTO_STATUS_REPAIRING: 20,
    FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED: 3,
    FULL_AUTO_STATUS_NEEDS_USER: 3,
    FULL_AUTO_STATUS_FAILED: 3,
}


def full_auto_exit_code(status) -> int:
    """Exit code for the CLI. Only PUBLISH_READY is success; a child rc never is."""
    return int(FULL_AUTO_EXIT_CODES.get(str(status or "").strip(), 3))


def format_full_auto(document: dict) -> str:
    """Human readable summary of a full-auto status document."""
    lines = [
        "Story OS Canonical Full-Auto",
        "",
        "Status:         " + str(document.get("status")),
        "Episode:        " + str(document.get("episode_dir")),
        "Story Intent:   " + str(document.get("story_intent")),
        "Visual Profile: " + str(document.get("visual_profile")),
        "Visual Lock:    " + str(document.get("visual_lock")),
        "Story Lock:     " + str(document.get("story_lock")),
        "Stage:          " + str(document.get("current_stage")),
        "Production:     " + str(document.get("production")),
        "Review:         " + str(document.get("review")),
        "Repair:         " + str(document.get("repair")),
        "Release:        " + str(document.get("release")),
    ]
    for note in document.get("notes") or []:
        lines.append("")
        lines.append("note: " + str(note))
    lines.append("")
    lines.append("Success is the canonical stage reaching PUBLISH_READY, not a worker exit code.")
    return chr(10).join(lines)


def self_test() -> None:
    dry = plan(ROOT, "天界普通工作人员的一天", dry_run=True, story_root=ROOT)
    assert dry["status"] == STATUS_PLANNED, dry
    assert dry["visual_profile"]["profile_id"] == visual_profile_selector.M02, dry
    assert dry["created"] is False and dry["visual_profile"]["lock_path"] is None, dry
    conflict = plan(ROOT, "古代江南女子卖花的一天", dry_run=True, story_root=ROOT)
    assert conflict["status"] == STATUS_NEEDS_CONFIRMATION, conflict
    assert sorted(conflict["visual_profile"]["candidates"]) == sorted(
        [visual_profile_selector.M01, visual_profile_selector.M03]), conflict
    assert any(a["step"] == "adjudicate_visual_profile" for a in conflict["next_actions"])
    assert "unattended production: not enabled" in format_plan(dry)
    print("PRODUCTION ORCHESTRATOR SELF-TEST PASS")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story OS one sentence production plan")
    sub = ap.add_subparsers(dest="cmd")

    produce = sub.add_parser("produce", help="one sentence story request -> Production Plan")
    produce.add_argument("--idea", required=True, help="one sentence story request")
    produce.add_argument("--title", help="Episode title (defaults to the idea)")
    produce.add_argument("--root", help="repository root (defaults to this checkout)")
    produce.add_argument("--frames", type=int, default=DEFAULT_FRAME_COUNT)
    produce.add_argument("--force-profile", help="explicit Visual Profile id (user override)")
    produce.add_argument("--series", help="series name for episode_context")
    produce.add_argument("--previous-profile", help="series locked profile for episode_context")
    produce.add_argument("--dry-run", action="store_true",
                         help="select only; write nothing")
    produce.add_argument("--json", action="store_true", help="print the full plan document")

    review = sub.add_parser("review", help="rule review of an Episode's existing evidence")
    review.add_argument("episode_dir")
    review.add_argument("--root", help="repository root (defaults to this checkout)")
    review.add_argument("--json", action="store_true")

    repair = sub.add_parser("repair", help="derive repair tasks from a review report")
    repair.add_argument("episode_dir")
    repair.add_argument("--root", help="repository root (defaults to this checkout)")
    repair.add_argument("--json", action="store_true")

    sub.add_parser("self-test")
    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd in (None, "self-test"):
        self_test()
        return 0

    if args.cmd == "produce":
        context = {}
        if args.series:
            context["series"] = args.series
        if args.previous_profile:
            context["previous_profile"] = args.previous_profile
        root = _root(args.root)
        plan_doc = plan(
            root, args.idea, title=args.title, frames=args.frames,
            forced_profile_id=args.force_profile,
            episode_context=context or None,
            dry_run=args.dry_run, story_root=root,
        )
        print(json.dumps(plan_doc, ensure_ascii=False, indent=2) if args.json else format_plan(plan_doc))
        return 0

    root = _root(args.root)
    report = auto_review_loop.review(args.episode_dir, story_root=root)
    if args.cmd == "review":
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json
              else auto_review_loop.format_report(report))
        return 0 if report["status"] == auto_review_loop.STATUS_PASS else 2

    repair_plan = repair_engine.plan_repairs(report)
    print(json.dumps(repair_plan, ensure_ascii=False, indent=2) if args.json
          else repair_engine.format_plan(repair_plan))
    return 0 if repair_plan["status"] == repair_engine.STATUS_NO_ACTION else 2


if __name__ == "__main__":
    raise SystemExit(main())
