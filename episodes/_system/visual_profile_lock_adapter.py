#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Visual Lock Runtime Adapter (Visual Profile Governance Phase 4.1).

Why this module exists
----------------------
Phase 3.3 selects a Visual Profile and emits selection evidence; Phase 3.5
verifies that evidence inside a Visual Lock. What was missing was the step that
turns "the Selector picked M01, and here is why" into an Episode-scoped Visual
Lock document, without pretending the choice has already been adjudicated.

    Story Intent + Episode Context + Audience Expectation
            |
            v
    Visual Profile Selector                    (visual_profile_selector.py)
            |
            v
    Selection Evidence                         (selector-evidence.schema.json)
            |
            v
    Visual Lock DRAFT -> meta/visual-profile.json        <-- this module
            |
            v
    (Phase 4.2 owns confirmation; Phase 4.3 owns the Gate)

Boundaries
----------
- Selection layer only. It writes exactly one document (the Episode Visual Lock
  draft) and reads the registry. It never produces images and never runs
  production.
- It never picks a profile itself (the Selector does), never confirms one, never
  re-selects for an Episode that already has a lock, and never overwrites an
  existing lock file.
- It does not touch episode-state.json, story-gates.json, Frame Contracts, the
  production ledger, machine_gate or any Runtime file.
- A draft is NOT a lock. A draft declares confirmation_mode="pending", which the
  Phase 3.5 lock contract deliberately does not accept, so a draft can never be
  mistaken for adjudicated evidence and no lock can be created here.

Lifecycle
---------
    DRAFT -> SELECTED -> NEEDS_CONFIRMATION -> LOCKED -> FROZEN

Only SELECTED and NEEDS_CONFIRMATION are produced here. Nothing in this module
can move a lock to LOCKED/FROZEN: that needs the Phase 4.2 confirmation record
(confirmed_by + confirmed_at) written by whoever is allowed to adjudicate.
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import story_json
import visual_profile_registry as registry
import visual_profile_selector as selector

ROOT = Path(__file__).resolve().parents[2]

# Single Visual Lock location. Phase 3.5 already reads this path; the adapter
# deliberately adds no fourth store.
LOCK_REL = Path("meta/visual-profile.json")
LOCK_ALT_REL = Path("meta/visual_profile.json")
RUNTIME_REQUEST_REL = Path("meta/runtime-request.json")

ADAPTER_VERSION = "1.0"

LIFECYCLE_DRAFT = "DRAFT"
LIFECYCLE_SELECTED = "SELECTED"
LIFECYCLE_NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
LIFECYCLE_LOCKED = "LOCKED"
LIFECYCLE_FROZEN = "FROZEN"
LIFECYCLE_STATES = (
    LIFECYCLE_DRAFT,
    LIFECYCLE_SELECTED,
    LIFECYCLE_NEEDS_CONFIRMATION,
    LIFECYCLE_LOCKED,
    LIFECYCLE_FROZEN,
)
# A freshly created Episode may only carry one of these two states. LOCKED and
# FROZEN require an explicit confirmation record and are never auto-written.
WRITABLE_LIFECYCLE_STATES = (LIFECYCLE_SELECTED, LIFECYCLE_NEEDS_CONFIRMATION)

CONFIRMATION_PENDING = "pending"
LOCK_POLICY = "advisory_draft_only"

ERROR_DRAFT_INVALID = "VISUAL_PROFILE_LOCK_DRAFT_INVALID"
ERROR_LOCK_EXISTS = "VISUAL_PROFILE_LOCK_EXISTS"
ERROR_LIFECYCLE_INVALID = "VISUAL_PROFILE_LIFECYCLE_INVALID"


class VisualProfileLockAdapterError(registry.VisualProfileError):
    """Fail-fast adapter error (shares the registry SystemExit convention)."""

    code = ERROR_DRAFT_INVALID


def _root(story_root: Path | str | None = None) -> Path:
    return Path(story_root) if story_root else ROOT


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# lifecycle
# --------------------------------------------------------------------------- #

def lifecycle_for_status(status: str) -> str:
    """Map a selector status to the lifecycle state this adapter may write.

    selected / defaulted  -> SELECTED (a profile is named, nothing is confirmed)
    needs_confirmation    -> NEEDS_CONFIRMATION (no profile may be named yet)
    rejected              -> DRAFT (a rejected request never reaches a draft)
    """
    if status in (selector.STATUS_SELECTED, selector.STATUS_DEFAULTED):
        return LIFECYCLE_SELECTED
    if status == selector.STATUS_NEEDS_CONFIRMATION:
        return LIFECYCLE_NEEDS_CONFIRMATION
    if status == selector.STATUS_REJECTED:
        return LIFECYCLE_DRAFT
    raise VisualProfileLockAdapterError(
        f"unknown selector status {status!r}; expected one of " + ", ".join(selector.STATUSES),
        ERROR_LIFECYCLE_INVALID,
    )


