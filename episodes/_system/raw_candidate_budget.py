#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atomic candidate budget + candidate lifecycle for Story OS V2.6.0."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import runtime_atomic_store as atomic
import frame_contract
import story_json

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/runtime/raw-candidate-budget.json")
OVERRIDE_REL = Path("meta/runtime/raw-candidate-budget-override.json")

# Both codes are emitted by the same raw-candidate budget guard. The first
# means the per-frame lane is exhausted; the second means the Episode-wide
# total is exhausted. Once the formal authorization lifecycle adds capacity,
# both must be resumable through the same deterministic queue path.
BUDGET_BLOCK_CODES = frozenset({"RAW_CANDIDATE_BUDGET_EXHAUSTED", "EPISODE_IMAGE_LOOP_GUARD"})
CFG = ROOT / "runtimes/runtime-fast-path-v251.json"
KINDS = {"original", "repair", "exception", "user_exception", "authority_refresh", "user_continuation"}
VISUAL_LOCK_POLICY_SEMANTIC_PREFIX = "visual-lock-policy:"

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def _read_json(path: Path) -> dict:
    return story_json.read_json(path, default={})

def limits() -> dict:
    defaults = {"original": 2, "repair": 2, "exception": 2, "user_exception": 1, "authority_refresh": 0, "user_continuation": 0}
    try:
        configured = _read_json(CFG).get("raw_candidate_budget") or {}
        return {**defaults, **configured}
    except Exception:
        return defaults

def frame_count(ep: Path) -> int:
    ep = Path(ep)
    for rel in ("meta/episode-state.json", "meta/release-manifest.json"):
        d = _read_json(ep / rel)
        for key in ("frame_count", "body_frame_count"):
            raw = d.get(key)
            if isinstance(raw, int) and raw > 0:
                return raw
        release = d.get("release") or {}
        raw = release.get("body_frame_count")
        if isinstance(raw, int) and raw > 0:
            return raw
    ledger = _read_json(ep / "meta/production-ledger.json")
    frames = ledger.get("frames") or {}
    if isinstance(frames, dict) and frames:
        return len(frames)
    return 20

def _authorized_episode_override(ep: Path) -> int | None:
    """Return an episode budget raise only when it carries an explicit decision.

    This file is an authorized execution decision, not audit-only evidence.
    Legacy named authorizations remain readable without rewriting history.
    """
    override = _read_json(Path(ep).resolve() / OVERRIDE_REL)
    if not isinstance(override, dict):
        return None
    if str(override.get("status") or "").upper() == "TERMINATED":
        return None
    raw = override.get("max_total_content_candidates")
    auth = override.get("authorization")
    legacy_auth = override.get("authorized_by")
    authorized = (
        isinstance(auth, dict) and auth.get("approved") is True
        and isinstance(auth.get("source"), str) and bool(auth["source"].strip())
    ) or (isinstance(legacy_auth, str) and bool(legacy_auth.strip()))
    if authorized and type(raw) is int and raw > 0:
        return raw
    return None


def _authorization_ok(node: dict) -> bool:
    """A raise is honored only when it carries an explicit decision."""
    node = node or {}
    auth = node.get("authorization")
    legacy_auth = node.get("authorized_by")
    return (
        isinstance(auth, dict) and auth.get("approved") is True
        and isinstance(auth.get("source"), str) and bool(auth["source"].strip())
    ) or (isinstance(legacy_auth, str) and bool(legacy_auth.strip()))


