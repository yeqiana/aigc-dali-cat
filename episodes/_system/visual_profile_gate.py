#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Visual Profile Production Gate (Visual Profile Governance Phase 4.3).

Why this module exists
----------------------
Phase 3.5 verifies that a Visual Lock records a purposeful selection. Phase 4.2
gives that lock a lifecycle. What a production run still needs to know is
narrower and stricter:

    may this Episode actually be produced with the profile it declared?

This module answers that question. It is a production-facing evidence gate, so it
asks for more than Phase 3.5: the lock must exist, name a registered profile
whose path still matches the registry, carry the selection fact, carry a
confirmation record, and be LOCKED (FROZEN once the Episode reaches a release
stage).

    Selector -> Visual Lock DRAFT -> [confirm] LOCKED -> [freeze] FROZEN
                                                              |
                                             validate_visual_profile_for_production()
                                                              |
                                                     production decision

Checks, in evaluation order (the first failure decides result["code"])
---------------------------------------------------------------------
    1. profile_id is registered and active       VISUAL_PROFILE_NOT_REGISTERED / _NOT_ACTIVE
    2. profile_path matches the registry entry   VISUAL_PROFILE_PATH_MISMATCH
       and the file it points at exists          VISUAL_PROFILE_FILE_MISSING
    3. the lock is LOCKED (or FROZEN)            VISUAL_PROFILE_NOT_LOCKED
    4. selection_evidence carries the fact       VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING
    5. the confirmation record is present        VISUAL_PROFILE_CONFIRMATION_MISSING
    6. release stages additionally require       VISUAL_PROFILE_NOT_FROZEN
       the FROZEN lifecycle state

Boundaries
----------
- Read-only. It never selects a profile, never confirms, never freezes and never
  writes to an Episode.
- It does not re-run Phase 3.5 logic by copying it: the registry, path, evidence
  and confirmation checks share the Phase 3.5 contract constants so the two gates
  cannot drift apart.
- machine_gate.py is NOT modified and does NOT call this module yet. An audit
  found no visual hook in machine_gate, so Phase 4.3 ships the validator only.
  Wiring it into the production gate is a separate, deliberate step.
- Historical compatibility: an Episode with no Visual Lock and no governance
  opt-in is reported as legacy_unmanaged and does NOT block production.

Result contract
---------------
    status   pass | fail | legacy_unmanaged   (legacy_unmanaged never blocks)
    ok       True unless status == fail
    code     the first error code, or None
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import visual_profile_lock as lock_gate
import visual_profile_lock_adapter as adapter
import visual_profile_lock_lifecycle as lifecycle
import visual_profile_registry as registry

ROOT = Path(__file__).resolve().parents[2]

GATE_VERSION = "1.0"

STAGE_PRODUCTION = "production"
# Reaching any of these means real assets exist for this profile, so the lock
# must already be frozen.
RELEASE_STAGES = ("release", "release_lock", "delivery", "publish", "publish_ready",
                  "published", "data_reviewed")
RELEASE_STATE_NAMES = ("PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED")

LIFECYCLE_LOCKED = lifecycle.LIFECYCLE_LOCKED
LIFECYCLE_FROZEN = lifecycle.LIFECYCLE_FROZEN
PRODUCTION_LIFECYCLE_STATES = (LIFECYCLE_LOCKED, LIFECYCLE_FROZEN)

STATUS_PASS = lock_gate.STATUS_PASS
STATUS_FAIL = lock_gate.STATUS_FAIL
STATUS_LEGACY = lock_gate.STATUS_LEGACY

ERROR_NOT_REGISTERED = lock_gate.ERROR_NOT_REGISTERED
ERROR_NOT_ACTIVE = lock_gate.ERROR_NOT_ACTIVE
ERROR_PATH_MISMATCH = lock_gate.ERROR_PATH_MISMATCH
ERROR_FILE_MISSING = lock_gate.ERROR_FILE_MISSING
ERROR_EVIDENCE_MISSING = lock_gate.ERROR_EVIDENCE_MISSING
ERROR_CONFIRMATION_MISSING = lock_gate.ERROR_CONFIRMATION_MISSING
ERROR_LOCK_MISSING = lock_gate.ERROR_LOCK_MISSING
ERROR_LOCK_INVALID = lock_gate.ERROR_LOCK_INVALID
ERROR_LOCK_UNREADABLE = lock_gate.ERROR_LOCK_UNREADABLE