def lifecycle_of_lock(lock) -> str | None:
    """Read the lifecycle state of an existing Visual Lock document.

    Returns None for a document that declares no lifecycle and no selector status
    (a pre-governance V2.2.4 episode meta lock, for example), so an unmanaged
    Episode is reported as unmanaged instead of being given an invented state.
    """
    if not isinstance(lock, dict):
        return None
    declared = str(lock.get("lifecycle_state") or "").strip()
    if declared in LIFECYCLE_STATES:
        return declared
    if str(lock.get("lock_status") or "").strip().lower() == "locked":
        return LIFECYCLE_LOCKED
    raw = lock.get("status")
    if not isinstance(raw, str) or not raw.strip():
        raw = lock.get("selection") if isinstance(lock.get("selection"), str) else None
    status = str(raw or "").strip()
    if status not in selector.STATUSES:
        return None
    mode = str(lock.get("confirmation_mode") or "").strip()
    if mode and mode != CONFIRMATION_PENDING:
        return LIFECYCLE_LOCKED
    return lifecycle_for_status(status)


# --------------------------------------------------------------------------- #
# selector input + draft
# --------------------------------------------------------------------------- #

def build_selector_input(
    *,
    story_intent: dict | None = None,
    episode_context: dict | None = None,
    audience_expectation: dict | None = None,
    forced_profile_id: str | None = None,
) -> dict:
    """Build a Selector Input (Phase 3.2 contract) from Episode creation facts.

    Only declared story facts are used. Phase 4.1 has no title/request-text to
    Story Intent model, so a one-sentence creation still reaches the Selector with
    an empty story intent and therefore resolves to the registry default profile,
    exactly as before. Guessing a world from a title would be a silent substitute,
    which is what the Visual Profile governance chain exists to prevent.
    """
    intent = dict(story_intent or {})
    intent.setdefault("world", "")
    payload: dict[str, Any] = {"story_intent": intent}
    context = {k: v for k, v in dict(episode_context or {}).items() if v not in (None, "")}
    if context:
        payload["episode_context"] = context
    audience = {k: v for k, v in dict(audience_expectation or {}).items() if v not in (None, "")}
    if audience:
        payload["audience_expectation"] = audience
    forced = str(forced_profile_id or "").strip()
    if forced:
        payload["user_override"] = {"forced_profile_id": forced}
    return payload


def create_visual_lock_draft(selector_input, selector_output, *, story_root=None) -> dict:
    """Convert a Selector Output into a Visual Lock draft (never a lock).

    The draft copies the selection evidence verbatim and names a profile only when
    the Selector actually selected one. A needs_confirmation outcome names no
    profile: the candidates stay in selection.candidates until a human adjudicates.
    """
    root = _root(story_root)
    if not isinstance(selector_output, dict):
        raise VisualProfileLockAdapterError("selector output must be a JSON object")
    status = str(selector_output.get("status") or "").strip()
    if status not in selector.STATUSES:
        raise VisualProfileLockAdapterError(
            f"selector output status {status!r} is not one of " + ", ".join(selector.STATUSES)
        )
    if status == selector.STATUS_REJECTED:
        raise VisualProfileLockAdapterError(
            "the Selector rejected this request; no Visual Lock draft may be written",
            selector.ERROR_SELECTION_REJECTED,
        )

    evidence = selector_output.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        raise VisualProfileLockAdapterError(
            "selector output carries no selection evidence; "
            "a Visual Lock draft without evidence is not allowed"
        )
    evidence_errors = selector.validate_selector_evidence(evidence, root)
    if evidence_errors:
        raise VisualProfileLockAdapterError(
            "selection evidence is not contract-conformant: " + "; ".join(evidence_errors)
            + f" (selector input {selector_input!r})"
        )

    lifecycle = lifecycle_for_status(status)
    candidates = [
        str(candidate.get("profile"))
        for candidate in (selector_output.get("candidates") or [])
        if isinstance(candidate, dict) and candidate.get("profile")
    ]
    notes: list[str] = []
    profile_id = ""
    profile_path = ""

    if lifecycle == LIFECYCLE_SELECTED:
        profile_id = str(selector_output.get("selected_profile") or "").strip()
        if not profile_id:
            raise VisualProfileLockAdapterError(
                "a selected selector output must name selected_profile"
            )
        entry = registry.registry_entry(profile_id, root)
        if entry is None:
            raise VisualProfileLockAdapterError(
                f"selected profile_id={profile_id!r} is not registered in "
                + registry.REGISTRY_REL.as_posix(),
                registry.ERROR_NOT_REGISTERED,
            )
        entry_status = str(entry.get("status") or "").strip()
        if entry_status != registry.ACTIVE_STATUS:
            raise VisualProfileLockAdapterError(
                f"selected profile_id={profile_id!r} status={entry_status!r} is not "
                + repr(registry.ACTIVE_STATUS),
                registry.ERROR_NOT_ACTIVE,
            )
        profile_path = str(entry.get("path") or "")
        if candidates:
            notes.append("other profiles also matched: " + ", ".join(candidates))
    else:
        notes.append(
            "selection is not adjudicated: no profile is named until a confirmation is recorded"
        )

    return {
        "schema_version": 1,
        "adapter_version": ADAPTER_VERSION,
        "lifecycle_state": lifecycle,
        "lock_policy": LOCK_POLICY,
        "status": status,
        "profile_id": profile_id,
        "profile_path": profile_path,
        "selection": {
            "status": status,
            "source": str(evidence.get("source") or ""),
            "selector_version": str(evidence.get("selector_version") or ""),
            "candidates": candidates,
            "inputs_summary": dict(evidence.get("inputs_summary") or {}),
        },
        "selection_evidence": dict(evidence),
        "confirmation_mode": CONFIRMATION_PENDING,
        "confirmed_by": None,
        "confirmed_at": None,
        "draft_created_at": now_utc(),
        "notes": notes,
    }


