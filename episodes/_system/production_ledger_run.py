"""Production ledger runtime commands (Story OS B4 split).

Runtime lane: begin / success / tech-fail / review / authorize-repair /
restore-evidence-gap-review. Shared library globals are imported from
production_ledger_core; the CLI facade re-exports these command functions.
"""
from __future__ import annotations

from production_ledger_core import *  # noqa: F401,F403  (shared ledger globals)
import identity_continuity  # STORY_OS_P1_1_IDENTITY_CONTINUITY
import story_semantic_trace  # STORY_OS_W22_STORY_SEMANTIC_TRACE

def declared_reference_contract(ep: Path) -> bool | None:
    """True when story-gates declares required reference/identity anchors.

    None means the episode has no reference registry at all (legacy episodes),
    so no execution evidence is recorded and no new gate rule applies.
    """
    gates_path = ep / "meta/story-gates.json"
    if not gates_path.is_file():
        return None
    try:
        gates = load_json(gates_path)
    except Exception:
        return None
    visual = gates.get("visual") if isinstance(gates, dict) else None
    refs = visual.get("references") if isinstance(visual, dict) else None
    if not isinstance(refs, dict):
        return None
    return refs.get("required") is True


def build_reference_execution(ep: Path, refs: list[dict], *, started_at: str) -> dict | None:
    """W-21 attempt-level record of which references this generation used.

    The record starts as intent (selected references + required flag). It is only
    upgraded to verified execution evidence when the provider receipt proves the
    same files reached the image provider.
    """
    required = declared_reference_contract(ep)
    if required is None:
        return None
    selected = [
        {
            "id": str(ref.get("id") or ref.get("role") or ""),
            "path": ref.get("path"),
            "sha256": ref.get("sha256"),
            "role": ref.get("role"),
            "kind": ref.get("kind"),
        }
        for ref in refs
    ]
    return {
        "required": bool(required),
        "selected_references": selected,
        "passed_to_provider": False,
        "provider": None,
        "provider_receipt_id": None,
        "verified": False,
        "recorded_at": started_at,
    }


def merge_provider_reference_evidence(attempt: dict, receipt_data: dict, provider_receipt: dict) -> dict:
    """Bind provider receipt reference evidence onto the attempt record.

    verified is true only when every reference really sent to the provider matches
    the SHA-256 declared when the attempt began. Drift (or a declared reference that
    never reached the provider) keeps verified false, which the gate rejects.
    """
    evidence = dict(attempt.get("reference_execution") or {})
    declared = {}
    for row in ((attempt.get("request") or {}).get("references") or []):
        if isinstance(row, dict) and row.get("path"):
            declared[str(row["path"])] = row
    sent = [row for row in (receipt_data.get("references") or []) if isinstance(row, dict) and row.get("path")]
    selected = []
    verified = bool(sent)
    for index, row in enumerate(sent, 1):
        path = str(row["path"])
        source = declared.get(path) or {}
        selected.append({
            "id": str(source.get("id") or source.get("role") or ""),
            "path": path,
            "sha256": row.get("sha256"),
            "role": source.get("role"),
            "kind": source.get("kind"),
            "order": int(row.get("order") or index),
        })
        expected = str(source.get("sha256") or "").lower()
        actual = str(row.get("sha256") or "").lower()
        if not expected or expected != actual:
            verified = False
    if declared and not sent:
        verified = False
    evidence.update({
        "selected_references": selected,
        "passed_to_provider": bool(sent),
        "provider": str(receipt_data.get("generation_route") or receipt_data.get("provider") or "") or None,
        "provider_receipt_id": str((provider_receipt or {}).get("sha256") or receipt_data.get("capability_id") or "") or None,
        "provider_receipt_path": (provider_receipt or {}).get("path"),
        "verified": verified,
        "verified_at": now_iso(),
    })
    return evidence

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
    reference_execution = build_reference_execution(ep, refs, started_at=attempt["started_at"])
    if reference_execution is not None:
        attempt["reference_execution"] = reference_execution
        if reference_execution["required"]:
            # W-21: mark the ledger as evidence-aware so the machine gate can require
            # reference execution evidence without failing historical episodes.
            data.setdefault("reference_execution_evidence", {
                "schema_version": 1,
                "enforced_from": attempt["started_at"],
                "runs_from_attempt": attempt["attempt_id"],
                "note": "reference execution evidence is recorded from this attempt onward",
            })
    # P1-1: mark the ledger identity-evidence aware when the episode declares
    # required identity anchors, so the machine gate can require frame-level
    # identity continuity evidence without failing historical episodes.
    if identity_continuity.identity_contract(ep).get("required"):
        data.setdefault("identity_continuity_evidence", {
            "schema_version": 1,
            "enforced_from": attempt["started_at"],
            "runs_from_attempt": attempt["attempt_id"],
            "characters": sorted(identity_continuity.identity_contract(ep).get("characters") or {}),
            "note": "identity pixel continuity evidence is recorded from this attempt onward",
        })
    # W-22: mark the ledger story-semantic-trace aware when the episode declares a
    # story role map, so the gate can require per-frame semantic evidence without
    # failing historical episodes.
    if story_semantic_trace.required(ep):
        data.setdefault("story_semantic_trace_evidence", {
            "schema_version": 1,
            "enforced_from": attempt["started_at"],
            "runs_from_attempt": attempt["attempt_id"],
            "note": "story semantic trace evidence is recorded from this attempt onward",
        })
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
        if isinstance(attempt.get("reference_execution"), dict):
            attempt["reference_execution"] = merge_provider_reference_evidence(attempt, receipt_data, provider_receipt)
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
    delegated = bool(getattr(args, "delegated_auto", False))
    # STORY_OS_DELEGATED_LOCKED_REPAIR (additive): an authorized full-set semantic
    # critic can still find a real content defect after the release lock. That
    # repair is content-bearing, so it still consumes the ordinary repair budget,
    # but it must be recorded as delegated auto review. Reopening a locked frame
    # without --delegated-auto remains reserved for the direct-user lanes.
    if frame["status"] == "LOCKED":
        if not delegated:
            raise SystemExit("locked frame repair requires --delegated-auto or authorize-user-locked-repair")
        if not str(getattr(args, "note", "") or "").strip():
            raise SystemExit("locked frame delegated repair requires an evidence note")
        frame.setdefault("superseded_locks", []).append({
            "at": now_iso(),
            "lock": frame.get("lock"),
            "approved_asset": frame.get("approved_asset"),
            "reason": "delegated auto review found a content defect after lock",
        })
    elif frame["status"] != "CONTENT_FAILED":
        raise SystemExit(f"repair authorization requires CONTENT_FAILED, got {frame['status']}")
    if frame.get("content_repairs_used", 0) >= content_repair_limit(data):
        raise SystemExit("content repair limit reached")
    frame["status"] = "REPAIR_AUTHORIZED"
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
