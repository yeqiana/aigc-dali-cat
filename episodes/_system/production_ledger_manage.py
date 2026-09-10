"""Production ledger management commands (Story OS B4 split).

Management lane: init / authorize-* / accept-user-exception-candidate /
promote / lock / batch-begin / batch-end / audit / show. Shared library globals
are imported from production_ledger_core; the CLI facade re-exports these.
"""
from __future__ import annotations

from production_ledger_core import *  # noqa: F401,F403  (shared ledger globals)

def cmd_init(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path = ep / LEDGER_FILE
    if path.exists() and not args.force:
        raise SystemExit(f"ledger already exists: {path}")
    data = init_ledger(ep, count=args.frame_count, ratio=args.aspect_ratio, overwrite=args.force)
    c = data["canvas"]
    print(f"initialized {path}")
    print(f"canvas: {c['aspect_ratio']} / {c['width']}脳{c['height']} ({c['source']})")


def cmd_authorize_user_locked_repair(args: argparse.Namespace) -> None:
    """Reopen a locked frame for its first ordinary repair after direct user scope approval."""
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] != "LOCKED":
        raise SystemExit(f"locked repair requires LOCKED, got {frame['status']}")
    if frame.get("content_repairs_used", 0) != 0:
        raise SystemExit("locked repair is only for a frame with no ordinary content repair")
    approval = args.approval_text.strip()
    if not approval:
        raise SystemExit("direct user approval text is required")
    frame.setdefault("superseded_locks", []).append({"at": now_iso(), "lock": frame.get("lock"), "approved_asset": frame.get("approved_asset")})
    frame["status"] = "REPAIR_AUTHORIZED"
    frame["repair_authorization"] = {"at": now_iso(), "note": args.reason, "user_approved": True, "delegated_auto_review": False, "approval_basis": "direct_user_review_locked_repair", "approval_text": approval}
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: REPAIR_AUTHORIZED (direct-user locked-frame scope recorded)")


def cmd_authorize_user_passed_repair(args: argparse.Namespace) -> None:
    """Reopen a pre-lock PASSED frame when a later user-approved authority change invalidates it."""
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] != "PASSED":
        raise SystemExit(f"passed repair requires PASSED, got {frame['status']}")
    if frame.get("content_repairs_used", 0) != 0:
        raise SystemExit("passed repair is only for a frame with no ordinary content repair")
    approval = args.approval_text.strip()
    if not approval:
        raise SystemExit("direct user approval text is required")
    frame.setdefault("superseded_passes", []).append({
        "at": now_iso(),
        "current_candidate": frame.get("current_candidate"),
        "reviews": list(frame.get("reviews") or []),
        "reason": args.reason,
    })
    frame["status"] = "REPAIR_AUTHORIZED"
    frame["repair_authorization"] = {
        "at": now_iso(),
        "note": args.reason,
        "user_approved": True,
        "delegated_auto_review": False,
        "approval_basis": "direct_user_review_passed_repair",
        "approval_text": approval,
    }
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: REPAIR_AUTHORIZED (direct-user passed-frame authority change recorded)")


def cmd_authorize_authority_refresh(args: argparse.Namespace) -> None:
    """Reopen a ready/passed frame after non-content authority or contract drift.

    This path is audit-only and does not consume the single content-repair budget.
    It exists for cases such as Frame Contract / authenticity / continuity authority
    updates where existing pixels must be regenerated against the new provenance.

    A LOCKED frame is admitted here too: a shared authority/contract repair that lands
    after the release lock still only re-renders the same content decision, so it must
    not consume the ordinary content-repair counter. The superseded lock is preserved.
    """
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] not in {"PASSED", "ORIGINAL_READY", "REPAIR_READY", "LOCKED"}:
        raise SystemExit(f"authority refresh requires PASSED/ORIGINAL_READY/REPAIR_READY/LOCKED, got {frame['status']}")
    approval = args.approval_text.strip()
    if not approval:
        raise SystemExit("direct user approval text is required")
    current_contract = current_frame_contract_provenance(ep, key)
    if not current_contract:
        raise SystemExit("current frame contract provenance missing")
    prior_lock = frame.get("lock") if frame["status"] == "LOCKED" else None
    if prior_lock:
        frame.setdefault("superseded_locks", []).append({"at": now_iso(), "lock": prior_lock, "approved_asset": frame.get("approved_asset")})
    frame.setdefault("authority_refresh_history", []).append({
        "at": now_iso(),
        "previous_status": frame.get("status"),
        "current_candidate": frame.get("current_candidate"),
        "reviews": list(frame.get("reviews") or []),
        "reason": args.reason,
    })
    frame["status"] = "AUTHORITY_REFRESH_AUTHORIZED"
    frame["authority_refresh_authorization"] = {
        "at": now_iso(),
        "reason": args.reason,
        "approval_text": approval,
        "approval_basis": "direct_user_authority_contract_refresh",
        "frame_contract_sha256": current_contract.get("contract_sha256"),
        "content_repair_budget_unchanged": True,
    }
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: AUTHORITY_REFRESH_AUTHORIZED (content repair budget unchanged)")