# --------------------------------------------------------------------------- #
# Episode lock file
# --------------------------------------------------------------------------- #

def lock_path(episode) -> Path | None:
    """Return the existing Visual Lock path for an Episode, or None."""
    ep = Path(episode)
    for rel in (LOCK_REL, LOCK_ALT_REL):
        candidate = ep / rel
        if candidate.is_file():
            return candidate
    return None


def read_lock(episode) -> tuple:
    """Read an Episode Visual Lock. Returns (document, repo-relative path)."""
    path = lock_path(episode)
    if path is None:
        return None, None
    rel = (LOCK_REL if path.name == LOCK_REL.name else LOCK_ALT_REL).as_posix()
    data = story_json.read_json(path, default=None, require_object=True)
    if not isinstance(data, dict):
        raise VisualProfileLockAdapterError(
            f"existing Visual Lock is unreadable or not a JSON object: {rel}",
            registry.ERROR_FILE_INVALID,
        )
    return data, rel


def write_visual_lock_draft(episode, draft, *, story_root=None) -> Path:
    """Write one Visual Lock draft. Refuses to overwrite an existing lock."""
    ep = Path(episode)
    if not isinstance(draft, dict):
        raise VisualProfileLockAdapterError("draft must be a JSON object")
    existing = lock_path(ep)
    if existing is not None:
        raise VisualProfileLockAdapterError(
            f"refusing to overwrite an existing Visual Lock: {existing}",
            ERROR_LOCK_EXISTS,
        )
    lifecycle = str(draft.get("lifecycle_state") or "").strip()
    if lifecycle not in WRITABLE_LIFECYCLE_STATES:
        raise VisualProfileLockAdapterError(
            f"lifecycle_state={lifecycle!r} may not be written by this adapter "
            f"(allowed: {', '.join(WRITABLE_LIFECYCLE_STATES)})",
            ERROR_LIFECYCLE_INVALID,
        )
    if not isinstance(draft.get("selection_evidence"), dict) or not draft["selection_evidence"]:
        raise VisualProfileLockAdapterError("a Visual Lock draft must carry selection_evidence")
    target = ep / LOCK_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    story_json.write_json(target, draft)
    return target


def ensure_visual_lock(
    episode,
    *,
    selector_input=None,
    story_root=None,
    write: bool = True,
) -> dict:
    """Produce the Visual Lock report for one Episode.

    An Episode that already carries a Visual Lock is read and reported as-is: the
    Selector is not re-run and nothing is overwritten. Otherwise the Selector runs
    and a SELECTED / NEEDS_CONFIRMATION draft is written unless write=False.

    Raises VisualProfileSelectionError (fail closed) for an invalid Selector input
    or an unregistered forced profile id, and VisualProfileLockAdapterError when no
    legal draft can be produced.
    """
    ep = Path(episode)
    root = _root(story_root)

    existing, source = read_lock(ep)
    if existing is not None:
        return {
            "source": "existing",
            "written": False,
            "lock_path": source,
            "lifecycle_state": lifecycle_of_lock(existing),
            "selector_output": None,
            "draft": None,
            "profile_id": str(existing.get("profile_id") or "").strip() or None,
            "status": str(existing.get("status") or "").strip() or None,
        }

    payload = selector_input if isinstance(selector_input, dict) else build_selector_input()
    output = selector.select(payload, story_root=root, strict=True)
    draft = create_visual_lock_draft(payload, output, story_root=root)
    written = False
    if write:
        write_visual_lock_draft(ep, draft, story_root=root)
        written = True
    return {
        "source": "selector",
        "written": written,
        "lock_path": LOCK_REL.as_posix() if written else None,
        "lifecycle_state": draft["lifecycle_state"],
        "selector_output": output,
        "draft": draft,
        "profile_id": draft["profile_id"] or None,
        "status": output["status"],
    }