ERROR_NOT_LOCKED = "VISUAL_PROFILE_NOT_LOCKED"
ERROR_NOT_FROZEN = "VISUAL_PROFILE_NOT_FROZEN"

ERROR_CODES = (
    ERROR_NOT_REGISTERED,
    ERROR_NOT_ACTIVE,
    ERROR_PATH_MISMATCH,
    ERROR_FILE_MISSING,
    ERROR_EVIDENCE_MISSING,
    ERROR_CONFIRMATION_MISSING,
    ERROR_LOCK_MISSING,
    ERROR_LOCK_INVALID,
    ERROR_LOCK_UNREADABLE,
    ERROR_NOT_LOCKED,
    ERROR_NOT_FROZEN,
)


def _root(story_root: Path | str | None = None) -> Path:
    return Path(story_root) if story_root else ROOT


# --------------------------------------------------------------------------- #
# stage helpers
# --------------------------------------------------------------------------- #

def normalized_stage(stage) -> str:
    return str(stage or STAGE_PRODUCTION).strip().lower()


def requires_frozen(stage) -> bool:
    """True when this stage implies production assets already exist."""
    raw = str(stage or "").strip()
    if raw.upper() in RELEASE_STATE_NAMES:
        return True
    return normalized_stage(stage) in RELEASE_STAGES


# --------------------------------------------------------------------------- #
# result assembly
# --------------------------------------------------------------------------- #

def _blank(stage: str) -> dict[str, Any]:
    return {
        "status": STATUS_LEGACY,
        "ok": True,
        "code": None,
        "gate_version": GATE_VERSION,
        "stage": stage,
        "requires_frozen": requires_frozen(stage),
        "required": False,
        "requirement_reason": None,
        "governed": False,
        "judged": False,
        "source": None,
        "profile_id": None,
        "profile_path": None,
        "lifecycle_state": None,
        "checks": [],
        "errors": [],
    }


def _record(result: dict, check: str, status: str, detail: str, code: str | None = None) -> None:
    result["checks"].append({"name": check, "status": status, "code": code, "detail": detail})
    if status == "fail":
        result["errors"].append({"code": code, "detail": detail})


def _pass(result: dict, check: str, detail: str = "ok") -> None:
    _record(result, check, "pass", detail)


def _fail(result: dict, check: str, code: str, detail: str) -> None:
    _record(result, check, "fail", detail, code)


def _skip(result: dict, check: str, detail: str) -> None:
    _record(result, check, "skip", detail)


def _finish(result: dict) -> dict[str, Any]:
    if result["errors"]:
        result["status"] = STATUS_FAIL
        result["code"] = result["errors"][0]["code"]
    elif result.get("judged"):
        result["status"] = STATUS_PASS
        result["code"] = None
    else:
        result["status"] = STATUS_LEGACY
        result["code"] = None
    result["ok"] = result["status"] != STATUS_FAIL
    return result


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #

def _check_registry(result: dict, profile_id: str, root: Path) -> dict | None:
    try:
        entry = registry.registry_entry(profile_id, root)
        registered = registry.registry_ids(root)
    except registry.VisualProfileError as exc:
        _fail(result, "profile_registered", getattr(exc, "code", ERROR_LOCK_INVALID),
              f"registry could not be read: {exc}")
        return None
    if entry is None:
        _fail(result, "profile_registered", ERROR_NOT_REGISTERED,
              f"profile_id={profile_id!r} is not registered in {registry.REGISTRY_REL.as_posix()} "
              f"(registered: {', '.join(registered)})")
        return None
    status = str(entry.get("status") or "").strip()
    if status != registry.ACTIVE_STATUS:
        _fail(result, "profile_registered", ERROR_NOT_ACTIVE,
              f"profile_id={profile_id!r} status={status!r} is not '{registry.ACTIVE_STATUS}'")
        return None
    _pass(result, "profile_registered", f"profile_id={profile_id!r} is registered and active")
    return entry


