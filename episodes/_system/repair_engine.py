#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Repair Engine (Autonomous Production Pipeline Phase 5.4).

Purpose:
    Turn review findings into repair *tasks*. The engine is one table: an issue
    code maps to a category, an action, an owner and a reason, so the review loop
    and the repair plan can never disagree about what a finding means.

        identity                 who is in the frame
        semantic                 why the frame exists
        visual_profile           which visual world the Episode renders in
        missing_evidence         evidence the review cannot find
        asset_failure            pixels or declared artifacts that are broken

Boundaries
----------
- Plan only. Nothing is executed, no image is regenerated, no file is written.
- The engine never repairs by rewriting an authority: Story Lock, Visual Lock,
  story-gates.json, episode-state.json and the Runtime request are not allowed
  mutation targets, and every task is validated against that whitelist.
- A code the engine does not recognise is reported as non-repairable instead of
  being forced into a guessed remedy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    # Repo convention is script execution (python episodes/_system/x.py). The same
    # module is also runnable as python -m episodes._system.x, which puts the
    # repository root on sys.path instead, so both entry points are kept working.
    sys.path.insert(0, str(_HERE))

ROOT = Path(__file__).resolve().parents[2]

ENGINE_VERSION = "1.0"
MODE = "plan_only"
EXECUTES = False
MUTATES_STORY_LOCK = False
MUTATES_VISUAL_LOCK = False

CATEGORY_IDENTITY = "identity"
CATEGORY_SEMANTIC = "semantic"
CATEGORY_VISUAL_PROFILE = "visual_profile"
CATEGORY_MISSING_EVIDENCE = "missing_evidence"
CATEGORY_ASSET_FAILURE = "asset_failure"
CATEGORIES = (
    CATEGORY_IDENTITY,
    CATEGORY_SEMANTIC,
    CATEGORY_VISUAL_PROFILE,
    CATEGORY_MISSING_EVIDENCE,
    CATEGORY_ASSET_FAILURE,
)

ACTION_REGENERATE_FRAME = "regenerate_frame"
ACTION_ATTACH_IDENTITY_EVIDENCE = "attach_identity_evidence"
ACTION_ATTACH_SEMANTIC_TRACE = "attach_story_semantic_trace"
ACTION_REVIEW_FRAME_IDENTITY = "review_frame_identity"
ACTION_REBIND_FRAME_CONTRACT = "rebind_frame_contract"
ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION = "request_human_visual_lock_confirmation"
ACTION_REPAIR_DECLARED_ARTIFACT = "repair_declared_artifact"
ACTION_MANUAL_REVIEW = "manual_review"

OWNER_HUMAN = "human"
OWNER_RUNTIME = "runtime"

STATUS_NO_ACTION = "no_action"
STATUS_REPAIR_REQUIRED = "repair_required"
STATUS_BLOCKED = "blocked"

ERROR_TASKS_FORBIDDEN_MUTATION = "REPAIR_TASK_FORBIDDEN_MUTATION"
ERROR_REPORT_INVALID = "REPAIR_REPORT_INVALID"

SOURCE_STORY_SEMANTIC_TRACE = "story_semantic_trace"
SOURCE_IDENTITY_CONTINUITY = "identity_continuity"
SOURCE_VISUAL_PROFILE_GATE = "visual_profile_gate"
SOURCE_REPAIR_ENGINE = "repair_engine"

# Mutation whitelist: what a repair task is allowed to touch.
ALLOWED_MUTATION_PREFIXES = (
    "meta/frame-reviews/",
    "meta/runtime/contracts/frames/",
    "media/",
    "meta/production-ledger.json",
)
FORBIDDEN_MUTATION_TOKENS = (
    "visual-profile",
    "story-gates",
    "episode-state",
    "story-lock",
    "release-manifest",
    "runtime-request",
    "character-contract",
)


def _rule(category, action, owner, repairable, reason, source) -> dict:
    return {
        "category": category,
        "action": action,
        "owner": owner,
        "repairable": bool(repairable),
        "reason": reason,
        "source": source,
    }