def authorized_frame_raise(ep: Path, frame_key: str, kind: str) -> dict:
    """Authorized per-frame raise above the fixed per-kind candidate limit.

    The fixed limit stops image loops. A frame can still need one more
    candidate when its own authority changed after the budget was spent (for
    example a direct-user appearance update that forces regeneration against a
    new Frame Contract). Only an entry in the same authorized override file,
    carrying its own authorization source, can raise that one frame; without
    such an entry the fixed per-kind limit applies unchanged.
    """
    override = _read_json(Path(ep).resolve() / OVERRIDE_REL)
    if not isinstance(override, dict):
        return {"extra": 0, "sources": []}
    if str(override.get("status") or "").upper() == "TERMINATED":
        return {"extra": 0, "sources": []}
    total = 0
    sources: list[str] = []
    for row in override.get("per_frame_authorizations") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("frame") or "").zfill(2) != frame_key:
            continue
        if str(row.get("kind") or "") != kind:
            continue
        extra = row.get("additional")
        if type(extra) is not int or extra <= 0:
            continue
        if not _authorization_ok(row):
            continue
        total += extra
        source = (row.get("authorization") or {}).get("source") or row.get("authorized_by") or ""
        sources.append(str(source)[:200])
    return {"extra": total, "sources": sources}


def resolve_limit(ep: Path) -> dict:
    """Fixed global cap wins; otherwise an authorized raise beats the formula."""
    cfg = _read_json(CFG)
    fixed = ((cfg.get("episode_candidate_budget") or {}).get("max_total_content_candidates"))
    if type(fixed) is int and fixed > 0:
        return {"limit": fixed, "source": "global_fixed", "override_applied": False}
    count = frame_count(Path(ep))
    default = min(60, max(20, count + 15))
    override_limit = _authorized_episode_override(Path(ep))
    if override_limit is not None and override_limit > default:
        return {"limit": override_limit, "source": OVERRIDE_REL.as_posix(), "override_applied": True}
    return {"limit": default, "source": "derived_frame_count_plus_15", "override_applied": False}

def episode_limit(ep: Path) -> int:
    return resolve_limit(ep)["limit"]


def _override_path(ep: Path) -> Path:
    return Path(ep).resolve() / OVERRIDE_REL


def authorize_episode_budget(ep: Path, *, max_total: int, source: str, note: str = "") -> dict:
    """Persist an explicit Episode-level continuation authorization.

    This is the supported operational replacement for hand-editing the override
    JSON.  It never infers approval: callers must provide a non-empty source.
    """
    ep = Path(ep).resolve()
    source = str(source or "").strip()
    if not source:
        raise ValueError("authorization source is required")
    if type(max_total) is not int or max_total <= 0:
        raise ValueError("max_total must be a positive integer")
    baseline = min(60, max(20, frame_count(ep) + 15))
    if max_total <= baseline:
        raise ValueError(f"max_total must exceed the default episode budget ({baseline})")
    current = _read_json(_override_path(ep))
    if not isinstance(current, dict):
        current = {}
    data = dict(current)
    data.update({
        "schema_version": 2,
        "status": "AUTHORIZED",
        "updated_at": now(),
        "max_total_content_candidates": max_total,
        "authorization": {"approved": True, "source": source, "note": str(note or "").strip(), "authorized_at": now()},
    })
    data.pop("termination", None)
    story_json.write_json(_override_path(ep), data)
    return data


def authorize_frame_budget(ep: Path, *, frame: int, kind: str, additional: int, source: str, note: str = "") -> dict:
    """Persist one bounded per-frame continuation authorization."""
    ep = Path(ep).resolve()
    source = str(source or "").strip()
    if not source:
        raise ValueError("authorization source is required")
    if kind not in KINDS - {"authority_refresh", "user_continuation"}:
        raise ValueError("kind does not support manual budget raise")
    if type(additional) is not int or additional <= 0:
        raise ValueError("additional must be a positive integer")
    frame_key = f"{int(frame):02d}"
    current = _read_json(_override_path(ep))
    if not isinstance(current, dict):
        current = {}
    rows = list(current.get("per_frame_authorizations") or [])
    row = {
        "frame": frame_key,
        "kind": kind,
        "additional": additional,
        "authorization": {"approved": True, "source": source, "note": str(note or "").strip(), "authorized_at": now()},
    }
    rows.append(row)
    data = dict(current)
    data.update({"schema_version": 2, "status": "AUTHORIZED", "updated_at": now(), "per_frame_authorizations": rows})
    data.pop("termination", None)
    story_json.write_json(_override_path(ep), data)
    return data


