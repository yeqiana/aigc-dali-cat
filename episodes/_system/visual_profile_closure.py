#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Visual Profile Production Closure (Visual Profile Governance Phase 4.6-B).

Why this module exists
----------------------
Phase 4.2 can move a Visual Lock from LOCKED to FROZEN, but nothing in the runtime ever
performed that second transition on its own, so an Episode could reach PRODUCTION_PASSED
carrying a LOCKED profile that was never frozen. Phase 4.6-B closes that gap without
inventing new policy: it watches for the first committed Production Asset and asks the
canonical lifecycle to freeze the profile.

    Visual Lock LOCKED
            |
    ... production generates, reviews, repairs, promotes ...
            |
    first formal Production Asset committed        <-- production ledger promote
            |
    freeze_on_first_asset_commit()                 <-- this module
            |
    Visual Lock FROZEN

What counts as a formal Production Asset
----------------------------------------
Exactly the moment production_ledger_manage.cmd_promote copies a reviewed PASSED frame
candidate into the Episode approved asset root and writes frames[NN].approved_asset. That
is the only place in the repository that writes approved_asset, and it is the same fact the
machine gate later consumes as production.frames.NN.approved_asset.

Deliberately NOT a trigger: provider request sent, raw image written, candidate generated,
backend exit code zero, provider receipt received, review pending, repair pending.

Boundaries
----------
Canonical only: it never writes lifecycle_state itself. It calls
visual_profile_lock_lifecycle.freeze_visual_lock().
It never confirms a profile. A SELECTED / NEEDS_CONFIRMATION / DRAFT lock is reported as a
failure; it is never auto-locked, and no confirmed_by or confirmation record is ever
synthesized so that production can continue.
Legacy / ungoverned Episodes are skipped, never failed and never frozen, so a historical
Episode cannot be hurt by this hook.
Idempotent and race-safe: concurrent frames serialize on the existing runtime_atomic_store
FileLock and re-read the lock inside it, so only one legal LOCKED to FROZEN transition
happens and later triggers are NOOP.
Advisory with respect to production: the caller treats any failure as a diagnostic. This
module never touches episode-state.json, story-gates.json, Frame Contracts or Runtime.

Phase 4.6.1 recovery: reconcile_episode()
----------------------------------------
The promote hook only fires on a promotion. When a promotion happens while the profile is not
yet LOCKED the hook fails safely, and nothing re-triggers it after a later confirmation, so an
Episode can be left at LOCKED + approved_asset + not FROZEN and machine_gate then reports
VISUAL_PROFILE_NOT_FROZEN. reconcile_episode() is the idempotent recovery for exactly that
state: on a governed LOCKED profile that already has a committed formal Production Asset it
performs the same canonical LOCKED -> FROZEN transition as the hook, with trigger
production_closure_reconcile. It can only ever add FROZEN: it never confirms a profile, never
auto-locks a draft, never migrates a legacy Episode and never writes a second lock.

Result contract
---------------
    status   frozen | noop | skipped | fail
    code     explicit error code for fail, else None

    frozen   the profile has just been frozen by this call
    noop     already FROZEN, or a racing frame won; nothing was written
    skipped  legacy / ungoverned Episode: not managed by this closure
    fail     an unadjudicated lock reached an asset commit, or the canonical freeze failed

Trigger evidence inside the lock carries frame and production_attempt_id. When the ledger has
no stable attempt id for the promoted asset the field is None rather than being fabricated.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import runtime_atomic_store as atomic_store  # noqa: E402
import story_json  # noqa: E402
import visual_profile_lock as lock_gate  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_lock_lifecycle as lifecycle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

CLOSURE_VERSION = "1.0"

LEDGER_REL = Path("meta/production-ledger.json")
LOCK_REL = adapter.LOCK_REL

