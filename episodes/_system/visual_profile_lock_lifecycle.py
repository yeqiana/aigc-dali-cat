#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Visual Lock Lifecycle Management (Visual Profile Governance Phase 4.2).

Why this module exists
----------------------
Phase 4.1 turns a Selector result into a Visual Lock DRAFT and deliberately
refuses to adjudicate it: the draft declares confirmation_mode="pending", which
the Phase 3.5 evidence gate rejects on purpose. Before this module nothing could
move that draft forward, so an Episode could never carry an adjudicated lock.

This module owns exactly that gap: the state machine and the confirmation record.

    Selector -> Selection Evidence -> Visual Lock DRAFT   (Phase 4.1)
             -> [confirm] -> LOCKED                        <-- this module
             -> [freeze]  -> FROZEN
             -> [verify]  -> Production Gate               (Phase 4.3)

State machine
-------------
Allowed
    SELECTED            -> LOCKED
    NEEDS_CONFIRMATION  -> LOCKED      (a human names the profile)
    LOCKED              -> FROZEN      (production has begun)

Forbidden, each with an explicit error code
    DRAFT               -> LOCKED      VISUAL_LOCK_INVALID_TRANSITION
    NEEDS_CONFIRMATION  -> FROZEN      VISUAL_LOCK_INVALID_TRANSITION
    FROZEN              -> any         VISUAL_LOCK_ALREADY_FROZEN

Boundaries
----------
- Transitions and the confirmation record only. It never selects a profile (the
  Selector does), never invents selection evidence, never produces images and
  never runs production.
- It writes exactly one document: the Episode Visual Lock it was asked to
  advance. It does not touch episode-state.json, story-gates.json, Frame
  Contracts, the production ledger or machine_gate.
- Historical Episodes are untouched. An Episode without a Visual Lock raises
  VISUAL_LOCK_NOT_FOUND rather than being given an invented one.
- machine_gate does not call this module. Phase 4.3 wires its own opt-in gate.

Confirmation record
-------------------
A LOCKED lock carries the nested Phase 4.2 block

    "confirmation": {"mode", "confirmed_by", "confirmed_at", "reason"}

and the Phase 3.5 top-level fields (confirmation_mode / confirmed_by /
confirmed_at) so the existing evidence gate keeps passing. FROZEN inherits the
whole confirmation record and never rewrites it.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import story_json
import visual_profile_lock as lock_gate
import visual_profile_lock_adapter as adapter
import visual_profile_registry as registry

ROOT = Path(__file__).resolve().parents[2]

LIFECYCLE_DRAFT = adapter.LIFECYCLE_DRAFT
LIFECYCLE_SELECTED = adapter.LIFECYCLE_SELECTED
LIFECYCLE_NEEDS_CONFIRMATION = adapter.LIFECYCLE_NEEDS_CONFIRMATION
LIFECYCLE_LOCKED = adapter.LIFECYCLE_LOCKED
LIFECYCLE_FROZEN = adapter.LIFECYCLE_FROZEN
LIFECYCLE_STATES = adapter.LIFECYCLE_STATES

LOCK_REL = adapter.LOCK_REL
RUNTIME_REQUEST_REL = adapter.RUNTIME_REQUEST_REL

LIFECYCLE_VERSION = "1.0"

CONFIRMATION_MODES = ("human", "direct_user", "delegated_auto", "system")
HUMAN_CONFIRMATION_MODES = ("human", "direct_user", "delegated_auto")

# The only transitions this state machine allows. A draft is never locked
# directly, and a needs_confirmation selection is never frozen: it must pass
# through an explicit confirmation that names the profile first.
ALLOWED_TRANSITIONS = {
    LIFECYCLE_SELECTED: (LIFECYCLE_LOCKED,),
    LIFECYCLE_NEEDS_CONFIRMATION: (LIFECYCLE_LOCKED,),
    LIFECYCLE_LOCKED: (LIFECYCLE_FROZEN,),
    LIFECYCLE_DRAFT: (),
    LIFECYCLE_FROZEN: (),
}

ERROR_INVALID_TRANSITION = "VISUAL_LOCK_INVALID_TRANSITION"
ERROR_ALREADY_FROZEN = "VISUAL_LOCK_ALREADY_FROZEN"
ERROR_NOT_FOUND = "VISUAL_LOCK_NOT_FOUND"
ERROR_CONFIRMATION_INVALID = "VISUAL_LOCK_CONFIRMATION_INVALID"
ERROR_PROFILE_REQUIRED = "VISUAL_LOCK_PROFILE_REQUIRED"
ERROR_STATE_UNKNOWN = "VISUAL_LOCK_STATE_UNKNOWN"
ERROR_TARGET_INVALID = "VISUAL_LOCK_TARGET_INVALID"