def terminate_override(ep: Path, *, source: str, reason: str) -> dict:
    """Close all manual budget raises while preserving their audit trail."""
    ep = Path(ep).resolve()
    source = str(source or "").strip()
    reason = str(reason or "").strip()
    if not source or not reason:
        raise ValueError("termination source and reason are required")
    current = _read_json(_override_path(ep))
    if not isinstance(current, dict) or not current:
        raise ValueError("budget override does not exist")
    data = dict(current)
    data.update({"schema_version": 2, "status": "TERMINATED", "updated_at": now(),
                 "termination": {"source": source, "reason": reason, "terminated_at": now()}})
    story_json.write_json(_override_path(ep), data)
    return data


def override_status(ep: Path) -> dict:
    data = _read_json(_override_path(Path(ep)))
    active = bool(data) and str(data.get("status") or "AUTHORIZED").upper() != "TERMINATED"
    return {"exists": bool(data), "active": active, "status": data.get("status") if data else None,
            "effective_episode_budget": resolve_limit(Path(ep)), "override": data}

def summary(ep: Path, *, pending: int = 0) -> dict:
    state = load(ep)
    claims = [row for *_prefix, row in _all_claims(state) if isinstance(row, dict)]
    committed = sum(row.get("committed") is True for row in claims)
    resolution = resolve_limit(ep)
    available = max(0, resolution["limit"] - len(claims))
    return {**resolution, "committed": committed, "inflight_reserved": len(claims)-committed,
            "available": available, "pending_generation": pending,
            "episode_capacity": min(pending, available),
            "additional_capacity_needed": max(0, pending-available),
            "per_frame_limits_still_apply": True}

def default_state() -> dict:
    return {
        "schema_version": 3,
        "module_version": "2.6.0",
        "updated_at": now(),
        "frames": {},
        "events": [],
    }

def _upgrade_state(d: dict) -> dict:
    old_schema = int(d.get("schema_version") or 0)
    d.setdefault("frames", {})
    d.setdefault("events", [])
    if old_schema < 3:
        # V2.5.1.1 had no commit lifecycle. Existing retained claims already consumed
        # content budget, so migrate them conservatively as committed.
        for _frame, kinds in (d.get("frames") or {}).items():
            for _kind, bucket in (kinds or {}).items():
                bucket.setdefault("claims", {})
                for _token, row in (bucket.get("claims") or {}).items():
                    if isinstance(row, dict):
                        row.setdefault("committed", True)
                        row.setdefault("committed_at", row.get("at") or row.get("claimed_at") or now())
    d["schema_version"] = 3
    d["module_version"] = "2.6.0"
    return d

def load(ep: Path) -> dict:
    d = atomic.read_json(Path(ep).resolve() / REL, default_state())
    if not isinstance(d, dict):
        d = default_state()
    return _upgrade_state(d)

def kind_for_queue_item(item: dict) -> str:
    kind = str((item or {}).get("kind") or "").lower()
    capture_id = str((item or {}).get("capture_id") or "")
    if kind == "repair" and capture_id.startswith("authority-refresh-"):
        return "authority_refresh"
    if kind == "repair" and capture_id.startswith("user-continuation-"):
        return "user_continuation"
    if kind == "repair" and capture_id.startswith("user-exception-"):
        # Direct-user exception repair is independently authorized and must not
        # collide with the bounded automatic candidate-pool bucket (exception).
        # Production Ledger separately enforces the one-user-exception limit.
        return "user_exception"
    if kind == "repair":
        return "repair"
    if kind == "baseline_candidate":
        # Baseline candidate competition is a bounded bootstrap lane, not an
        # ordinary content repair. Reuse the existing exception candidate bucket
        # so the one-shot repair budget remains semantically intact.
        return "exception"
    return "original"