def _check_path(result: dict, lock: dict, entry: dict, root: Path, *, metadata_only: bool) -> None:
    declared = lock_gate.normalize_rel(lock.get("profile_path"))
    expected = lock_gate.normalize_rel(entry.get("path"))
    result["profile_path"] = declared or None
    if not declared:
        _fail(result, "profile_path_matches_registry", ERROR_LOCK_INVALID,
              "profile_path is missing; a Visual Lock must name the profile document it locked")
        return
    if declared != expected:
        _fail(result, "profile_path_matches_registry", ERROR_PATH_MISMATCH,
              f"profile_path={declared} does not match the registry path {expected} "
              f"for profile_id={lock.get('profile_id')!r}")
        return
    if not metadata_only and not (root / declared).is_file():
        _fail(result, "profile_path_matches_registry", ERROR_FILE_MISSING,
              f"registered profile document is missing: {declared}")
        return
    _pass(result, "profile_path_matches_registry", f"profile_path matches the registry entry: {declared}")


def _check_lifecycle(result: dict, lock: dict, stage: str) -> str | None:
    state = lifecycle.lifecycle_of(lock)
    result["lifecycle_state"] = state
    if state is None:
        _fail(result, "lifecycle_locked", ERROR_NOT_LOCKED,
              "this Visual Lock declares no recognizable lifecycle state; "
              f"production requires {LIFECYCLE_LOCKED}")
        return None
    if state not in PRODUCTION_LIFECYCLE_STATES:
        _fail(result, "lifecycle_locked", ERROR_NOT_LOCKED,
              f"lifecycle_state={state!r} must be {LIFECYCLE_LOCKED} before production "
              "(a draft SELECTED / NEEDS_CONFIRMATION lock is not adjudicated)")
        return state
    if requires_frozen(stage) and state != LIFECYCLE_FROZEN:
        _fail(result, "lifecycle_frozen", ERROR_NOT_FROZEN,
              f"stage={stage!r} requires lifecycle_state={LIFECYCLE_FROZEN}, got {state!r}; "
              "freeze the profile before release")
        return state
    if state == LIFECYCLE_FROZEN:
        _pass(result, "lifecycle_locked", f"lifecycle_state={LIFECYCLE_FROZEN} (frozen and locked)")
    else:
        _pass(result, "lifecycle_locked", f"lifecycle_state={LIFECYCLE_LOCKED}")
    return state


def _check_evidence(result: dict, lock: dict) -> None:
    evidence = lock.get("selection_evidence")
    if not isinstance(evidence, dict) or not evidence:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              "selection_evidence is missing; a produced profile must carry the selection fact")
        return
    missing = []
    for field in lock_gate.EVIDENCE_REQUIRED_FIELDS:
        if field not in evidence:
            missing.append(field)
        elif field != "matched_rules" and evidence.get(field) in (None, "", [], {}):
            missing.append(field)
    if "matched_rules" not in missing and not isinstance(evidence.get("matched_rules"), list):
        missing.append("matched_rules")
    if missing:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              f"selection_evidence is missing required field(s): {', '.join(missing)}")
        return
    digest = str(evidence.get("inputs_digest") or "")
    if lock_gate.DIGEST_RE.match(digest) is None:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              f"selection_evidence.inputs_digest={digest!r} is not 'sha256:' followed by 64 hex characters")
        return
    _pass(result, "selection_evidence_present",
          f"selection fact from selector_version={evidence.get('selector_version')!r} "
          f"source={evidence.get('source')!r}")