ERROR_CODES = (
    ERROR_INVALID_TRANSITION,
    ERROR_ALREADY_FROZEN,
    ERROR_NOT_FOUND,
    ERROR_CONFIRMATION_INVALID,
    ERROR_PROFILE_REQUIRED,
    ERROR_STATE_UNKNOWN,
    ERROR_TARGET_INVALID,
)


class VisualProfileLifecycleError(adapter.VisualProfileLockAdapterError):
    """Fail-fast lifecycle error (shares the registry SystemExit convention)."""

    code = ERROR_INVALID_TRANSITION


def _root(story_root: Path | str | None = None) -> Path:
    return Path(story_root) if story_root else ROOT


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path(ROOT).resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


# --------------------------------------------------------------------------- #
# reading
# --------------------------------------------------------------------------- #

def lifecycle_of(lock) -> str | None:
    """Current lifecycle state of a lock document, or None when unrecognizable."""
    return adapter.lifecycle_of_lock(lock)


def confirmation_of(lock) -> dict[str, Any]:
    """The confirmation record, read from the nested block or the legacy fields."""
    if not isinstance(lock, dict):
        return {"mode": "", "confirmed_by": "", "confirmed_at": "", "reason": None}
    nested = lock.get("confirmation")
    nested = nested if isinstance(nested, dict) else {}
    mode = str(nested.get("mode") or lock.get("confirmation_mode") or "").strip()
    by = str(nested.get("confirmed_by") or lock.get("confirmed_by") or "").strip()
    at = str(nested.get("confirmed_at") or lock.get("confirmed_at") or "").strip()
    reason = nested.get("reason")
    if reason is None:
        reason = lock.get("confirmed_note")
    return {"mode": mode, "confirmed_by": by, "confirmed_at": at, "reason": reason}


def is_confirmed(lock) -> bool:
    """True when the lock carries an adjudicated confirmation record."""
    record = confirmation_of(lock)
    if record["mode"] not in CONFIRMATION_MODES:
        return False
    if record["mode"] in HUMAN_CONFIRMATION_MODES and not record["confirmed_by"]:
        return False
    if not record["confirmed_at"]:
        return False
    return bool(record["confirmed_by"]) or record["mode"] == "system"


def _resolve_target(target, story_root=None) -> tuple[dict, Path | None, Path | None]:
    """Return (lock, lock_path_or_None, episode_dir_or_None).

    target  Episode directory (reads and may write its lock) or a lock document
            (pure, never written).
    """
    if isinstance(target, dict):
        return dict(target), None, None
    if isinstance(target, (str, Path)):
        episode = Path(target)
        existing = adapter.lock_path(episode)
        if existing is None:
            raise VisualProfileLifecycleError(
                f"{_rel(episode)}/{LOCK_REL.as_posix()} does not exist; there is no Visual Lock "
                "to advance",
                ERROR_NOT_FOUND,
            )
        lock, _source = adapter.read_lock(episode)
        if not isinstance(lock, dict):
            raise VisualProfileLifecycleError(
                f"Visual Lock is unreadable or not a JSON object: {_rel(existing)}",
                ERROR_STATE_UNKNOWN,
            )
        return lock, existing, episode
    raise VisualProfileLifecycleError(
        f"target must be an Episode directory or a Visual Lock document, got {type(target).__name__}",
        ERROR_TARGET_INVALID,
    )


# --------------------------------------------------------------------------- #
# transition rules
# --------------------------------------------------------------------------- #

def validate_transition(current, target, *, lock=None) -> dict[str, Any]:
    """Is (current -> target) allowed? Read-only; returns {ok, code, detail}."""
    current = str(current or "").strip()
    target = str(target or "").strip()
    if current not in LIFECYCLE_STATES:
        return {"ok": False, "code": ERROR_STATE_UNKNOWN,
                "detail": f"current lifecycle state {current!r} is not one of {', '.join(LIFECYCLE_STATES)}"}
    if target not in LIFECYCLE_STATES:
        return {"ok": False, "code": ERROR_STATE_UNKNOWN,
                "detail": f"target lifecycle state {target!r} is not one of {', '.join(LIFECYCLE_STATES)}"}
    if current == LIFECYCLE_FROZEN:
        return {"ok": False, "code": ERROR_ALREADY_FROZEN,
                "detail": ("this Visual Lock is FROZEN; a frozen profile may not be modified. "
                           "change the profile by creating a new Episode version instead")}
    allowed = ALLOWED_TRANSITIONS.get(current, ())
    if target not in allowed:
        return {"ok": False, "code": ERROR_INVALID_TRANSITION,
                "detail": (f"{current} -> {target} is not an allowed transition "
                           f"(allowed from {current}: {', '.join(allowed) or 'none'})")}
    return {"ok": True, "code": None, "detail": f"{current} -> {target} is allowed"}