def cmd_authorize_user_exception_repair(args: argparse.Namespace) -> None:
    """Record one explicit, non-delegable user exception after a hard repair failure.

    This does not reset the ordinary single-repair counter.  It exists so a
    directly quoted user exception is auditable rather than being disguised as
    an original request or silently accepted candidate.
    """
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] not in {"NEEDS_USER", "LOCKED"}:
        raise SystemExit(f"user exception repair requires NEEDS_USER or LOCKED, got {frame['status']}")
    if frame.get("content_repairs_used", 0) != 1:
        raise SystemExit("user exception repair requires exactly one ordinary content repair")
    if frame.get("user_exception_repairs_used", 0) >= 1:
        raise SystemExit("user exception repair limit reached")
    approval = args.approval_text.strip()
    if not approval:
        raise SystemExit("direct user approval text is required")
    prior_lock = frame.get("lock") if frame["status"] == "LOCKED" else None
    if prior_lock:
        frame.setdefault("superseded_locks", []).append({"at": now_iso(), "lock": prior_lock, "approved_asset": frame.get("approved_asset")})
    frame["status"] = "EXCEPTION_REPAIR_AUTHORIZED"
    frame.setdefault("user_exception_authorizations", []).append({
        "at": now_iso(),
        "approval_text": approval,
        "reason": args.reason,
        "user_approved": True,
        "delegated_auto_review": False,
        "approval_basis": "direct_user_review_exception",
    })
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: EXCEPTION_REPAIR_AUTHORIZED (direct user exception recorded)")


def cmd_accept_user_exception_candidate(args: argparse.Namespace) -> None:
    """Accept an already-generated exception candidate with direct user review.

    The ordinary repair and one direct-user exception remain fully recorded;
    this command only accepts that existing candidate and never resets either
    repair counter.
    """
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] != "NEEDS_USER":
        raise SystemExit(f"exception acceptance requires NEEDS_USER, got {frame['status']}")
    if frame.get("content_repairs_used", 0) != 1 or frame.get("user_exception_repairs_used", 0) != 1:
        raise SystemExit("exception acceptance requires one ordinary and one user-exception repair")
    approval = args.approval_text.strip()
    if not approval:
        raise SystemExit("direct user approval text is required")
    candidate = frame.get("current_candidate") or {}
    raw_path = candidate.get("path")
    if not raw_path:
        raise SystemExit("current exception candidate missing")
    candidate_path = (repo_root() / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path)
    if not candidate_path.is_file() or sha256_file(candidate_path) != str(candidate.get("sha256") or "").lower():
        raise SystemExit("current exception candidate missing or hash drifted")
    matching_attempt = None
    for attempt in reversed(frame.get("attempts") or []):
        if (attempt.get("candidate") or {}).get("sha256") == candidate.get("sha256"):
            matching_attempt = attempt
            break
    if not isinstance(matching_attempt, dict):
        raise SystemExit("current exception candidate has no matching generation attempt")
    verify_attempt_frame_contract_provenance(ep, key, matching_attempt)
    verify_attempt_visual_provenance(ep, matching_attempt)
    acceptance = {
        "at": now_iso(),
        "approval_text": approval,
        "reason": args.reason,
        "user_approved": True,
        "delegated_auto_review": False,
        "approval_basis": "direct_user_review_exception_acceptance",
        "candidate_sha256": candidate["sha256"],
    }
    frame.setdefault("user_exception_acceptances", []).append(acceptance)
    frame.setdefault("reviews", []).append({
        "at": acceptance["at"], "decision": "pass", "notes": "Direct user accepted existing exception candidate: " + args.reason,
        "approval_basis": acceptance["approval_basis"], "candidate_sha256": candidate["sha256"],
    })
    frame["status"] = "PASSED"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: PASSED (direct-user exception candidate acceptance recorded)")