FREEZE_TRIGGER = "first_production_asset_committed"
# Phase 4.6.1: the recovery path records a trigger of its own so a frozen lock still says which
# closure produced it (a live promotion, or a resume/postflight reconciliation).
RECONCILE_TRIGGER = "production_closure_reconcile"

RESULT_FROZEN = "frozen"
RESULT_NOOP = "noop"
RESULT_SKIPPED = "skipped"
RESULT_FAIL = "fail"
RESULT_STATUSES = (RESULT_FROZEN, RESULT_NOOP, RESULT_SKIPPED, RESULT_FAIL)

# Reuses the canonical production-gate vocabulary for the one state error this hook can
# raise, so a repair rule and a reader need no second code language.
ERROR_NOT_LOCKED = "VISUAL_PROFILE_NOT_LOCKED"
ERROR_FREEZE_FAILED = "VISUAL_PROFILE_FREEZE_FAILED"

ERROR_CODES = (ERROR_NOT_LOCKED, ERROR_FREEZE_FAILED)


def _root(story_root=None) -> Path:
    return Path(story_root) if story_root else ROOT


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _result(status: str, code=None, **extra: Any) -> dict:
    payload = {"status": status, "code": code, "closure_version": CLOSURE_VERSION}
    payload.update(extra)
    return payload


# --------------------------------------------------------------------------- #
# production fact: which frames carry a committed (promoted) asset
# --------------------------------------------------------------------------- #

def load_ledger(episode) -> dict:
    data = story_json.read_json(Path(episode) / LEDGER_REL, default={})
    return data if isinstance(data, dict) else {}


def _attempt_id_for(frame: dict, info: dict):
    """The generation attempt that produced the promoted asset, or None.

    cmd_promote records approved_asset.source_sha256 from the frame candidate, and the
    candidate records the attempt that produced it. When that chain is absent (an older
    ledger shape) the id stays None instead of being invented.
    """
    candidate = frame.get("current_candidate")
    if not isinstance(candidate, dict) or not candidate.get("attempt_id"):
        return None
    source_sha = info.get("source_sha256")
    if source_sha and candidate.get("sha256") != source_sha:
        return None
    return str(candidate["attempt_id"])


def committed_assets(episode) -> list:
    """Every frame whose approved asset has been committed, oldest promote first.

    Read-only. It reports ledger facts; it never promotes, locks or freezes a frame.
    """
    frames = load_ledger(episode).get("frames")
    if not isinstance(frames, dict):
        return []
    found = []
    for key in sorted(frames):
        frame = frames.get(key)
        if not isinstance(frame, dict):
            continue
        info = frame.get("approved_asset")
        if not isinstance(info, dict) or not info.get("path") or not info.get("sha256"):
            continue
        lock = frame.get("lock") if isinstance(frame.get("lock"), dict) else {}
        found.append({
            "frame": key,
            "path": info.get("path"),
            "sha256": info.get("sha256"),
            "promoted_at": info.get("promoted_at"),
            "status": frame.get("status"),
            "locked": frame.get("status") == "LOCKED",
            "locked_sha256": lock.get("sha256"),
            "attempt_id": _attempt_id_for(frame, info),
        })
    found.sort(key=lambda item: (str(item.get("promoted_at") or ""), str(item["frame"])))
    return found


def first_committed_asset(episode):
    """The first formal Production Asset committed for this Episode, or None."""
    assets = committed_assets(episode)
    return assets[0] if assets else None


def _frame_key(frame):
    """Normalize an int or string frame identifier to the ledger key form."""
    if isinstance(frame, bool):
        return str(frame)
    if isinstance(frame, int):
        return "{:02d}".format(frame)
    raw = str(frame or "").strip()
    return "{:02d}".format(int(raw)) if raw.isdigit() else raw