def semantic_key_for_queue_item(item: dict) -> str | None:
    kind = kind_for_queue_item(item)
    if kind == "authority_refresh":
        contract = (item or {}).get("frame_contract") or {}
        key = str(contract.get("contract_sha256") or (item or {}).get("frame_contract_sha256") or "").strip().lower()
        return key or None
    if kind == "user_continuation":
        key = str((item or {}).get("capture_id") or "").strip()
        return key or None
    if kind == "exception" and str((item or {}).get("kind") or "").lower() == "baseline_candidate":
        # Visual Lock competitive candidates are bounded by the prompt policy that
        # produced them.  A framework fix may legitimately create a new explicit
        # policy revision; old-policy retained pixels must not permanently consume
        # the new revision's two-slot frame budget.  Keep the Episode-wide budget
        # unchanged so policy revisions cannot bypass the global image-loop guard.
        capture_id = str((item or {}).get("capture_id") or "").strip().lower()
        prefix = "visual-lock-candidate-"
        try:
            frame = int((item or {}).get("frame") or 0)
        except Exception:
            frame = 0
        marker = f"-{frame:02d}-" if frame > 0 else ""
        if capture_id.startswith(prefix) and marker:
            body = capture_id[len(prefix):]
            if marker in body:
                revision, slot = body.rsplit(marker, 1)
                if revision and slot.isdigit():
                    return f"{VISUAL_LOCK_POLICY_SEMANTIC_PREFIX}{revision}"
    return None


def _policy_scoped_exception(kind: str, semantic_key: str | None) -> bool:
    return kind == "exception" and str(semantic_key or "").startswith(VISUAL_LOCK_POLICY_SEMANTIC_PREFIX)


def _semantic_used(bucket: dict, semantic_key: str) -> int:
    key = str(semantic_key or "").lower()
    return sum(
        1 for row in ((bucket or {}).get("claims") or {}).values()
        if isinstance(row, dict) and str(row.get("semantic_key") or "").lower() == key
    )


def blocked_queue_context(ep: Path, items: list[dict]) -> dict:
    """Explain whether explicit budget authorization can resume blocked queue work.

    This is read-only decision support.  It never grants approval and never
    mutates the queue.  Ordinary original/repair/exception lanes can be raised
    through the existing authorized override lifecycle; semantic authority and
    user-continuation lanes keep their own explicit authorization contracts.
    """
    ep = Path(ep).resolve()
    state = load(ep)
    rows = []
    for item in items:
        frame = int((item or {}).get("frame") or 0)
        key = f"{frame:02d}"
        kind = kind_for_queue_item(item)
        bucket = (((state.get("frames") or {}).get(key) or {}).get(kind) or {})
        bucket_used = int(bucket.get("used") or 0)
        base_limit = int(limits().get(kind, 2))
        semantic_key = semantic_key_for_queue_item(item)
        used = _semantic_used(bucket, semantic_key) if _policy_scoped_exception(kind, semantic_key) else bucket_used
        semantic_authorized = False
        semantic_duplicate = False
        if kind in {"authority_refresh", "user_continuation"}:
            auth = (
                _authority_refresh_authorization(ep, key, semantic_key)
                if kind == "authority_refresh"
                else _user_continuation_authorization(ep, key, semantic_key)
            ) if semantic_key else {"approved": False, "source": ""}
            semantic_authorized = bool(auth.get("approved"))
            semantic_duplicate = bool(semantic_key) and any(
                str((claim or {}).get("semantic_key") or "").lower() == str(semantic_key).lower()
                for claim in (bucket.get("claims") or {}).values()
                if isinstance(claim, dict)
            )
            # Semantic lanes deliberately have a configured base limit of zero.
            # One machine/user authorization grants exactly one retained candidate
            # for that semantic key; this mirrors claim() instead of treating zero
            # as an unconditional hard stop in the read-side recovery decision.
            semantic_capacity = 1 if semantic_authorized and not semantic_duplicate else 0
            raise_row = {"extra": 0, "sources": [str(auth.get("source") or "")[:200]] if semantic_authorized else []}
            effective_limit = used + semantic_capacity
        else:
            raise_row = authorized_frame_raise(ep, key, kind)
            effective_limit = base_limit + int(raise_row.get("extra") or 0)
        rows.append({
            "frame": frame,
            "item_id": str((item or {}).get("id") or ""),
            "kind": kind,
            "used": used,
            "bucket_used": bucket_used,
            "base_limit": base_limit,
            "effective_limit": effective_limit,
            "frame_capacity_available": max(0, effective_limit - used),
            "frame_authorization_supported": kind in {"original", "repair", "exception", "user_exception"},
            "authorization_sources": list(raise_row.get("sources") or []),
            "semantic_key": semantic_key,
            "semantic_authorization_approved": semantic_authorized,
            "semantic_duplicate": semantic_duplicate,
        })
    episode = summary(ep, pending=len(rows))
    episode_available = int(episode.get("available") or 0)
    eligible = [row["frame"] for row in rows if row["frame_capacity_available"] > 0]
    resumable = eligible[:max(0, episode_available)]
    frame_needs = [row for row in rows if row["frame_capacity_available"] <= 0 and row["frame_authorization_supported"]]
    options = []
    if episode_available <= 0 and rows:
        options.append({
            "kind": "episode",
            "command": "raw_candidate_budget.py authorize-episode",
            "current_limit": int(episode.get("limit") or 0),
            "minimum_new_limit": int(episode.get("limit") or 0) + max(1, len(rows)),
            "requires_explicit_source": True,
        })
    for row in frame_needs:
        options.append({
            "kind": "frame",
            "command": "raw_candidate_budget.py authorize-frame",
            "frame": row["frame"],
            "candidate_kind": row["kind"],
            "minimum_additional": 1,
            "requires_explicit_source": True,
        })
    return {
        "episode": episode,
        "items": rows,
        "resumable_frames": sorted(set(resumable)),
        "authorization_required": bool(options),
        "authorization_options": options,
    }