def _check_confirmation(result: dict, lock: dict) -> None:
    mode = lock_gate.confirmation_mode(lock)
    if mode not in lock_gate.CONFIRMATION_MODES:
        _fail(result, "confirmation_recorded", ERROR_CONFIRMATION_MISSING,
              f"confirmation_mode={mode!r} is not one of {', '.join(lock_gate.CONFIRMATION_MODES)}")
        return
    if mode not in lock_gate.HUMAN_CONFIRMATION_MODES:
        _pass(result, "confirmation_recorded",
              f"confirmation_mode={mode!r} does not require a human confirmation record")
        return
    confirmed_by = str(lock.get("confirmed_by") or "").strip()
    confirmed_at = str(lock.get("confirmed_at") or "").strip()
    missing = [name for name, value in (("confirmed_by", confirmed_by), ("confirmed_at", confirmed_at))
               if not value]
    if missing:
        _fail(result, "confirmation_recorded", ERROR_CONFIRMATION_MISSING,
              f"confirmation_mode={mode!r} requires {', '.join(missing)}")
        return
    _pass(result, "confirmation_recorded",
          f"confirmed_by={confirmed_by!r} confirmed_at={confirmed_at}")


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def validate_visual_profile_for_production(
    episode=None,
    lock: Any = None,
    *,
    story_root: Path | str | None = None,
    stage: str = STAGE_PRODUCTION,
    required: bool | None = None,
    metadata_only: bool = False,
) -> dict[str, Any]:
    """Verify a Visual Lock may enter production. Read-only.

    episode       Episode directory whose meta/visual-profile.json is verified.
    lock          Visual Lock document. When supplied, the Episode is not read.
    story_root    repository root used to resolve the registry (tests).
    stage         production (default) or a release stage; release stages also
                  require the FROZEN lifecycle state.
    required      forced requirement flag. Default: derived from the Episode, or
                  from the supplied document when there is no Episode.
    metadata_only skip filesystem existence checks.

    Returns {status pass|fail|legacy_unmanaged, ok, code, lifecycle_state, checks,
    errors, ...}. legacy_unmanaged never blocks production.
    """
    root = _root(story_root)
    result = _blank(stage)

    if lock is None and episode is not None:
        # adapter.read_lock raises on an unreadable lock, which is exactly the
        # fail-closed behaviour a production gate wants.
        try:
            lock, source = adapter.read_lock(episode)
        except adapter.VisualProfileLockAdapterError as exc:
            _fail(result, "lock_readable", getattr(exc, "code", ERROR_LOCK_UNREADABLE),
                  f"Visual Lock could not be read: {exc}")
            return _finish(result)
        result["source"] = source
    elif lock is not None:
        result["source"] = "lock_document"

    if isinstance(required, bool):
        requirement = {"required": required, "reason": "explicit caller override"}
    elif episode is not None:
        requirement = lock_gate.visual_profile_requirement(episode)
    else:
        governed = lock_gate.lock_is_governed(lock)
        requirement = {
            "required": governed,
            "reason": "supplied lock document claims the visual lock contract" if governed
                      else "no Episode context supplied",
        }
    result["required"] = bool(requirement["required"])
    result["requirement_reason"] = requirement["reason"]

    if lock is None:
        if result["required"]:
            _fail(result, "lock_present", ERROR_LOCK_MISSING,
                  f"this Episode declares it needs a Visual Profile ({requirement['reason']}) "
                  f"but has no {adapter.LOCK_REL.as_posix()}")
        else:
            _skip(result, "lock_present",
                  f"no Visual Lock and no governance opt-in ({requirement['reason']})")
        return _finish(result)

    if not isinstance(lock, dict):
        _fail(result, "lock_readable", ERROR_LOCK_INVALID, "Visual Lock root must be a JSON object")
        return _finish(result)

    if not lock_gate.lock_is_governed(lock):
        result["governed"] = False
        result["requirement_reason"] = "pre-governance episode meta lock (no governance field)"
        _skip(result, "lock_present",
              "legacy episode meta lock: presence is not governance evidence, not judged")
        return _finish(result)

    result["governed"] = True
    result["judged"] = True

    profile_id = str(lock.get("profile_id") or "").strip()
    result["profile_id"] = profile_id or None

    if not profile_id:
        # An unadjudicated selection (a needs_confirmation draft) names no profile
        # on purpose. Report that as "not locked" rather than "not registered", so
        # the producer sees the real blocker: nobody has confirmed the profile yet.
        state = _check_lifecycle(result, lock, stage)
        if state not in PRODUCTION_LIFECYCLE_STATES:
            return _finish(result)
        _fail(result, "profile_registered", ERROR_NOT_REGISTERED,
              "profile_id is missing; a Visual Lock must name the profile it locked")
        return _finish(result)

    entry = _check_registry(result, profile_id, root)
    if entry is None:
        return _finish(result)
    _check_path(result, lock, entry, root, metadata_only=metadata_only)
    _check_lifecycle(result, lock, stage)
    _check_evidence(result, lock)
    _check_confirmation(result, lock)
    return _finish(result)