def _committed_asset(episode, frame=None):
    """The committed (promoted) asset this freeze is about, or None.

    The hook verifies the production fact instead of trusting its caller: a provider
    success or a raw candidate is not a formal Production Asset.
    """
    assets = committed_assets(episode)
    if frame is None:
        return assets[0] if assets else None
    key = _frame_key(frame)
    for asset in assets:
        if asset["frame"] == key:
            return asset
    return None


def governed(episode) -> bool:
    """True when the Episode carries a Visual Lock claiming the Phase 3.5 contract."""
    lock, _source, error = lock_gate.load_lock(Path(episode))
    if error or lock is None:
        return False
    return lock_gate.lock_is_governed(lock)


def required_for_production(episode) -> bool:
    """True when this profile must already be FROZEN: governed and already producing.

    Used by machine_gate to ask for the frozen lifecycle state without making any
    lifecycle judgement of its own. A legacy or asset-less Episode is never asked.
    """
    return governed(episode) and first_committed_asset(episode) is not None


# --------------------------------------------------------------------------- #
# freeze
# --------------------------------------------------------------------------- #

def freeze_on_first_asset_commit(episode, *, frame=None, attempt_id=None, reason=None,
                                 story_root=None, frozen_at=None,
                                 timeout: float | None = None) -> dict:
    """Freeze a LOCKED Visual Lock because a formal Production Asset was committed.

    episode         Episode directory.
    frame           frame key that was just promoted, when the caller knows it.
    attempt_id      production attempt that produced it, when the caller knows it.
    reason          optional freeze reason; a factual default is used otherwise.
    story_root      repository root used to resolve the registry (tests).
    frozen_at       optional fixed timestamp (tests).
    timeout         optional FileLock wait override; None defers to the canonical
                    runtime_atomic_store.FileLock default so no second policy lives here.

    Never raises for a managed outcome: every result is a status dict, because the caller
    must be able to treat a closure failure as a diagnostic rather than a production
    failure.

    Returns skipped when no formal asset has actually been committed for the Episode,
    or for the named frame, so a provider success or a raw candidate alone can never
    freeze a profile.
    """
    ep = Path(episode)
    root = _root(story_root)

    lock, source, error = lock_gate.load_lock(ep)
    if error:
        return _result(RESULT_FAIL, lock_gate.ERROR_LOCK_UNREADABLE, detail=error, path=source)
    if lock is None:
        return _result(RESULT_SKIPPED, None,
                       reason="episode carries no " + LOCK_REL.as_posix() + "; nothing to freeze")
    if not lock_gate.lock_is_governed(lock):
        return _result(RESULT_SKIPPED, None,
                       reason="pre-governance visual lock is not managed by this closure")

    state = lifecycle.lifecycle_of(lock)
    if state == lifecycle.LIFECYCLE_FROZEN:
        return _result(RESULT_NOOP, None, lifecycle_state=state,
                       reason="visual profile is already FROZEN; nothing to write")
    if state != lifecycle.LIFECYCLE_LOCKED:
        return _result(
            RESULT_FAIL, ERROR_NOT_LOCKED, lifecycle_state=state,
            detail=("lifecycle_state=" + repr(state) + " must be " + lifecycle.LIFECYCLE_LOCKED
                    + " before a committed production asset may freeze the profile; this hook"
                    " never confirms an unadjudicated lock and never auto-locks a draft"),
        )

    committed = _committed_asset(ep, frame)
    if committed is None:
        where = ("frame " + _frame_key(frame)) if frame is not None else "this Episode"
        return _result(
            RESULT_SKIPPED, None,
            reason=("no committed production asset for " + where
                    + "; a provider success or a raw candidate is not a formal asset"),
        )
    committed_frame = committed["frame"]
    committed_attempt = attempt_id if attempt_id is not None else committed["attempt_id"]

    lock_file = adapter.lock_path(ep)
    if lock_file is None:
        return _result(RESULT_SKIPPED, None,
                       reason="Visual Lock file is no longer present; nothing to freeze")

    evidence = {
        "trigger": FREEZE_TRIGGER,
        "recorded_at": now_utc(),
        "frame": str(committed_frame) if committed_frame else None,
        "production_attempt_id": str(committed_attempt) if committed_attempt else None,
    }
    message = reason or ("first formal production asset committed"
                         + (" (frame " + str(committed_frame) + ")" if committed_frame else ""))

    try:
        # Reuse the existing runtime lock primitive; no third locking system.
        lock_kwargs = {} if timeout is None else {"timeout": timeout}
        with atomic_store.FileLock(lock_file, **lock_kwargs):
            current, _current_source, current_error = lock_gate.load_lock(ep)
            if current_error:
                return _result(RESULT_FAIL, lock_gate.ERROR_LOCK_UNREADABLE, detail=current_error)
            current_state = lifecycle.lifecycle_of(current)
            if current_state == lifecycle.LIFECYCLE_FROZEN:
                return _result(RESULT_NOOP, None, lifecycle_state=current_state,
                               reason="another frame already froze this profile")
            if current_state != lifecycle.LIFECYCLE_LOCKED:
                return _result(
                    RESULT_FAIL, ERROR_NOT_LOCKED, lifecycle_state=current_state,
                    detail=("lifecycle_state=" + repr(current_state) + " changed while waiting for"
                            " the freeze lock; a committed asset may only freeze a LOCKED profile"),
                )
            report = lifecycle.freeze_visual_lock(
                ep, frozen_at=frozen_at, reason=message, story_root=root, evidence=evidence)
    except Exception as exc:  # a closure failure is never a production failure
        return _result(RESULT_FAIL, ERROR_FREEZE_FAILED, detail=type(exc).__name__ + ": " + str(exc))

    return _result(
        RESULT_FROZEN, None, lifecycle_state=lifecycle.LIFECYCLE_FROZEN,
        from_state=report.get("from"), to_state=report.get("to"),
        frame=evidence["frame"], production_attempt_id=evidence["production_attempt_id"],
        path=report.get("path"), evidence=evidence,
    )