def _authority_refresh_authorization(ep: Path, frame_key: str, semantic_key: str) -> dict:
    ledger = _read_json(Path(ep).resolve() / "meta/production-ledger.json")
    frame = (ledger.get("frames") or {}).get(frame_key) or {}
    auth = frame.get("authority_refresh_authorization") or {}
    direct_user = (
        str(auth.get("frame_contract_sha256") or "").lower() == str(semantic_key or "").lower()
        and bool(str(auth.get("approval_text") or "").strip())
        and str(auth.get("approval_basis") or "") == "direct_user_authority_contract_refresh"
    )
    machine_verified = False
    if (
        str(auth.get("frame_contract_sha256") or "").lower() == str(semantic_key or "").lower()
        and str(auth.get("approval_basis") or "") == "machine_verified_frame_contract_drift"
    ):
        candidate = frame.get("current_candidate") or {}
        candidate_sha = str(candidate.get("sha256") or "").lower()
        if candidate_sha and candidate_sha == str(auth.get("candidate_sha256") or "").lower():
            attempt = next(
                (
                    row for row in reversed(frame.get("attempts") or [])
                    if str(((row or {}).get("candidate") or {}).get("sha256") or "").lower() == candidate_sha
                ),
                None,
            )
            if isinstance(attempt, dict):
                recorded = (attempt.get("request") or {}).get("frame_contract")
                errors = frame_contract.verify_recorded_provenance(ep, frame_key, recorded)
                machine_verified = any("frame_contract_sha256 stale" in str(error) for error in errors)
    source = str(auth.get("approval_text") or auth.get("reason") or "")[:200]
    return {"approved": bool(direct_user or machine_verified), "source": source}

def _user_continuation_authorization(ep: Path, frame_key: str, semantic_key: str) -> dict:
    ledger = _read_json(Path(ep).resolve() / "meta/production-ledger.json")
    frame = (ledger.get("frames") or {}).get(frame_key) or {}
    rows = frame.get("user_continuation_authorizations") or []
    auth = rows[-1] if rows and isinstance(rows[-1], dict) else {}
    raw_index = str(semantic_key or "").rsplit("-", 1)[-1]
    try:
        semantic_index = int(raw_index)
    except Exception:
        semantic_index = -1
    approved = (
        semantic_index > 0
        and int(auth.get("continuation_index") or 0) == semantic_index
        and bool(str(auth.get("approval_text") or "").strip())
        and str(auth.get("approval_basis") or "") == "direct_user_continuation_after_exhaustion"
    )
    return {"approved": approved, "source": str(auth.get("approval_text") or "")[:200]}