ISSUE_RULES = {
    # W-22 story semantic trace
    "story_semantic_trace_missing": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_evidence_missing", SOURCE_STORY_SEMANTIC_TRACE),
    "story_semantic_trace_not_required": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_evidence_inconsistent", SOURCE_STORY_SEMANTIC_TRACE),
    "story_role_mismatch": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_role_mismatch", SOURCE_STORY_SEMANTIC_TRACE),
    "story_lock_missing": _rule(
        CATEGORY_SEMANTIC, ACTION_REPAIR_DECLARED_ARTIFACT, OWNER_HUMAN, False,
        "story_lock_unresolvable", SOURCE_STORY_SEMANTIC_TRACE),
    "story_lock_path_mismatch": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "story_lock_path_mismatch", SOURCE_STORY_SEMANTIC_TRACE),
    "story_lock_hash_drift": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "story_lock_hash_drift", SOURCE_STORY_SEMANTIC_TRACE),
    "frame_contract_hash_drift": _rule(
        CATEGORY_SEMANTIC, ACTION_REBIND_FRAME_CONTRACT, OWNER_RUNTIME, True,
        "frame_contract_hash_drift", SOURCE_STORY_SEMANTIC_TRACE),
    "semantic_evaluation_missing": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_evaluation_missing", SOURCE_STORY_SEMANTIC_TRACE),
    "semantic_beat_not_delivered": _rule(
        CATEGORY_SEMANTIC, ACTION_REGENERATE_FRAME, OWNER_RUNTIME, True,
        "story_beat_not_delivered", SOURCE_STORY_SEMANTIC_TRACE),
    "semantic_confidence_missing": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_evaluation_missing", SOURCE_STORY_SEMANTIC_TRACE),
    "semantic_method_missing": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_evaluation_missing", SOURCE_STORY_SEMANTIC_TRACE),
    "semantic_evidence_missing_provenance": _rule(
        CATEGORY_SEMANTIC, ACTION_ATTACH_SEMANTIC_TRACE, OWNER_HUMAN, True,
        "semantic_provenance_missing", SOURCE_STORY_SEMANTIC_TRACE),
    # P1-1 identity continuity
    "identity_continuity_evidence_missing": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_evidence_missing", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_not_required": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_evidence_inconsistent", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_missing_character": _rule(
        CATEGORY_IDENTITY, ACTION_REVIEW_FRAME_IDENTITY, OWNER_HUMAN, True,
        "identity_character_not_evaluated", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_anchor_missing": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_anchor_missing", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_anchor_mismatch": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_anchor_mismatch", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_hash_drift": _rule(
        CATEGORY_IDENTITY, ACTION_REVIEW_FRAME_IDENTITY, OWNER_HUMAN, True,
        "identity_anchor_hash_drift", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_authority_drift": _rule(
        CATEGORY_IDENTITY, ACTION_REVIEW_FRAME_IDENTITY, OWNER_HUMAN, True,
        "identity_authority_drift", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_evaluation_missing": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_evaluation_missing", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_not_consistent": _rule(
        CATEGORY_IDENTITY, ACTION_REGENERATE_FRAME, OWNER_RUNTIME, True,
        "identity_mismatch", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_confidence_missing": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_evaluation_missing", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_method_missing": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_evaluation_missing", SOURCE_IDENTITY_CONTINUITY),
    "identity_continuity_provenance_missing": _rule(
        CATEGORY_IDENTITY, ACTION_ATTACH_IDENTITY_EVIDENCE, OWNER_HUMAN, True,
        "identity_provenance_missing", SOURCE_IDENTITY_CONTINUITY),
    # Visual Profile governance Phase 4.3
    "VISUAL_PROFILE_NOT_LOCKED": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION, OWNER_HUMAN, True,
        "visual_lock_not_confirmed", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_NOT_FROZEN": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION, OWNER_HUMAN, True,
        "visual_lock_not_frozen", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_NOT_CONFIRMED": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION, OWNER_HUMAN, True,
        "visual_lock_not_confirmed", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_CONFIRMATION_MISSING": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION, OWNER_HUMAN, True,
        "visual_lock_confirmation_missing", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_LOCK_MISSING": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION, OWNER_HUMAN, True,
        "visual_lock_missing", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_selection_evidence_missing", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_NOT_REGISTERED": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_profile_not_registered", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_NOT_ACTIVE": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_profile_not_active", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_PATH_MISMATCH": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_profile_path_mismatch", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_FILE_MISSING": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_profile_file_missing", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_LOCK_INVALID": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_lock_invalid", SOURCE_VISUAL_PROFILE_GATE),
    "VISUAL_PROFILE_LOCK_UNREADABLE": _rule(
        CATEGORY_VISUAL_PROFILE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
        "visual_lock_unreadable", SOURCE_VISUAL_PROFILE_GATE),
}