def verify_visual_profile_for_production(
    episode,
    *,
    story_root: Path | str | None = None,
    stage: str = STAGE_PRODUCTION,
    metadata_only: bool = False,
) -> list[str]:
    """Gate adapter: error strings for a failing production check, [] otherwise.

    A legacy or unmanaged Episode never produces errors, so wiring this into a
    future gate cannot retroactively fail historical Episodes.
    """
    if metadata_only:
        return []
    result = validate_visual_profile_for_production(
        episode=episode, story_root=story_root, stage=stage)
    if result["status"] != STATUS_FAIL:
        return []
    return [f"{error['code']}: {error['detail']}" for error in result["errors"]]


# --------------------------------------------------------------------------- #
# CLI (read-only)
# --------------------------------------------------------------------------- #

def _parse_stage(argv_stage) -> str:
    return str(argv_stage or STAGE_PRODUCTION)


def cmd_validate(args: argparse.Namespace) -> int:
    target = Path(args.target)
    if target.is_dir():
        result = validate_visual_profile_for_production(
            episode=target, story_root=args.story_root, stage=_parse_stage(args.stage))
    else:
        lock = lock_gate.read_json(target, default=None)
        if not isinstance(lock, dict):
            result = _blank(_parse_stage(args.stage))
            _fail(result, "lock_readable", ERROR_LOCK_UNREADABLE,
                  f"lock document is unreadable or not a JSON object: {target}")
        else:
            result = validate_visual_profile_for_production(
                lock=lock, story_root=args.story_root, stage=_parse_stage(args.stage))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == STATUS_FAIL else 0


def cmd_verify(args: argparse.Namespace) -> int:
    errors = verify_visual_profile_for_production(
        Path(args.episode_dir), story_root=args.story_root, stage=_parse_stage(args.stage))
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print("VISUAL PROFILE PRODUCTION GATE VERIFIED")
    return 0


def self_test() -> None:
    assert requires_frozen("production") is False
    assert requires_frozen("release") is True
    assert requires_frozen("PUBLISH_READY") is True
    assert normalized_stage(None) == STAGE_PRODUCTION
    assert validate_visual_profile_for_production(None)["status"] == STATUS_LEGACY
    pre_governance = {"profile_id": "M00", "mode": "explicit_user_locked"}
    assert validate_visual_profile_for_production(lock=pre_governance)["status"] == STATUS_LEGACY
    print("VISUAL PROFILE PRODUCTION GATE SELF-TEST PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story OS Visual Profile production gate (governance Phase 4.3)")
    parser.add_argument("--story-root", dest="story_root", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    child = sub.add_parser("validate", help="validate an Episode directory or a Visual Lock document")
    child.add_argument("target")
    child.add_argument("--stage", default=STAGE_PRODUCTION)
    child.set_defaults(func=cmd_validate)
    child = sub.add_parser("verify", help="gate adapter: non-zero exit when the Episode fails")
    child.add_argument("episode_dir")
    child.add_argument("--stage", default=STAGE_PRODUCTION)
    child.set_defaults(func=cmd_verify)
    sub.add_parser("self-test").set_defaults(func=lambda args: (self_test(), 0)[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