# --------------------------------------------------------------------------- #
# transition application
# --------------------------------------------------------------------------- #

def _note(lock: dict, message: str) -> None:
    notes = lock.get("notes")
    notes = list(notes) if isinstance(notes, list) else []
    notes.append(message)
    lock["notes"] = notes


def _apply_confirmation(lock, *, profile_id, actor, mode, reason, at, story_root) -> dict:
    """Write the confirmation record and adjudicate the selection."""
    resolved_mode = str(mode or "").strip() or "human"
    if resolved_mode not in CONFIRMATION_MODES:
        raise VisualProfileLifecycleError(
            f"confirmation mode {resolved_mode!r} is not one of {', '.join(CONFIRMATION_MODES)}",
            ERROR_CONFIRMATION_INVALID,
        )
    confirmed_by = str(actor or "").strip()
    if resolved_mode in HUMAN_CONFIRMATION_MODES and not confirmed_by:
        raise VisualProfileLifecycleError(
            f"confirmation mode {resolved_mode!r} requires confirmed_by",
            ERROR_CONFIRMATION_INVALID,
        )

    current = lifecycle_of(lock)
    chosen = str(profile_id or lock.get("profile_id") or "").strip()

    if current == LIFECYCLE_NEEDS_CONFIRMATION:
        # The draft named no profile on purpose; the confirmation has to name one,
        # and it has to be one the Selector actually offered.
        if not chosen:
            raise VisualProfileLifecycleError(
                "a needs_confirmation selection must name the confirmed profile_id "
                "(the Selector left the choice open, so it cannot be inferred)",
                ERROR_PROFILE_REQUIRED,
            )
        entry = registry.registry_entry(chosen, story_root)
        if entry is None:
            raise VisualProfileLifecycleError(
                f"confirmed profile_id={chosen!r} is not registered in "
                + registry.REGISTRY_REL.as_posix(),
                registry.ERROR_NOT_REGISTERED,
            )
        if str(entry.get("status") or "").strip() != registry.ACTIVE_STATUS:
            raise VisualProfileLifecycleError(
                f"confirmed profile_id={chosen!r} status={entry.get('status')!r} is not "
                + repr(registry.ACTIVE_STATUS),
                registry.ERROR_NOT_ACTIVE,
            )
        selection = lock.get("selection") if isinstance(lock.get("selection"), dict) else {}
        candidates = [str(item) for item in (selection.get("candidates") or [])]
        if candidates and chosen not in candidates:
            raise VisualProfileLifecycleError(
                f"confirmed profile_id={chosen!r} is not one of the Selector candidates: "
                + ", ".join(candidates),
                ERROR_PROFILE_REQUIRED,
            )
        lock["profile_id"] = chosen
        lock["profile_path"] = str(entry.get("path") or "")
        _note(lock, f"needs_confirmation resolved to {chosen} by {confirmed_by or resolved_mode}")
    elif not chosen:
        raise VisualProfileLifecycleError(
            "this Visual Lock names no profile_id and none was supplied to confirm",
            ERROR_PROFILE_REQUIRED,
        )

    status = str(lock.get("status") or "").strip()
    if status in lock_gate.BLOCKED_STATUSES:
        status = "selected"
    lock["status"] = status or "selected"
    selection = lock.get("selection")
    if isinstance(selection, dict):
        selection = dict(selection)
        selection["status"] = lock["status"]
        selection["adjudication"] = {
            "resolved_profile_id": chosen,
            "by": confirmed_by or resolved_mode,
            "at": at,
            "source": "lifecycle_confirmation",
        }
        lock["selection"] = selection

    lock["confirmation"] = {
        "mode": resolved_mode,
        "confirmed_by": confirmed_by or None,
        "confirmed_at": at,
        "reason": reason,
    }
    lock["confirmation_mode"] = resolved_mode
    lock["confirmed_by"] = confirmed_by or None
    lock["confirmed_at"] = at
    lock["lifecycle_state"] = LIFECYCLE_LOCKED
    lock["lock_policy"] = "advisory_locked"
    _note(lock, f"locked by {confirmed_by or resolved_mode} at {at}")
    return lock