DEFAULT_RULE = _rule(
    CATEGORY_MISSING_EVIDENCE, ACTION_MANUAL_REVIEW, OWNER_HUMAN, False,
    "unclassified_issue", SOURCE_REPAIR_ENGINE)

REPAIR_REASONS = {
    ACTION_REGENERATE_FRAME: "frame_pixels_must_be_regenerated",
    ACTION_ATTACH_IDENTITY_EVIDENCE: "identity_evidence_must_be_recorded",
    ACTION_ATTACH_SEMANTIC_TRACE: "story_semantic_trace_must_be_recorded",
    ACTION_REVIEW_FRAME_IDENTITY: "identity_must_be_reviewed_against_anchor",
    ACTION_REBIND_FRAME_CONTRACT: "frame_contract_must_be_rebound",
    ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION: "human_visual_lock_confirmation_required",
    ACTION_REPAIR_DECLARED_ARTIFACT: "declared_artifact_unresolvable",
    ACTION_MANUAL_REVIEW: "human_review_required",
}


class RepairEngineError(SystemExit):
    """Fail-fast repair error (shares the registry SystemExit convention)."""

    code = ERROR_REPORT_INVALID

    def __init__(self, message, code=None):
        self.code = code or self.code
        super().__init__(self.code + ": " + str(message))


def classify(code) -> dict:
    """Issue code -> repair rule. Unknown codes are non-repairable by default."""
    rule = ISSUE_RULES.get(str(code))
    if rule is None:
        rule = dict(DEFAULT_RULE)
        rule["reason"] = "unclassified_issue:" + str(code)
    return dict(rule)