def _all_claims(d: dict):
    for frame, kinds in (d.get("frames") or {}).items():
        for kind, bucket in (kinds or {}).items():
            for token, row in ((bucket or {}).get("claims") or {}).items():
                yield frame, kind, bucket, token, row

def _find_token(d: dict, token: str):
    for row in _all_claims(d):
        if row[3] == token:
            return row
    return None

def _reserved_total(d: dict) -> int:
    return sum(1 for *_prefix, row in _all_claims(d) if isinstance(row, dict))

def claim(ep, frame, kind, reason="", token=None, semantic_key=None):
    ep = Path(ep).resolve()
    import episode_lifecycle
    episode_lifecycle.assert_writable(ep, "raw_candidate_budget.claim")
    if kind not in KINDS:
        raise ValueError(f"kind must be {sorted(KINDS)}")
    key = f"{int(frame):02d}"
    semantic_key = str(semantic_key or "").strip().lower() or None
    token = str(token or "").strip() or f"{key}:{kind}:{int(dt.datetime.now().timestamp()*1000000)}"
    result = {}

    def mutate(d: dict):
        _upgrade_state(d)
        found = _find_token(d, token)
        if found:
            f, k, bucket, _, row = found
            same_semantic = (
                not semantic_key
                if kind not in {"authority_refresh", "user_continuation"}
                else False
            ) or str((row or {}).get("semantic_key") or "").lower() == str(semantic_key or "").lower()
            if f != key or k != kind or not same_semantic:
                result.update({"decision": "TOKEN_CONTEXT_MISMATCH", "token": token})
                return
            used = _semantic_used(bucket, semantic_key) if _policy_scoped_exception(kind, semantic_key) else int(bucket.get("used") or 0)
            result.update({
                "frame": f, "kind": k, "used": used,
                "limit": int(limits().get(k, 2)), "decision": "REUSE_CLAIM",
                "token": token, "committed": bool((row or {}).get("committed")),
                "semantic_key": (row or {}).get("semantic_key"),
            })
            return

        bucket = d["frames"].setdefault(key, {}).setdefault(kind, {"used": 0, "claims": {}})
        bucket.setdefault("claims", {})
        base_limit = int(limits().get(kind, 2))
        raise_row = {"extra": 0, "sources": []}
        if kind in {"authority_refresh", "user_continuation"}:
            if not semantic_key:
                decision = "AUTHORITY_REFRESH_SEMANTIC_KEY_REQUIRED" if kind == "authority_refresh" else "USER_CONTINUATION_SEMANTIC_KEY_REQUIRED"
                result.update({"frame": key, "kind": kind, "decision": decision, "token": token})
                return
            auth = _authority_refresh_authorization(ep, key, semantic_key) if kind == "authority_refresh" else _user_continuation_authorization(ep, key, semantic_key)
            if not auth["approved"]:
                decision = "AUTHORITY_REFRESH_NOT_AUTHORIZED" if kind == "authority_refresh" else "USER_CONTINUATION_NOT_AUTHORIZED"
                result.update({"frame": key, "kind": kind, "decision": decision, "token": token, "semantic_key": semantic_key})
                return
            duplicate = next((row for row in bucket["claims"].values() if str((row or {}).get("semantic_key") or "").lower() == semantic_key), None)
            if duplicate is not None:
                decision = "AUTHORITY_REFRESH_CONTRACT_ALREADY_CLAIMED" if kind == "authority_refresh" else "USER_CONTINUATION_AUTHORIZATION_ALREADY_CLAIMED"
                result.update({"frame": key, "kind": kind, "decision": decision, "token": token, "semantic_key": semantic_key})
                return
            # These lanes are bounded by one retained candidate per explicit
            # semantic authorization plus the episode-wide cap. They never
            # borrow ordinary content-repair slots.
            per_kind_limit = int(bucket.get("used") or 0) + 1
            authorization_source = auth["source"]
        else:
            raise_row = authorized_frame_raise(ep, key, kind)
            per_kind_limit = base_limit + int(raise_row["extra"])
            authorization_source = None
            scoped_used = _semantic_used(bucket, semantic_key) if _policy_scoped_exception(kind, semantic_key) else int(bucket.get("used") or 0)
            if scoped_used >= per_kind_limit:
                result.update({
                    "frame": key, "kind": kind, "used": scoped_used,
                    "limit": per_kind_limit, "base_limit": base_limit,
                    "bucket_used": int(bucket.get("used") or 0),
                    "authorized_raise": int(raise_row["extra"]),
                    "decision": "STOP_IMAGE_LOOP", "token": token,
                    "semantic_key": semantic_key,
                })
                return

        total_limit = episode_limit(ep)
        total_now = _reserved_total(d)
        if total_now >= total_limit:
            result.update({
                "frame": key, "kind": kind, "used": int(bucket.get("used") or 0),
                "limit": per_kind_limit, "episode_used": total_now,
                "episode_limit": total_limit, "decision": "EPISODE_IMAGE_LOOP_GUARD", "token": token,
            })
            return

        bucket["used"] = int(bucket.get("used") or 0) + 1
        claim_row = {"claimed_at": now(), "reason": reason, "committed": False, "committed_at": None}
        if semantic_key:
            claim_row["semantic_key"] = semantic_key
        if authorization_source:
            claim_row["authorization_source"] = authorization_source
        bucket["claims"][token] = claim_row
        if raise_row["extra"]:
            bucket["claims"][token]["authorized_raise"] = int(raise_row["extra"])
            bucket["claims"][token]["authorization_sources"] = list(raise_row["sources"])
        d["updated_at"] = now()
        event = {"at": now(), "event": "claim", "frame": key, "kind": kind, "token": token}
        if semantic_key:
            event["semantic_key"] = semantic_key
        if raise_row["extra"]:
            event["authorized_raise"] = int(raise_row["extra"])
        d["events"].append(event)
        result.update({
            "frame": key, "kind": kind,
            "used": (_semantic_used(bucket, semantic_key) if _policy_scoped_exception(kind, semantic_key) else bucket["used"]),
            "bucket_used": bucket["used"], "limit": per_kind_limit,
            "authorized_raise": int(raise_row["extra"]),
            "episode_used": total_now + 1, "episode_limit": total_limit,
            "decision": "ALLOW", "token": token, "committed": False,
            "semantic_key": semantic_key,
        })

    atomic.update_json(ep / REL, default_state, mutate)
    return result.get("decision") in {"ALLOW", "REUSE_CLAIM"}, result

