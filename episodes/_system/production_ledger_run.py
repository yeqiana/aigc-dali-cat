"""Production ledger runtime commands (Story OS B4 split).

Runtime lane: begin / success / tech-fail / review / authorize-repair /
restore-evidence-gap-review. Shared library globals are imported from
production_ledger_core; the CLI facade re-exports these command functions.
"""
from __future__ import annotations

from production_ledger_core import *  # noqa: F401,F403  (shared ledger globals)

def cmd_begin(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    kind = args.kind
    status = frame["status"]
    last_kind = (frame.get("attempts") or [{}])[-1].get("kind")
    if status == "TECH_FAILED" and last_kind and kind != last_kind:
        raise SystemExit(f"technical retry must preserve attempt kind {last_kind!r}")
    if kind == "original" and status not in {"PENDING", "TECH_FAILED"}:
        raise SystemExit(f"cannot begin original from {status}")
    if kind == "repair" and status not in {"REPAIR_AUTHORIZED", "AUTHORITY_REFRESH_AUTHORIZED", "EXCEPTION_REPAIR_AUTHORIZED", "TECH_FAILED"}:
        raise SystemExit(f"repair requires REPAIR_AUTHORIZED, AUTHORITY_REFRESH_AUTHORIZED, EXCEPTION_REPAIR_AUTHORIZED, or TECH_FAILED retry; got {status}")
    if kind == "repair" and status == "REPAIR_AUTHORIZED":
        if frame.get("content_repairs_used", 0) >= content_repair_limit(data):
            raise SystemExit("content repair limit reached")
        frame["content_repairs_used"] = frame.get("content_repairs_used", 0) + 1
    if kind == "repair" and status == "EXCEPTION_REPAIR_AUTHORIZED":
        if frame.get("user_exception_repairs_used", 0) >= 1:
            raise SystemExit("user exception repair limit reached")
        frame["user_exception_repairs_used"] = frame.get("user_exception_repairs_used", 0) + 1

    text = prompt_text(args)
    refs = parse_references(args.reference)
    enforce_capture_style_provenance(ep, refs)
    visual_provenance = current_visual_provenance(ep)
    frame_contract_provenance = current_frame_contract_provenance(ep, key)
    c = data["canvas"]
    payload = {
        "frame": key,
        "kind": kind,
        "prompt_sha256": sha256_bytes(text.encode("utf-8")),
        "prompt_chars": len(text),
        "prompt_bytes": len(text.encode("utf-8")),
        "capture_id": args.capture_id,
        "model": args.model,
        "quality": args.quality,
        "canvas": {"aspect_ratio": c["aspect_ratio"], "width": c["width"], "height": c["height"]},
        "references": refs,
        "visual_profile": visual_provenance,
        "frame_contract": frame_contract_provenance,
        "frame_contract_sha256": (frame_contract_provenance or {}).get("contract_sha256"),
        "batch_id": getattr(args, "batch_id", None),
    }
    attempt = {
        "attempt_id": uuid.uuid4().hex[:12],
        "started_at": now_iso(),
        "kind": kind,
        "request": payload,
        "request_fingerprint": request_fingerprint(payload),
        "notes": args.notes,
        "result": "pending",
    }
    if getattr(args, "runtime_transaction_id", None):
        attempt["runtime_transaction_id"] = str(args.runtime_transaction_id)
    frame.setdefault("attempts", []).append(attempt)
    frame["status"] = "GENERATING" if kind == "original" else "REPAIRING"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: {frame['status']} attempt={attempt['attempt_id']} fingerprint={attempt['request_fingerprint']}")


def cmd_success(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    attempt = active_attempt(frame)
    verify_attempt_visual_provenance(ep, attempt)
    verify_attempt_frame_contract_provenance(ep, key, attempt)
    candidate = Path(args.path).resolve()
    if not candidate.is_file():
        raise SystemExit(f"candidate not found: {candidate}")
    dims = image_dimensions(candidate)
    expected = (data["canvas"]["width"], data["canvas"]["height"])
    if dims is None:
        raise SystemExit("candidate image dimensions cannot be parsed")
    if dims != expected:
        raise SystemExit(f"candidate size {dims[0]}x{dims[1]} != expected {expected[0]}x{expected[1]}")
    candidate_info = {
        "path": repo_relative(candidate),
        "sha256": sha256_file(candidate),
        "width": dims[0],
        "height": dims[1],
        "recorded_at": now_iso(),
        "kind": attempt["kind"],
        "attempt_id": attempt["attempt_id"],
    }
    provider_receipt = None
    if getattr(args, "provider_receipt", None):
        receipt_path = Path(args.provider_receipt).resolve()
        if not receipt_path.is_file():
            raise SystemExit(f"provider receipt not found: {receipt_path}")
        receipt_data = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        if not isinstance(receipt_data, dict):
            raise SystemExit("provider receipt root must be object")
        if str(receipt_data.get("frame") or "") not in {"", key}:
            raise SystemExit(f"provider receipt frame mismatch: {receipt_data.get('frame')} != {key}")
        release_canvas = receipt_data.get("release_canvas") or {}
        if release_canvas and (release_canvas.get("width"), release_canvas.get("height")) != expected:
            raise SystemExit("provider receipt release canvas mismatch")
        provider_receipt = {
            "path": repo_relative(receipt_path),
            "sha256": sha256_file(receipt_path),
            "capability_id": receipt_data.get("capability_id"),
            "provider_raw_canvas": receipt_data.get("provider_raw_canvas"),
            "ratio_delta": receipt_data.get("ratio_delta"),
            "normalize_decision": receipt_data.get("normalize_decision"),
            "provider_attestation": receipt_data.get("provider_attestation"),
        }
        attempt["provider_receipt"] = provider_receipt
    attempt["result"] = "success"
    attempt["completed_at"] = now_iso()
    attempt["candidate"] = candidate_info
    frame["current_candidate"] = candidate_info
    frame["status"] = "ORIGINAL_READY" if attempt["kind"] == "original" else "REPAIR_READY"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: {frame['status']} {dims[0]}脳{dims[1]} sha256={candidate_info['sha256']}")


def cmd_tech_fail(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    attempt = active_attempt(frame)
    attempt["result"] = "technical_failure"
    attempt["completed_at"] = now_iso()
    attempt["error"] = {"code": args.code, "message": args.message}
    frame.setdefault("technical_failures", []).append({
        "at": now_iso(), "attempt_id": attempt["attempt_id"], "code": args.code, "message": args.message
    })
    frame["status"] = "TECH_FAILED"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: TECH_FAILED; content_repairs_used={frame.get('content_repairs_used', 0)} (unchanged)")


def cmd_review(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] not in {"ORIGINAL_READY", "REPAIR_READY"}:
        raise SystemExit(f"review requires ready candidate, got {frame['status']}")
    was_repair = frame["status"] == "REPAIR_READY"
    decision = args.decision
    frame.setdefault("reviews", []).append({"at": now_iso(), "decision": decision, "notes": args.notes})
    if decision == "pass":
        frame["status"] = "PASSED"
    elif decision == "repair":
        if was_repair or frame.get("content_repairs_used", 0) >= content_repair_limit(data):
            frame["status"] = "NEEDS_USER"
        else:
            frame["status"] = "CONTENT_FAILED"
    else:
        frame["status"] = "NEEDS_USER"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: {frame['status']}")


def cmd_authorize_repair(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] != "CONTENT_FAILED":
        raise SystemExit(f"repair authorization requires CONTENT_FAILED, got {frame['status']}")
    if frame.get("content_repairs_used", 0) >= content_repair_limit(data):
        raise SystemExit("content repair limit reached")
    frame["status"] = "REPAIR_AUTHORIZED"
    delegated = bool(getattr(args, "delegated_auto", False))
    frame["repair_authorization"] = {
        "at": now_iso(),
        "note": args.note,
        "user_approved": not delegated,
        "delegated_auto_review": delegated,
        "approval_basis": "delegated_auto_review" if delegated else "direct_user_review",
    }
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: REPAIR_AUTHORIZED")


def cmd_restore_evidence_gap_review(args: argparse.Namespace) -> None:
    """Restore a ready candidate when a review failed only from missing inputs."""
    ep = episode_dir(args.episode_dir)
    path, data = get_ledger(ep)
    key, frame = frame_obj(data, args.frame)
    if frame["status"] != "CONTENT_FAILED" or frame.get("content_repairs_used", 0) != 0:
        raise SystemExit("evidence-gap restore requires an un-repaired CONTENT_FAILED frame")
    reviews = frame.get("reviews") or []
    if not reviews or reviews[-1].get("notes") != "Phase5 Visual Lock critic failed actual-pixel admission":
        raise SystemExit("evidence-gap restore requires the Visual Lock critic review marker")
    candidate = frame.get("current_candidate") or {}
    raw_path = candidate.get("path")
    candidate_path = (repo_root() / raw_path).resolve() if raw_path and not Path(raw_path).is_absolute() else Path(raw_path or "")
    if not candidate_path.is_file() or sha256_file(candidate_path) != str(candidate.get("sha256") or "").lower():
        raise SystemExit("current candidate missing or hash drifted")
    kind = str(candidate.get("kind") or "")
    if kind not in {"original", "repair"}:
        raise SystemExit("candidate kind is not restorable")
    frame.setdefault("review_evidence_gaps", []).append({
        "at": now_iso(), "reason": args.reason, "restored_from": "CONTENT_FAILED",
        "review_marker": reviews[-1].get("notes"),
    })
    frame["status"] = "ORIGINAL_READY" if kind == "original" else "REPAIR_READY"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: {frame['status']} (restored after input-evidence gap)")