def _digest(*parts) -> str:
    blob = "|".join(str(part) for part in parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def mutations_for(action: str, frame) -> list:
    """The only artifacts a repair task may touch. Empty means plan only."""
    if not frame:
        return []
    if action in (ACTION_ATTACH_SEMANTIC_TRACE, ACTION_ATTACH_IDENTITY_EVIDENCE):
        return ["meta/frame-reviews/" + str(frame) + ".json"]
    if action == ACTION_REGENERATE_FRAME:
        return ["media/frames/" + str(frame), "meta/production-ledger.json"]
    if action == ACTION_REBIND_FRAME_CONTRACT:
        return ["meta/runtime/contracts/frames/" + str(frame) + ".json"]
    return []


def validate_tasks(tasks) -> list:
    """Return violations proving a task would rewrite a protected authority."""
    violations = []
    for task in tasks or []:
        for target in task.get("mutates") or []:
            lowered = str(target).lower()
            forbidden = [token for token in FORBIDDEN_MUTATION_TOKENS if token in lowered]
            if forbidden:
                violations.append(
                    "task " + str(task.get("task_id")) + " targets a protected authority: "
                    + str(target) + " (" + ",".join(forbidden) + ")")
            elif not any(lowered.startswith(prefix) for prefix in ALLOWED_MUTATION_PREFIXES):
                violations.append(
                    "task " + str(task.get("task_id")) + " targets " + str(target)
                    + " which is outside the repair whitelist")
    return violations


def plan_repairs(report) -> dict:
    """Derive repair tasks from an auto_review_loop report. Writes nothing."""
    if not isinstance(report, dict):
        raise RepairEngineError("a review report document is required")
    issues = [issue for issue in (report.get("issues") or []) if isinstance(issue, dict)]

    groups: dict = {}
    for issue in issues:
        rule = classify(issue.get("code"))
        frame = issue.get("frame")
        key = (str(frame) if frame else "episode", rule["action"])
        group = groups.setdefault(key, {
            "frame": frame, "action": rule["action"], "rules": [], "codes": [],
            "messages": [],
        })
        group["rules"].append(rule)
        group["codes"].append(str(issue.get("code")))
        group["messages"].append(str(issue.get("message") or ""))

    tasks = []
    for key in sorted(groups):
        group = groups[key]
        rules = group["rules"]
        codes = sorted(set(group["codes"]))
        owners = {rule["owner"] for rule in rules}
        categories = sorted({rule["category"] for rule in rules})
        repairable = all(rule["repairable"] for rule in rules)
        frame = group["frame"]
        action = group["action"]
        reasons = sorted({rule["reason"] for rule in rules})
        tasks.append({
            "task_id": "repair:" + _digest(
                str(report.get("episode_id") or ""), key[0], action, ",".join(codes))[:12],
            "action": action,
            "target": str(frame) if frame else "episode",
            "category": categories[0] if len(categories) == 1 else "mixed",
            "categories": categories,
            "owner": OWNER_HUMAN if OWNER_HUMAN in owners else OWNER_RUNTIME,
            "reason": reasons[0],
            "reasons": reasons,
            "repairable": repairable,
            "issue_codes": codes,
            "messages": group["messages"],
            "mutates": mutations_for(action, frame),
            "source": sorted({rule["source"] for rule in rules})[0],
            "guards": {"story_lock": "untouched", "visual_lock": "untouched"},
        })

    violations = validate_tasks(tasks)
    if violations:
        raise RepairEngineError(
            "a repair task would rewrite a protected authority: " + "; ".join(violations),
            ERROR_TASKS_FORBIDDEN_MUTATION,
        )

    if not tasks:
        status = STATUS_NO_ACTION
    elif any(not task["repairable"] for task in tasks):
        status = STATUS_BLOCKED
    else:
        status = STATUS_REPAIR_REQUIRED

    return {
        "schema_version": 1,
        "engine_version": ENGINE_VERSION,
        "mode": MODE,
        "executes": EXECUTES,
        "episode_id": report.get("episode_id"),
        "episode_dir": report.get("episode_dir"),
        "review_status": report.get("status"),
        "status": status,
        "tasks": tasks,
        "guards": {
            "story_lock": "never_modified",
            "visual_lock": "never_modified",
            "episode_state": "never_modified",
            "mutates_story_lock": MUTATES_STORY_LOCK,
            "mutates_visual_lock": MUTATES_VISUAL_LOCK,
            "forbidden_mutations": list(FORBIDDEN_MUTATION_TOKENS),
            "allowed_mutations": list(ALLOWED_MUTATION_PREFIXES),
        },
        "notes": [
            "plan only: every task is proposed, not executed",
            "Story Lock and Visual Lock are never repair targets; a lock problem is a human decision",
        ],
    }


def format_plan(repair_plan: dict) -> str:
    lines = [
        "Repair Plan (plan only)",
        "Episode: " + str(repair_plan.get("episode_id")),
        "Review:  " + str(repair_plan.get("review_status")),
        "Status:  " + str(repair_plan.get("status")),
        "Tasks:   " + str(len(repair_plan.get("tasks") or [])),
    ]
    for task in repair_plan.get("tasks") or []:
        lines.append("")
        lines.append("  " + task["action"] + " -> " + task["target"]
                     + "  [" + task["category"] + ", owner=" + task["owner"] + "]")
        lines.append("    reason:  " + task["reason"])
        lines.append("    codes:   " + ", ".join(task["issue_codes"]))
        lines.append("    mutates: " + (", ".join(task["mutates"]) or "nothing (human step)"))
        lines.append("    guards:  story_lock=" + task["guards"]["story_lock"]
                     + " visual_lock=" + task["guards"]["visual_lock"])
    if not repair_plan.get("tasks"):
        lines.append("")
        lines.append("  no action: the review found nothing to repair")
    return chr(10).join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan", help="review an Episode and plan repair tasks")
    p.add_argument("episode_dir")
    p.add_argument("--root", help="repository root (defaults to this checkout)")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("plan-report", help="plan repair tasks from a saved review report")
    p.add_argument("report")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "plan-report":
        content = Path(args.report).read_text(encoding="utf-8")
        report = json.loads(content)
    else:
        import auto_review_loop  # local import: auto_review_loop imports this module

        report = auto_review_loop.review(
            args.episode_dir,
            story_root=Path(args.root) if args.root else ROOT,
        )
    repair_plan = plan_repairs(report)
    print(json.dumps(repair_plan, ensure_ascii=False, indent=2) if args.json
          else format_plan(repair_plan))
    return 0 if repair_plan["status"] == STATUS_NO_ACTION else 2


if __name__ == "__main__":
    raise SystemExit(main())