def commit(ep, token, reason="candidate_file_committed"):
    ep = Path(ep).resolve()
    import episode_lifecycle
    episode_lifecycle.assert_writable(ep, "raw_candidate_budget.commit")
    token = str(token or "").strip()
    result = {}

    def mutate(d: dict):
        _upgrade_state(d)
        found = _find_token(d, token)
        if not found:
            result.update({"decision": "TOKEN_NOT_FOUND", "token": token})
            return
        frame, kind, _bucket, _tok, row = found
        if row.get("committed") is True:
            result.update({"decision": "ALREADY_COMMITTED", "token": token, "frame": frame, "kind": kind})
            return
        row["committed"] = True
        row["committed_at"] = now()
        row["commit_reason"] = reason
        d["updated_at"] = now()
        d.setdefault("events", []).append({"at": now(), "event": "commit", "frame": frame, "kind": kind, "token": token})
        result.update({"decision": "COMMITTED", "token": token, "frame": frame, "kind": kind})

    atomic.update_json(ep / REL, default_state, mutate)
    return result.get("decision") in {"COMMITTED", "ALREADY_COMMITTED"}, result

def release(ep, token, reason="technical_failure_before_candidate_commit"):
    ep = Path(ep).resolve()
    token = str(token or "").strip()
    result = {}

    def mutate(d: dict):
        _upgrade_state(d)
        found = _find_token(d, token)
        if not found:
            result.update({"decision": "TOKEN_NOT_FOUND", "token": token})
            return
        frame, kind, bucket, _tok, row = found
        if row.get("committed") is True:
            result.update({"decision": "COMMITTED_NOT_RELEASED", "token": token, "frame": frame, "kind": kind})
            return
        bucket.get("claims", {}).pop(token, None)
        bucket["used"] = max(0, int(bucket.get("used") or 0) - 1)
        d["updated_at"] = now()
        d.setdefault("events", []).append({"at": now(), "event": "release", "frame": frame, "kind": kind, "token": token, "reason": reason})
        result.update({"decision": "RELEASED", "token": token, "frame": frame, "kind": kind, "used": bucket["used"]})

    atomic.update_json(ep / REL, default_state, mutate)
    return result.get("decision") == "RELEASED", result