# --------------------------------------------------------------------------- #
# recovery: reconcile an interrupted / late-confirmed closure (Phase 4.6.1)
# --------------------------------------------------------------------------- #

def reconcile_episode(episode, *, story_root=None, reason=None, frozen_at=None,
                      timeout: float | None = None) -> dict:
    """Restore the Visual Profile closure from the facts as they are right now.

    The promote hook only runs at a promotion. If an approved asset was committed while the
    profile was not yet LOCKED, the hook failed safely and a later confirmation leaves the
    Episode at LOCKED + committed asset + not FROZEN; no new promotion will re-trigger it. This
    is the recovery for that one state, and for nothing else:

        Case A  no Visual Lock, or pre-governance / unmanaged  -> skipped (never migrated)
        Case B  DRAFT / SELECTED / NEEDS_CONFIRMATION + asset   -> fail VISUAL_PROFILE_NOT_LOCKED
        Case C  LOCKED, no committed asset                      -> noop (FROZEN is not owed)
        Case D  LOCKED + committed asset                        -> LOCKED -> FROZEN (canonical)
        Case E  FROZEN                                          -> noop (file untouched)

    It can only ever add FROZEN. It never confirms a profile, never auto-locks a draft, never
    writes selector evidence and never migrates a legacy Episode. The transition itself goes
    through visual_profile_lock_lifecycle.freeze_visual_lock, exactly like the promote hook.

    episode     Episode directory.
    story_root  repository root used to resolve the registry (tests).
    reason      optional reconcile reason; a factual default is used otherwise. It is recorded
                twice: as the freeze reason and as frozen.reconcile_reason.
    frozen_at   optional fixed timestamp (tests).
    timeout     optional FileLock wait override; None defers to the canonical
                runtime_atomic_store.FileLock default so no second policy lives here.

    Never raises for a managed outcome: the caller must be able to treat the result as a
    status. A fail is never a "continue" signal.
    """
    ep = Path(episode)
    root = _root(story_root)

    lock, source, error = lock_gate.load_lock(ep)
    if error:
        return _result(RESULT_FAIL, lock_gate.ERROR_LOCK_UNREADABLE, detail=error, path=source)
    if lock is None:
        # Case A: no Visual Lock. A legacy Episode is never migrated or given a lock.
        return _result(RESULT_SKIPPED, None, lifecycle_state=None,
                       reason="episode carries no " + LOCK_REL.as_posix()
                              + "; nothing to reconcile")
    if not lock_gate.lock_is_governed(lock):
        # Case A: pre-governance V2.2.4 meta lock. Presence is not governance evidence.
        return _result(RESULT_SKIPPED, None, lifecycle_state=lifecycle.lifecycle_of(lock),
                       reason="pre-governance visual lock is not managed by this closure")

    state = lifecycle.lifecycle_of(lock)
    if state == lifecycle.LIFECYCLE_FROZEN:
        # Case E: already FROZEN. The file must not change at all.
        return _result(RESULT_NOOP, None, lifecycle_state=state,
                       reason="visual profile is already FROZEN; nothing to reconcile")

    committed = first_committed_asset(ep)
    if committed is None:
        # Case C (and the asset-less half of Case B): without a formal Production Asset there is
        # nothing to freeze, so LOCKED stays LOCKED and an unadjudicated draft stays unadjudicated.
        return _result(RESULT_NOOP, None, lifecycle_state=state,
                       reason="no committed production asset for this Episode; FROZEN is not owed")

    if state != lifecycle.LIFECYCLE_LOCKED:
        # Case B: an approved asset exists but the profile was never adjudicated. Report it and
        # stop; this recovery never confirms a profile to make production continue.
        return _result(
            RESULT_FAIL, ERROR_NOT_LOCKED, lifecycle_state=state,
            detail=("a committed production asset exists while lifecycle_state=" + repr(state)
                    + "; only a real confirmation may move it to LOCKED, and this recovery never"
                    " confirms, auto-locks or migrates a profile"),
        )

    # Case D: LOCKED + committed asset -> the canonical LOCKED -> FROZEN transition.
    committed_frame = committed["frame"]
    committed_attempt = committed["attempt_id"]
    reconcile_reason = reason or ("committed production asset exists while visual profile "
                                  "remained " + str(state))
    evidence = {
        "trigger": RECONCILE_TRIGGER,
        "recorded_at": now_utc(),
        "frame": str(committed_frame) if committed_frame else None,
        "production_attempt_id": str(committed_attempt) if committed_attempt else None,
        "reconcile_reason": reconcile_reason,
    }
    message = reason or ("production closure reconciled: a committed production asset exists"
                         + (" (frame " + str(committed_frame) + ")" if committed_frame else ""))

    lock_file = adapter.lock_path(ep)
    if lock_file is None:
        return _result(RESULT_SKIPPED, None,
                       reason="Visual Lock file is no longer present; nothing to reconcile")

    try:
        # Reuse the existing runtime lock primitive; no third locking system.
        lock_kwargs = {} if timeout is None else {"timeout": timeout}
        with atomic_store.FileLock(lock_file, **lock_kwargs):
            current, _current_source, current_error = lock_gate.load_lock(ep)
            if current_error:
                return _result(RESULT_FAIL, lock_gate.ERROR_LOCK_UNREADABLE, detail=current_error)
            current_state = lifecycle.lifecycle_of(current)
            if current_state == lifecycle.LIFECYCLE_FROZEN:
                # A concurrent reconciliation already froze this profile: this call is a noop.
                return _result(RESULT_NOOP, None, lifecycle_state=current_state,
                               reason="another reconcile already froze this profile")
            if current_state != lifecycle.LIFECYCLE_LOCKED:
                return _result(RESULT_NOOP, None, lifecycle_state=current_state,
                               reason=("lifecycle_state=" + repr(current_state) + " changed while"
                                       " waiting for the reconcile lock; nothing to freeze"))
            report = lifecycle.freeze_visual_lock(
                ep, frozen_at=frozen_at, reason=message, story_root=root, evidence=evidence)
    except Exception as exc:  # a closure failure is a diagnostic, never a crash
        return _result(RESULT_FAIL, ERROR_FREEZE_FAILED,
                       detail=type(exc).__name__ + ": " + str(exc))

    return _result(
        RESULT_FROZEN, None, lifecycle_state=lifecycle.LIFECYCLE_FROZEN,
        from_state=report.get("from"), to_state=report.get("to"),
        frame=evidence["frame"], production_attempt_id=evidence["production_attempt_id"],
        reconcile_reason=reconcile_reason, path=report.get("path"), evidence=evidence,
    )


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #

def _selected_lock(root: Path) -> dict:
    import visual_profile_registry as registry
    profile_id = registry.default_profile_id(root)
    entry = registry.registry_entry(profile_id, root)
    return {
        "schema_version": 1,
        "lifecycle_state": adapter.LIFECYCLE_SELECTED,
        "lock_policy": "advisory_draft_only",
        "status": "selected",
        "profile_id": profile_id,
        "profile_path": entry["path"],
        "selection": {"status": "selected", "source": "rule_engine",
                      "selector_version": "1.0", "candidates": [], "inputs_summary": {}},
        "selection_evidence": {"selector_version": "1.0", "source": "rule_engine",
                               "inputs_digest": "sha256:" + "a" * 64,
                               "matched_rules": ["world=real"], "reason": ["prio=semantic"]},
        "confirmation_mode": "pending",
        "confirmed_by": None,
        "confirmed_at": None,
    }


def _seed_episode(root: Path, name: str = "99_closure") -> Path:
    ep = root / "episodes" / name
    (ep / "meta").mkdir(parents=True, exist_ok=True)
    story_json.write_json(ep / LOCK_REL, _selected_lock(root))
    return ep


def _seed_ledger(ep: Path, *, frame: str = "01", attempt_id="a1b2c3d4") -> None:
    candidate = {"path": "media/candidates/" + frame + ".png", "sha256": "c" * 64}
    if attempt_id:
        candidate["attempt_id"] = attempt_id
    story_json.write_json(ep / LEDGER_REL, {
        "schema_version": 1,
        "canvas": {"aspect_ratio": "4:5", "width": 1080, "height": 1350},
        "frames": {frame: {
            "number": int(frame),
            "status": "LOCKED",
            "attempts": [],
            "current_candidate": candidate,
            "approved_asset": {"path": "media/approved/" + frame + ".png",
                              "sha256": "d" * 64,
                              "source_sha256": candidate["sha256"],
                              "promoted_at": "2026-09-12T10:00:00+08:00"},
            "lock": {"at": "2026-09-12T10:05:00+08:00", "sha256": "d" * 64, "reason": "approved"},
            "reviews": [],
        }},
        "asset_roots": {"approved": "media/approved"},
    })


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="visual-profile-closure-") as tmp:
        root = Path(tmp) / "repo"
        shutil.copytree(ROOT / "standards/visual_profiles", root / "standards/visual_profiles")

        # legacy: no lock at all -> skipped, never failed
        bare = root / "episodes" / "98_legacy"
        (bare / "meta").mkdir(parents=True, exist_ok=True)
        assert freeze_on_first_asset_commit(bare, story_root=root)["status"] == RESULT_SKIPPED
        assert required_for_production(bare) is False

        # unadjudicated SELECTED lock -> fail, never auto-locked
        selected = _seed_episode(root, "97_selected")
        result = freeze_on_first_asset_commit(selected, frame="01", story_root=root)
        assert result["status"] == RESULT_FAIL and result["code"] == ERROR_NOT_LOCKED, result
        kept = json.loads((selected / LOCK_REL).read_text(encoding="utf-8"))
        assert kept["lifecycle_state"] == adapter.LIFECYCLE_SELECTED

        # LOCKED + committed asset -> frozen once, then idempotent NOOP
        episode = _seed_episode(root)
        lifecycle.confirm_visual_lock(episode, confirmed_by="yeqian",
                                      confirmed_at="2026-09-12T09:00:00+08:00",
                                      reason="reviewed", story_root=root)
        assert required_for_production(episode) is False  # no asset committed yet
        _seed_ledger(episode)
        assert required_for_production(episode) is True
        assert first_committed_asset(episode)["attempt_id"] == "a1b2c3d4"

        report = freeze_on_first_asset_commit(episode, frame="01",
                                              attempt_id="a1b2c3d4", story_root=root)
        assert report["status"] == RESULT_FROZEN and report["from_state"] == "LOCKED", report
        frozen = json.loads((episode / LOCK_REL).read_text(encoding="utf-8"))
        assert frozen["lifecycle_state"] == lifecycle.LIFECYCLE_FROZEN
        assert frozen["frozen"]["trigger"] == FREEZE_TRIGGER
        assert frozen["frozen"]["frame"] == "01"
        assert frozen["frozen"]["production_attempt_id"] == "a1b2c3d4"
        assert frozen["frozen"]["inherits_confirmation_by"] == "yeqian"
        assert frozen["confirmation"]["confirmed_by"] == "yeqian"
        before = (episode / LOCK_REL).read_text(encoding="utf-8")
        again = freeze_on_first_asset_commit(episode, frame="01", story_root=root)
        assert again["status"] == RESULT_NOOP, again
        assert (episode / LOCK_REL).read_text(encoding="utf-8") == before

        # no stable attempt id in the ledger -> None, never fabricated
        plain = _seed_episode(root, "96_plain")
        lifecycle.confirm_visual_lock(plain, confirmed_by="yeqian",
                                      confirmed_at="2026-09-12T09:00:00+08:00", story_root=root)
        _seed_ledger(plain, attempt_id=None)
        assert first_committed_asset(plain)["attempt_id"] is None
        assert freeze_on_first_asset_commit(plain, story_root=root)["status"] == RESULT_FROZEN
        settled = json.loads((plain / LOCK_REL).read_text(encoding="utf-8"))
        assert settled["frozen"]["frame"] == "01"
        assert settled["frozen"]["production_attempt_id"] is None

        # Phase 4.6.1 recovery -------------------------------------------------
        # legacy Episode: reconcile skips and never creates a lock
        assert reconcile_episode(bare, story_root=root)["status"] == RESULT_SKIPPED
        assert not (bare / LOCK_REL).exists()

        # SELECTED + committed asset: refused, and never auto-confirmed
        unadjudicated = _seed_episode(root, "94_selected_asset")
        _seed_ledger(unadjudicated)
        refused = reconcile_episode(unadjudicated, story_root=root)
        assert refused["status"] == RESULT_FAIL and refused["code"] == ERROR_NOT_LOCKED, refused
        kept_unadjudicated = json.loads((unadjudicated / LOCK_REL).read_text(encoding="utf-8"))
        assert kept_unadjudicated["lifecycle_state"] == adapter.LIFECYCLE_SELECTED
        assert "frozen" not in kept_unadjudicated

        # SELECTED without any asset: nothing is owed, so it is a quiet noop
        quiet = _seed_episode(root, "93_selected_no_asset")
        assert reconcile_episode(quiet, story_root=root)["status"] == RESULT_NOOP
        assert json.loads((quiet / LOCK_REL).read_text(encoding="utf-8"))[
            "lifecycle_state"] == adapter.LIFECYCLE_SELECTED

        # LOCKED without any committed asset: not frozen
        locked_only = _seed_episode(root, "92_locked_no_asset")
        lifecycle.confirm_visual_lock(locked_only, confirmed_by="yeqian",
                                      confirmed_at="2026-09-12T09:00:00+08:00", story_root=root)
        assert reconcile_episode(locked_only, story_root=root)["status"] == RESULT_NOOP
        assert json.loads((locked_only / LOCK_REL).read_text(encoding="utf-8"))[
            "lifecycle_state"] == lifecycle.LIFECYCLE_LOCKED

        # LOCKED + committed asset + no promote hook ran: recovered, then idempotent
        recovered = _seed_episode(root, "91_locked_asset")
        lifecycle.confirm_visual_lock(recovered, confirmed_by="yeqian",
                                      confirmed_at="2026-09-12T09:00:00+08:00",
                                      reason="late confirmation", story_root=root)
        _seed_ledger(recovered)
        report = reconcile_episode(recovered, story_root=root)
        assert report["status"] == RESULT_FROZEN, report
        assert report["from_state"] == "LOCKED" and report["to_state"] == "FROZEN"
        assert report["frame"] == "01" and report["production_attempt_id"] == "a1b2c3d4"
        healed = json.loads((recovered / LOCK_REL).read_text(encoding="utf-8"))
        assert healed["lifecycle_state"] == lifecycle.LIFECYCLE_FROZEN
        assert healed["frozen"]["trigger"] == RECONCILE_TRIGGER
        assert healed["frozen"]["reconcile_reason"]
        assert healed["frozen"]["inherits_confirmation_by"] == "yeqian"
        assert healed["confirmation"]["confirmed_by"] == "yeqian"
        healed_text = (recovered / LOCK_REL).read_text(encoding="utf-8")
        assert reconcile_episode(recovered, story_root=root)["status"] == RESULT_NOOP
        assert (recovered / LOCK_REL).read_text(encoding="utf-8") == healed_text
    print("VISUAL PROFILE CLOSURE SELF-TEST PASS")