def selection_record(report: dict) -> dict:
    """The runtime-request summary of an automatic Visual Profile selection.

    Phase 3.5 treats this record as the Episode declaring that it needs a governed
    Visual Lock, so it is written only for a selection made by this adapter.
    """
    output = report.get("selector_output") or {}
    evidence = output.get("evidence") if isinstance(output, dict) else None
    record = {
        "adapter_version": ADAPTER_VERSION,
        "source": "selector",
        "status": report.get("status"),
        "lifecycle_state": report.get("lifecycle_state"),
        "selected_profile": report.get("profile_id"),
        "lock_path": report.get("lock_path") or LOCK_REL.as_posix(),
        "written": bool(report.get("written")),
        "requires_confirmation": report.get("lifecycle_state") != LIFECYCLE_LOCKED,
    }
    if isinstance(evidence, dict):
        record["selection_evidence"] = evidence
    return record


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #

def self_test() -> None:
    assert lifecycle_for_status(selector.STATUS_SELECTED) == LIFECYCLE_SELECTED
    assert lifecycle_for_status(selector.STATUS_DEFAULTED) == LIFECYCLE_SELECTED
    assert lifecycle_for_status(selector.STATUS_NEEDS_CONFIRMATION) == LIFECYCLE_NEEDS_CONFIRMATION
    assert lifecycle_of_lock({"status": "selected", "confirmation_mode": "human",
                              "confirmed_by": "x", "confirmed_at": "t"}) == LIFECYCLE_LOCKED
    assert lifecycle_of_lock({"profile_id": "M00", "mode": "explicit_user_locked"}) is None

    with tempfile.TemporaryDirectory(prefix="visual-lock-adapter-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / "standards/visual_profiles", root / "standards/visual_profiles")

        payload = build_selector_input(story_intent={"world": "historical_real", "era": "ancient"})
        output = selector.select(payload, story_root=root)
        draft = create_visual_lock_draft(payload, output, story_root=root)
        assert draft["lifecycle_state"] == LIFECYCLE_SELECTED
        assert draft["profile_id"] == selector.M01
        assert draft["profile_path"] == registry.registry_entry(selector.M01, root)["path"]
        assert draft["confirmation_mode"] == CONFIRMATION_PENDING
        assert draft["selection_evidence"]["inputs_digest"].startswith("sha256:")
        assert draft["selection"]["candidates"] == []

        episode = root / "episodes" / "99_selftest"
        written = write_visual_lock_draft(episode, draft)
        assert written.is_file()
        again, rel = read_lock(episode)
        assert again == draft and rel == LOCK_REL.as_posix()
        assert ensure_visual_lock(episode, selector_input=payload, story_root=root)["source"] == "existing"
        try:
            write_visual_lock_draft(episode, draft)
            raise AssertionError("an existing Visual Lock must not be overwritten")
        except VisualProfileLockAdapterError as exc:
            assert exc.code == ERROR_LOCK_EXISTS

        ambiguous = build_selector_input(story_intent={
            "world": "historical_real", "era": "ancient",
            "location": "\u6c5f\u5357", "experience_type": "immersive_first_person",
        })
        pending = create_visual_lock_draft(
            ambiguous, selector.select(ambiguous, story_root=root), story_root=root
        )
        assert pending["lifecycle_state"] == LIFECYCLE_NEEDS_CONFIRMATION
        assert pending["profile_id"] == ""
        assert len(pending["selection"]["candidates"]) == 2

        report = ensure_visual_lock(root / "episodes" / "99_ensure",
                                    selector_input=payload, story_root=root)
        assert report["written"] is True
        assert report["lifecycle_state"] == LIFECYCLE_SELECTED
        assert selection_record(report)["selected_profile"] == selector.M01
    print("VISUAL LOCK ADAPTER SELF-TEST PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story OS Visual Lock runtime adapter (governance Phase 4.1)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test").set_defaults(func=lambda args: (self_test(), 0)[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