def self_test():
    import tempfile, threading
    with tempfile.TemporaryDirectory(prefix="candidate budget 并发 ") as td:
        ep = Path(td)
        results = []
        def one(i):
            results.append(claim(ep, i + 1, "original", token=f"q{i}"))
        threads = [threading.Thread(target=one, args=(i,)) for i in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(results) == 5 and all(x[0] for x in results)
        ok, row = commit(ep, "q0")
        assert ok and row["decision"] == "COMMITTED"
        ok, row = release(ep, "q0")
        assert not ok and row["decision"] == "COMMITTED_NOT_RELEASED"
        ok, _ = release(ep, "q1")
        assert ok
    print("RAW CANDIDATE BUDGET V2.6.0 ATOMIC LIFECYCLE SELF-TEST PASS")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("claim"); p.add_argument("episode_dir"); p.add_argument("--frame", required=True, type=int)
    p.add_argument("--kind", required=True, choices=sorted(KINDS)); p.add_argument("--reason", default=""); p.add_argument("--token"); p.add_argument("--semantic-key")
    p = sub.add_parser("commit"); p.add_argument("episode_dir"); p.add_argument("--token", required=True); p.add_argument("--reason", default="candidate_file_committed")
    p = sub.add_parser("release"); p.add_argument("episode_dir"); p.add_argument("--token", required=True); p.add_argument("--reason", default="technical_failure_before_candidate_commit")
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    p = sub.add_parser("authorize-episode"); p.add_argument("episode_dir"); p.add_argument("--max-total", required=True, type=int); p.add_argument("--source", required=True); p.add_argument("--note", default="")
    p = sub.add_parser("authorize-frame"); p.add_argument("episode_dir"); p.add_argument("--frame", required=True, type=int); p.add_argument("--kind", required=True, choices=sorted(KINDS - {"authority_refresh", "user_continuation"})); p.add_argument("--additional", required=True, type=int); p.add_argument("--source", required=True); p.add_argument("--note", default="")
    p = sub.add_parser("terminate-override"); p.add_argument("episode_dir"); p.add_argument("--source", required=True); p.add_argument("--reason", required=True)
    p = sub.add_parser("override-status"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return 0
    if a.cmd == "show": print(json.dumps({**load(Path(a.episode_dir)), "effective_budget": summary(Path(a.episode_dir))}, ensure_ascii=False, indent=2)); return 0
    if a.cmd == "authorize-episode": print(json.dumps(authorize_episode_budget(Path(a.episode_dir), max_total=a.max_total, source=a.source, note=a.note), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "authorize-frame": print(json.dumps(authorize_frame_budget(Path(a.episode_dir), frame=a.frame, kind=a.kind, additional=a.additional, source=a.source, note=a.note), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "terminate-override": print(json.dumps(terminate_override(Path(a.episode_dir), source=a.source, reason=a.reason), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "override-status": print(json.dumps(override_status(Path(a.episode_dir)), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "claim":
        ok, row = claim(a.episode_dir, a.frame, a.kind, a.reason, a.token, a.semantic_key)
    elif a.cmd == "commit":
        ok, row = commit(a.episode_dir, a.token, a.reason)
    else:
        ok, row = release(a.episode_dir, a.token, a.reason)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