def cmd_inspect(args: argparse.Namespace) -> int:
    episode = Path(args.episode_dir)
    lock, source, error = lock_gate.load_lock(episode)
    print(json.dumps({
        "episode": episode.as_posix(),
        "lock_path": source,
        "lock_error": error,
        "governed": governed(episode),
        "lifecycle_state": lifecycle.lifecycle_of(lock),
        "committed_assets": committed_assets(episode),
        "freeze_required": required_for_production(episode),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Phase 4.6.1: recover an interrupted closure. Exit 1 only on a refused recovery."""
    report = reconcile_episode(Path(args.episode_dir), story_root=args.story_root,
                               reason=args.reason)
    print(json.dumps({
        "status": report.get("status"),
        "code": report.get("code"),
        "lifecycle_state": report.get("lifecycle_state"),
        "frame": report.get("frame"),
        "production_attempt_id": report.get("production_attempt_id"),
        "from_state": report.get("from_state"),
        "to_state": report.get("to_state"),
        "reconcile_reason": report.get("reconcile_reason"),
        "reason": report.get("reason"),
        "detail": report.get("detail"),
    }, ensure_ascii=False, indent=2))
    return 1 if report.get("status") == RESULT_FAIL else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story OS Visual Profile production closure (governance Phase 4.6-B)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    child = sub.add_parser("inspect", help="read-only: committed assets and freeze status")
    child.add_argument("episode_dir")
    child.set_defaults(func=cmd_inspect)
    child = sub.add_parser("reconcile",
                           help="recover a LOCKED profile that already has a committed asset")
    child.add_argument("episode_dir")
    child.add_argument("--story-root", dest="story_root", default=None)
    child.add_argument("--reason", default=None)
    child.set_defaults(func=cmd_reconcile)
    sub.add_parser("self-test").set_defaults(func=lambda args: (self_test(), 0)[1])
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