def cmd_promote(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] != "PASSED":
        raise SystemExit(f"promote requires PASSED and refuses to overwrite LOCKED assets, got {frame['status']}")
    candidate_info = frame.get("current_candidate")
    if not isinstance(candidate_info, dict) or not candidate_info.get("path"):
        raise SystemExit("current candidate missing")
    src_raw = candidate_info["path"]
    src = (repo_root() / src_raw).resolve() if not Path(src_raw).is_absolute() else Path(src_raw)
    if not src.is_file():
        raise SystemExit(f"candidate file missing: {src}")
    approved_dir = ep / data["asset_roots"]["approved"]
    approved_dir.mkdir(parents=True, exist_ok=True)
    dst = approved_dir / f"{key}{safe_ext(src)}"
    shutil.copy2(src, dst)
    info = {
        "path": repo_relative(dst),
        "sha256": sha256_file(dst),
        "width": data["canvas"]["width"],
        "height": data["canvas"]["height"],
        "promoted_at": now_iso(),
        "source_sha256": candidate_info.get("sha256"),
    }
    frame["approved_asset"] = info
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: approved -> {dst}")


def cmd_lock(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    approved = frame.get("approved_asset")
    if not isinstance(approved, dict) or not approved.get("sha256"):
        raise SystemExit("promote approved asset before locking")
    frame["lock"] = {"at": now_iso(), "sha256": approved["sha256"], "reason": args.reason}
    frame["status"] = "LOCKED"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: LOCKED sha256={approved['sha256']}")


def cmd_batch_begin(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    frames = parse_frame_set(args.frames)
    valid = data.get("frames") or {}
    missing = [x for x in frames if x not in valid]
    if missing:
        raise SystemExit(f"unknown frames: {missing}")
    batch = {
        "batch_id": uuid.uuid4().hex[:10],
        "started_at": now_iso(),
        "ended_at": None,
        "frames": frames,
        "max_successes": args.max_successes,
        "note": args.note,
        "status": "open",
    }
    data.setdefault("batches", []).append(batch)
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"batch {batch['batch_id']} open: {','.join(frames)}")


def cmd_batch_end(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    for batch in reversed(data.get("batches") or []):
        if batch.get("batch_id") == args.batch_id:
            if batch.get("status") != "open":
                raise SystemExit("batch already closed")
            batch["status"] = "closed"
            batch["ended_at"] = now_iso()
            batch["summary"] = args.summary
            data["updated_at"] = now_iso()
            save_json(path, data)
            print(f"batch {args.batch_id} closed")
            return
    raise SystemExit(f"batch not found: {args.batch_id}")


def cmd_audit(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    _, data = get_ledger(ep)
    failures: list[str] = []
    warnings: list[str] = []
    expected = (data["canvas"]["width"], data["canvas"]["height"])
    for key, frame in (data.get("frames") or {}).items():
        status = frame.get("status")
        if status not in FRAME_STATES:
            failures.append(f"{key}: invalid status {status!r}")
        if frame.get("content_repairs_used", 0) > content_repair_limit(data):
            failures.append(f"{key}: content repair count exceeds frozen policy")
        exception_repairs = frame.get("user_exception_repairs_used", 0)
        approvals = frame.get("user_exception_authorizations") or []
        if exception_repairs > 1:
            failures.append(f"{key}: user exception repair count > 1")
        if exception_repairs and not any(
            item.get("user_approved") is True
            and item.get("approval_basis") == "direct_user_review_exception"
            and item.get("approval_text")
            for item in approvals if isinstance(item, dict)
        ):
            failures.append(f"{key}: user exception repair lacks direct user approval evidence")
        approved = frame.get("approved_asset")
        if isinstance(approved, dict) and approved.get("path"):
            p = (repo_root() / approved["path"]).resolve()
            if not p.is_file():
                failures.append(f"{key}: approved asset missing: {approved['path']}")
            else:
                dims = image_dimensions(p)
                if dims != expected:
                    failures.append(f"{key}: approved size {dims}, expected {expected}")
                actual = sha256_file(p)
                if actual != approved.get("sha256"):
                    failures.append(f"{key}: approved hash drift")
        lock = frame.get("lock")
        if isinstance(lock, dict) and isinstance(approved, dict) and lock.get("sha256") != approved.get("sha256"):
            failures.append(f"{key}: lock hash != approved hash")
        if args.require_passed and status not in ACCEPTED_LEDGER_STATES:
            failures.append(f"{key}: not passed ({status})")
        if status == "TECH_FAILED":
            warnings.append(f"{key}: pending technical retry")
    for item in warnings:
        print(f"[WARN] {item}")
    for item in failures:
        print(f"[FAIL] {item}")
    if failures:
        raise SystemExit(1)
    print(f"PASS: production ledger; canvas={data['canvas']['aspect_ratio']} {expected[0]}脳{expected[1]}")


def cmd_show(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    _, data = get_ledger(ep)
    if args.frame:
        key, frame = frame_obj(data, args.frame)
        print(json.dumps({key: frame}, ensure_ascii=False, indent=2))
    else:
        summary = {
            "canvas": data.get("canvas"),
            "frames": {k: v.get("status") for k, v in (data.get("frames") or {}).items()},
            "open_batches": [b for b in data.get("batches") or [] if b.get("status") == "open"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