def _apply_freeze(lock, *, actor, reason, at) -> dict:
    """Freeze a locked profile. Inherits, never rewrites, the confirmation record."""
    record = confirmation_of(lock)
    if record["mode"] not in CONFIRMATION_MODES or not record["confirmed_at"]:
        raise VisualProfileLifecycleError(
            "a Visual Lock may only be frozen after it carries a confirmation record",
            ERROR_CONFIRMATION_INVALID,
        )
    if record["mode"] in HUMAN_CONFIRMATION_MODES and not record["confirmed_by"]:
        raise VisualProfileLifecycleError(
            f"confirmation mode {record['mode']!r} requires confirmed_by before freezing",
            ERROR_CONFIRMATION_INVALID,
        )
    lock["confirmation"] = {
        "mode": record["mode"],
        "confirmed_by": record["confirmed_by"] or None,
        "confirmed_at": record["confirmed_at"],
        "reason": record["reason"],
    }
    frozen_by = str(actor or "").strip() or record["confirmed_by"] or record["mode"]
    lock["frozen"] = {
        "frozen_by": frozen_by,
        "frozen_at": at,
        "reason": reason,
        "inherits_confirmation_by": record["confirmed_by"] or None,
    }
    lock["frozen_by"] = frozen_by
    lock["frozen_at"] = at
    lock["lifecycle_state"] = LIFECYCLE_FROZEN
    lock["lock_policy"] = "production_frozen"
    _note(lock, f"frozen by {frozen_by} at {at}")
    return lock


def transition_lock_state(target, next_state, *, profile_id=None, actor=None, mode=None,
                          reason=None, at=None, story_root=None, write: bool = True) -> dict:
    """Advance a Visual Lock to next_state. Returns {lock, from, to, written, path}.

    target      Episode directory (writes meta/visual-profile.json) or a lock
                document (pure: write is ignored because there is no file).
    next_state  LOCKED or FROZEN.
    Raises VisualProfileLifecycleError with an explicit code on an illegal
    transition. The document is only written once the transition is accepted.
    """
    lock, lock_file, _episode = _resolve_target(target, story_root)
    current = lifecycle_of(lock)
    if current is None:
        raise VisualProfileLifecycleError(
            "document declares no recognizable lifecycle state; this is not a governed Visual Lock",
            ERROR_STATE_UNKNOWN,
        )
    verdict = validate_transition(current, next_state, lock=lock)
    if not verdict["ok"]:
        raise VisualProfileLifecycleError(verdict["detail"], verdict["code"])

    stamped = str(at or "").strip() or now_utc()
    updated = dict(lock)
    if str(next_state).strip() == LIFECYCLE_LOCKED:
        updated = _apply_confirmation(updated, profile_id=profile_id, actor=actor,
                                      mode=mode, reason=reason, at=stamped,
                                      story_root=_root(story_root))
    else:
        updated = _apply_freeze(updated, actor=actor, reason=reason, at=stamped)

    written = False
    if write and lock_file is not None:
        story_json.write_json(lock_file, updated)
        written = True
    return {
        "lock": updated,
        "from": current,
        "to": updated["lifecycle_state"],
        "written": written,
        "path": _rel(lock_file) if lock_file is not None else None,
    }


def confirm_visual_lock(target, *, confirmed_by, confirmed_at=None, reason=None,
                        mode: str = "human", profile_id=None, story_root=None,
                        write: bool = True) -> dict:
    """Confirm a SELECTED / NEEDS_CONFIRMATION lock into LOCKED."""
    return transition_lock_state(
        target, LIFECYCLE_LOCKED, profile_id=profile_id, actor=confirmed_by,
        mode=mode, reason=reason, at=confirmed_at, story_root=story_root, write=write,
    )


def freeze_visual_lock(target, *, frozen_by=None, frozen_at=None, reason=None,
                       story_root=None, write: bool = True) -> dict:
    """Freeze a LOCKED profile. A FROZEN lock can never be modified again."""
    return transition_lock_state(
        target, LIFECYCLE_FROZEN, actor=frozen_by, reason=reason, at=frozen_at,
        story_root=story_root, write=write,
    )


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #

def self_test() -> None:
    assert validate_transition(LIFECYCLE_SELECTED, LIFECYCLE_LOCKED)["ok"]
    assert validate_transition(LIFECYCLE_NEEDS_CONFIRMATION, LIFECYCLE_LOCKED)["ok"]
    assert validate_transition(LIFECYCLE_LOCKED, LIFECYCLE_FROZEN)["ok"]
    assert validate_transition(LIFECYCLE_DRAFT, LIFECYCLE_LOCKED)["code"] == ERROR_INVALID_TRANSITION
    assert validate_transition(LIFECYCLE_NEEDS_CONFIRMATION, LIFECYCLE_FROZEN)["code"] == ERROR_INVALID_TRANSITION
    assert validate_transition(LIFECYCLE_FROZEN, LIFECYCLE_LOCKED)["code"] == ERROR_ALREADY_FROZEN
    assert validate_transition(LIFECYCLE_FROZEN, LIFECYCLE_FROZEN)["code"] == ERROR_ALREADY_FROZEN
    assert validate_transition("NOPE", LIFECYCLE_LOCKED)["code"] == ERROR_STATE_UNKNOWN

    with tempfile.TemporaryDirectory(prefix="visual-lock-lifecycle-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / "standards/visual_profiles", root / "standards/visual_profiles")
        episode = root / "episodes" / "99_lifecycle"
        (episode / "meta").mkdir(parents=True)

        selected = {
            "schema_version": 1,
            "lifecycle_state": LIFECYCLE_SELECTED,
            "status": "selected",
            "profile_id": registry.default_profile_id(root),
            "profile_path": registry.registry_entry(registry.default_profile_id(root), root)["path"],
            "selection": {"status": "selected", "candidates": []},
            "selection_evidence": {"selector_version": "1.0", "source": "rule_engine",
                                   "inputs_digest": "sha256:" + "a" * 64,
                                   "matched_rules": ["world=real"], "reason": ["prio=semantic"]},
            "confirmation_mode": "pending",
            "confirmed_by": None,
            "confirmed_at": None,
        }
        story_json.write_json(episode / LOCK_REL, selected)

        assert lifecycle_of(selected) == LIFECYCLE_SELECTED
        assert not is_confirmed(selected)
        report = confirm_visual_lock(episode, confirmed_by="yeqian",
                                     confirmed_at="2026-09-12T00:00:00+08:00",
                                     reason="reviewed", story_root=root)
        assert report["from"] == LIFECYCLE_SELECTED and report["to"] == LIFECYCLE_LOCKED
        assert report["written"] is True
        locked = json.loads((episode / LOCK_REL).read_text(encoding="utf-8"))
        assert locked["lifecycle_state"] == LIFECYCLE_LOCKED
        assert is_confirmed(locked)
        assert locked["confirmation"]["mode"] == "human"
        assert lock_gate.validate_visual_profile_lock(locked, story_root=root)["status"] == "pass"

        frozen = freeze_visual_lock(episode, frozen_by="yeqian",
                                    frozen_at="2026-09-12T01:00:00+08:00",
                                    reason="production started", story_root=root)
        assert frozen["to"] == LIFECYCLE_FROZEN
        frozen_lock = json.loads((episode / LOCK_REL).read_text(encoding="utf-8"))
        assert frozen_lock["confirmation"] == locked["confirmation"]
        try:
            freeze_visual_lock(episode, story_root=root)
            raise AssertionError("a frozen lock must not be modified")
        except VisualProfileLifecycleError as exc:
            assert exc.code == ERROR_ALREADY_FROZEN

        # needs_confirmation must name a profile to lock.
        pending = dict(selected, lifecycle_state=LIFECYCLE_NEEDS_CONFIRMATION,
                       status="needs_confirmation", profile_id="", profile_path="",
                       selection={"status": "needs_confirmation",
                                  "candidates": [registry.default_profile_id(root)]})
        try:
            confirm_visual_lock(pending, confirmed_by="yeqian", story_root=root, write=False)
            raise AssertionError("a needs_confirmation lock must name a profile")
        except VisualProfileLifecycleError as exc:
            assert exc.code == ERROR_PROFILE_REQUIRED
        resolved = confirm_visual_lock(
            pending, confirmed_by="yeqian", story_root=root, write=False,
            profile_id=registry.default_profile_id(root),
        )["lock"]
        assert resolved["lifecycle_state"] == LIFECYCLE_LOCKED
        assert resolved["profile_id"] == registry.default_profile_id(root)
        assert resolved["status"] == "selected"

        # a pure lock document never touches the filesystem
        assert confirm_visual_lock(selected, confirmed_by="x", story_root=root)["written"] is False
    print("VISUAL LOCK LIFECYCLE SELF-TEST PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story OS Visual Lock lifecycle state machine (governance Phase 4.2)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test").set_defaults(func=lambda args: (self_test(), 0)[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

