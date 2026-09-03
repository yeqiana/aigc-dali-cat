#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from canvas_spec import DEFAULT_ASPECT_RATIO, resolve_canvas_spec
from visual_profile import compile_prompt_contract
import frame_contract as resolved_frame_contract
import storyos_config

LEDGER_FILE = Path("meta/production-ledger.json")
MANIFEST_FILE = Path("meta/release-manifest.json")
ENGINE_VERSION = "1.2"
PROMPT_CHAR_LIMIT = 260
PROMPT_BYTE_LIMIT = 900
_CONFIG = storyos_config.load_config()
DEFAULT_IMAGE_QUALITY = str(storyos_config.get_path(_CONFIG, "image.quality"))
FRAME_STATES = {
    "PENDING",
    "GENERATING",
    "TECH_FAILED",
    "ORIGINAL_READY",
    "CONTENT_FAILED",
    "REPAIR_AUTHORIZED",
    "EXCEPTION_REPAIR_AUTHORIZED",
    "REPAIRING",
    "REPAIR_READY",
    "PASSED",
    "NEEDS_USER",
    "LOCKED",
}
REFERENCE_KINDS = {"identity", "prop", "location", "capture_style"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return data


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def episode_dir(raw: str) -> Path:
    p = Path(raw).resolve()
    if not p.is_dir():
        raise SystemExit(f"episode directory not found: {p}")
    return p


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def image_dimensions(path: Path) -> tuple[int, int] | None:
    ext = path.suffix.lower()
    try:
        if ext == ".png":
            head = path.read_bytes()[:24]
            if len(head) >= 24 and head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
                return struct.unpack(">II", head[16:24])
            return None
        if ext in {".jpg", ".jpeg"}:
            with path.open("rb") as f:
                if f.read(2) != b"\xff\xd8":
                    return None
                while True:
                    b = f.read(1)
                    if not b:
                        return None
                    if b != b"\xff":
                        continue
                    marker = f.read(1)
                    while marker == b"\xff":
                        marker = f.read(1)
                    if not marker:
                        return None
                    code = marker[0]
                    if code in {0xD8, 0xD9}:
                        continue
                    raw_len = f.read(2)
                    if len(raw_len) != 2:
                        return None
                    length = struct.unpack(">H", raw_len)[0]
                    if length < 2:
                        return None
                    if code in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
                        payload = f.read(length - 2)
                        if len(payload) < 5:
                            return None
                        height, width = struct.unpack(">HH", payload[1:5])
                        return width, height
                    f.seek(length - 2, 1)
    except OSError:
        return None
    return None


def read_manifest(ep: Path) -> dict | None:
    p = ep / MANIFEST_FILE
    return load_json(p) if p.exists() else None


def resolve_episode_canvas(ep: Path, override: str | None = None):
    manifest = read_manifest(ep)
    manifest_ratio = ((manifest.get("episode") or {}).get("aspect_ratio")) if manifest else None
    if override:
        override_spec = resolve_canvas_spec(override)
        if manifest_ratio and resolve_canvas_spec(manifest_ratio).aspect_ratio != override_spec.aspect_ratio:
            raise SystemExit(f"aspect-ratio override {override_spec.aspect_ratio} conflicts with Episode manifest lock {manifest_ratio}")
        return override_spec, "override"
    if manifest_ratio:
        return resolve_canvas_spec(manifest_ratio), "manifest"
    return resolve_canvas_spec(DEFAULT_ASPECT_RATIO), "default"


def frame_count(ep: Path, explicit: int | None = None) -> int:
    if explicit is not None:
        if explicit <= 0:
            raise SystemExit("frame count must be > 0")
        return explicit
    manifest = read_manifest(ep)
    if manifest:
        value = ((manifest.get("release") or {}).get("body_frame_count"))
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
    return 20


def blank_frame(number: int) -> dict:
    return {
        "number": number,
        "status": "PENDING",
        "content_repairs_used": 0,
        "technical_failures": [],
        "attempts": [],
        "current_candidate": None,
        "approved_asset": None,
        "lock": None,
        "reviews": [],
    }


def init_ledger(ep: Path, *, count: int | None = None, ratio: str | None = None, overwrite: bool = False) -> dict:
    path = ep / LEDGER_FILE
    if path.exists() and not overwrite:
        return load_json(path)
    spec, source = resolve_episode_canvas(ep, ratio)
    total = frame_count(ep, count)
    data = {
        "schema_version": 1,
        "engine_version": ENGINE_VERSION,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "note": "Per-frame production transaction ledger. This is NOT an episode stage source.",
        "canvas": {
            "aspect_ratio": spec.aspect_ratio,
            "width": spec.width,
            "height": spec.height,
            "source": source,
        },
        "policy": {
            "default_aspect_ratio": DEFAULT_ASPECT_RATIO,
            "prompt_char_limit": PROMPT_CHAR_LIMIT,
            "prompt_byte_limit": PROMPT_BYTE_LIMIT,
            "max_content_repairs_per_frame": 1,
            "technical_failures_consume_content_repair": False,
            "image_quality": DEFAULT_IMAGE_QUALITY,
            "normalize_enabled": True,
            "preserve_raw": True,
            "final_format": "PNG",
            "resize_algorithm": "Lanczos",
            "default_crop": "forbidden",
            "imageops_fit": "exception_only",
            "automatic_ratio_delta_max": float(storyos_config.get_path(_CONFIG, "normalize.automatic_ratio_delta_max")),
            "review_ratio_delta_max": float(storyos_config.get_path(_CONFIG, "normalize.review_ratio_delta_max")),
            "reject_ratio_delta_above": float(storyos_config.get_path(_CONFIG, "normalize.review_ratio_delta_max")),
            "noop_when_exact_match": True,
            "technical_failure_triggers_generation": False,
        },
        "asset_roots": {
            "raw": "media/raw",
            "originals": "media/candidates/originals",
            "repairs": "media/candidates/repairs",
            "approved": "media/approved",
            "publish": "media/publish",
            "contact_sheets": "media/review/contact-sheets",
        },
        "frames": {f"{i:02d}": blank_frame(i) for i in range(1, total + 1)},
        "batches": [],
    }
    for rel in data["asset_roots"].values():
        (ep / rel).mkdir(parents=True, exist_ok=True)
    save_json(path, data)
    return data


def get_ledger(ep: Path) -> tuple[Path, dict]:
    path = ep / LEDGER_FILE
    if not path.exists():
        data = init_ledger(ep)
    else:
        data = load_json(path)
    return path, data


def frame_obj(data: dict, raw: str) -> tuple[str, dict]:
    try:
        n = int(raw)
    except ValueError:
        raise SystemExit(f"invalid frame: {raw}")
    key = f"{n:02d}"
    frames = data.get("frames")
    if not isinstance(frames, dict) or key not in frames:
        raise SystemExit(f"frame {key} not registered")
    frame = frames[key]
    if frame.get("status") not in FRAME_STATES:
        raise SystemExit(f"frame {key} has invalid status: {frame.get('status')!r}")
    return key, frame


def prompt_text(args: argparse.Namespace) -> str:
    if bool(args.prompt) == bool(args.prompt_file):
        raise SystemExit("provide exactly one of --prompt or --prompt-file")
    if args.prompt:
        text = args.prompt
    else:
        p = Path(args.prompt_file)
        if not p.is_file():
            raise SystemExit(f"prompt file not found: {p}")
        text = p.read_text(encoding="utf-8")
    text = text.strip()
    if not text:
        raise SystemExit("prompt cannot be empty")
    chars, nbytes = len(text), len(text.encode("utf-8"))
    if not args.allow_long_prompt and (chars > PROMPT_CHAR_LIMIT or nbytes > PROMPT_BYTE_LIMIT):
        raise SystemExit(
            f"prompt budget exceeded: {chars} chars/{nbytes} bytes; "
            f"limit={PROMPT_CHAR_LIMIT} chars/{PROMPT_BYTE_LIMIT} bytes. "
            "Shorten the per-frame prompt or use --allow-long-prompt with an explicit reason in notes."
        )
    return text


def parse_references(values: list[str] | None) -> list[dict]:
    out = []
    for value in values or []:
        parts = value.split("::")
        if len(parts) != 3:
            raise SystemExit("--reference format must be PATH::ROLE::KIND")
        raw_path, role, kind = (x.strip() for x in parts)
        if kind not in REFERENCE_KINDS:
            raise SystemExit(f"invalid reference kind {kind!r}; choose {sorted(REFERENCE_KINDS)}")
        p = Path(raw_path).resolve()
        if not p.is_file():
            raise SystemExit(f"reference file not found: {p}")
        out.append({
            "path": repo_relative(p),
            "role": role,
            "kind": kind,
            "sha256": sha256_file(p),
        })
    if len(out) > 2:
        raise SystemExit("formal request supports at most 2 references by default; reduce references or split continuity anchors")
    return out


def _version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def creative_enforcement_required(ep: Path) -> bool:
    for rel in ("meta/episode-state.json", "meta/release-manifest.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            if _version_tuple(load_json(p).get("tool_version")) >= (2, 0, 3, 2):
                return True
        except Exception:
            continue
    return False


def approved_capture_style_source(ep: Path, ref_path: str) -> str | None:
    gates_path = ep / "meta/story-gates.json"
    if not gates_path.is_file():
        return None
    gates = load_json(gates_path)
    visual = gates.get("visual") or {}
    calibration = visual.get("calibration") or {}
    passed_paths = set()
    if isinstance(calibration.get("items"), list):
        for item in calibration["items"]:
            if isinstance(item, dict) and item.get("decision") in {"passed", "pass"}:
                raw = item.get("path") or item.get("asset_path")
                if raw:
                    try:
                        passed_paths.add(repo_relative(Path(raw).resolve() if Path(raw).is_absolute() else repo_root() / raw))
                    except Exception:
                        pass
    else:
        for key in ("baseline", "worst_condition", "first_major_anomaly"):
            item = calibration.get(key) or {}
            if item.get("decision") in {"passed", "pass"}:
                raw = item.get("asset_path") or item.get("path")
                if raw:
                    try:
                        passed_paths.add(repo_relative(Path(raw).resolve() if Path(raw).is_absolute() else repo_root() / raw))
                    except Exception:
                        pass
    if ref_path in passed_paths:
        return "approved_calibration"

    for item in ((visual.get("references") or {}).get("items") or []):
        if not isinstance(item, dict) or item.get("decision") not in {"passed", "pass"}:
            continue
        raw = item.get("path")
        kind = item.get("reference_kind") or item.get("kind")
        if not raw or kind != "capture_style":
            continue
        p = Path(raw)
        rel = repo_relative(p.resolve() if p.is_absolute() else repo_root() / p)
        if rel == ref_path:
            return "approved_reference"
    return None


def enforce_capture_style_provenance(ep: Path, refs: list[dict]) -> None:
    if not creative_enforcement_required(ep):
        return
    for ref in refs:
        if ref.get("kind") != "capture_style":
            continue
        source = approved_capture_style_source(ep, str(ref.get("path") or ""))
        if source is None:
            raise SystemExit(
                "capture_style reference must be an approved calibration frame or an explicitly "
                "passed capture_style reference; unapproved generated frames cannot recursively define style"
            )
        ref["source_kind"] = source


def current_visual_provenance(ep: Path) -> dict:
    contract = compile_prompt_contract(ep)
    return {
        "profile_id": contract["profile_id"],
        "profile_path": contract["profile_path"],
        "profile_sha256": contract["profile_sha256"],
        "capture_profile": contract["capture_profile"],
    }


def current_frame_contract_provenance(ep: Path, frame: str) -> dict | None:
    return resolved_frame_contract.provenance(ep, frame)


def verify_attempt_frame_contract_provenance(ep: Path, frame: str, attempt: dict) -> None:
    if not resolved_frame_contract.required(ep):
        return
    request = attempt.get("request") or {}
    errors = resolved_frame_contract.verify_recorded_provenance(ep, frame, request.get("frame_contract"))
    if errors:
        raise SystemExit("; ".join(errors))


def verify_attempt_visual_provenance(ep: Path, attempt: dict) -> None:
    request = attempt.get("request") or {}
    recorded = request.get("visual_profile")
    if not isinstance(recorded, dict):
        if creative_enforcement_required(ep):
            raise SystemExit("generation attempt missing visual profile provenance")
        return
    current = current_visual_provenance(ep)
    for key in ("profile_id", "profile_path", "profile_sha256", "capture_profile"):
        if str(recorded.get(key)) != str(current.get(key)):
            raise SystemExit(f"visual profile drift before candidate acceptance: {key}")

def request_fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def active_attempt(frame: dict) -> dict:
    attempts = frame.get("attempts") or []
    if not attempts:
        raise SystemExit("frame has no generation attempt")
    attempt = attempts[-1]
    if attempt.get("result") not in {None, "pending"}:
        raise SystemExit("latest attempt is already closed")
    return attempt


def cmd_init(args: argparse.Namespace) -> None:
    ep = episode_dir(args.episode_dir)
    path = ep / LEDGER_FILE
    if path.exists() and not args.force:
        raise SystemExit(f"ledger already exists: {path}")
    data = init_ledger(ep, count=args.frame_count, ratio=args.aspect_ratio, overwrite=args.force)
    c = data["canvas"]
    print(f"initialized {path}")
    print(f"canvas: {c['aspect_ratio']} / {c['width']}×{c['height']} ({c['source']})")


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
    if kind == "repair" and status not in {"REPAIR_AUTHORIZED", "EXCEPTION_REPAIR_AUTHORIZED", "TECH_FAILED"}:
        raise SystemExit(f"repair requires REPAIR_AUTHORIZED, EXCEPTION_REPAIR_AUTHORIZED, or TECH_FAILED retry; got {status}")
    if kind == "repair" and status == "REPAIR_AUTHORIZED":
        if frame.get("content_repairs_used", 0) >= 1:
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
    attempt["result"] = "success"
    attempt["completed_at"] = now_iso()
    attempt["candidate"] = candidate_info
    frame["current_candidate"] = candidate_info
    frame["status"] = "ORIGINAL_READY" if attempt["kind"] == "original" else "REPAIR_READY"
    data["updated_at"] = now_iso()
    save_json(path, data)
    print(f"{key}: {frame['status']} {dims[0]}×{dims[1]} sha256={candidate_info['sha256']}")


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
        if was_repair or frame.get("content_repairs_used", 0) >= 1:
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
    if frame.get("content_repairs_used", 0) >= 1:
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


def safe_ext(path: Path) -> str:
    ext = path.suffix.lower()
    return ext if ext in {".png", ".jpg", ".jpeg"} else ".png"


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


def parse_frame_set(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        for part in item.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                start, end = int(a), int(b)
                if end < start:
                    raise SystemExit(f"invalid frame range {part}")
                out.extend(f"{i:02d}" for i in range(start, end + 1))
            else:
                out.append(f"{int(part):02d}")
    return list(dict.fromkeys(out))


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
        if frame.get("content_repairs_used", 0) > 1:
            failures.append(f"{key}: content repair count > 1")
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
        if args.require_passed and status not in {"PASSED", "LOCKED"}:
            failures.append(f"{key}: not passed ({status})")
        if status == "TECH_FAILED":
            warnings.append(f"{key}: pending technical retry")
    for item in warnings:
        print(f"[WARN] {item}")
    for item in failures:
        print(f"[FAIL] {item}")
    if failures:
        raise SystemExit(1)
    print(f"PASS: production ledger; canvas={data['canvas']['aspect_ratio']} {expected[0]}×{expected[1]}")


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


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Story OS V1.2 Production Engine ledger")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="initialize per-frame ledger; default canvas is 4:5 / 1080x1350")
    s.add_argument("episode_dir")
    s.add_argument("--frame-count", type=int)
    s.add_argument("--aspect-ratio", help="4:5 or 9:16; omitted => manifest, then default 4:5")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("begin", help="record generation preflight and request fingerprint")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--kind", choices=["original", "repair"], default="original")
    s.add_argument("--prompt")
    s.add_argument("--prompt-file")
    s.add_argument("--capture-id", required=True)
    s.add_argument("--model", default="default")
    s.add_argument("--quality", choices=["high"], default=DEFAULT_IMAGE_QUALITY)
    s.add_argument("--reference", action="append", help="PATH::ROLE::KIND, KIND=identity|prop|location|capture_style")
    s.add_argument("--notes", default="")
    s.add_argument("--allow-long-prompt", action="store_true")
    s.set_defaults(func=cmd_begin)

    s = sub.add_parser("success", help="record a generated candidate; dimensions must exactly match canvas")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--path", required=True)
    s.set_defaults(func=cmd_success)

    s = sub.add_parser("tech-fail", help="record network/timeout/no-candidate failure without consuming content repair")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--code", required=True)
    s.add_argument("--message", required=True)
    s.set_defaults(func=cmd_tech_fail)

    s = sub.add_parser("review", help="content review for ready candidate")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--decision", choices=["pass", "repair", "needs_user"], required=True)
    s.add_argument("--notes", default="")
    s.set_defaults(func=cmd_review)

    s = sub.add_parser("authorize-repair", help="explicitly authorize the single content repair round")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--note", required=True)
    s.add_argument("--delegated-auto", action="store_true", help="continuous-execution agent approval; does not claim direct user review")
    s.set_defaults(func=cmd_authorize_repair)

    s = sub.add_parser("authorize-user-locked-repair", help="reopen a locked frame for its first ordinary repair with direct user scope approval")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_authorize_user_locked_repair)

    s = sub.add_parser("authorize-user-exception-repair", help="record one direct-user exception after the ordinary repair hard-fails")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_authorize_user_exception_repair)

    s = sub.add_parser("accept-user-exception-candidate", help="accept an existing NEEDS_USER exception candidate with direct user approval")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_accept_user_exception_candidate)

    s = sub.add_parser("restore-evidence-gap-review", help="restore a candidate incorrectly failed solely by an unavailable-input review")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_restore_evidence_gap_review)

    s = sub.add_parser("promote", help="copy current passed candidate into production/approved without overwriting source")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.set_defaults(func=cmd_promote)

    s = sub.add_parser("lock", help="lock approved asset by SHA-256")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_lock)

    s = sub.add_parser("batch-begin", help="open an auditable generation batch")
    s.add_argument("episode_dir")
    s.add_argument("--frames", action="append", required=True, help="e.g. 01-03 or 01,03,05")
    s.add_argument("--max-successes", type=int, default=3)
    s.add_argument("--note", default="")
    s.set_defaults(func=cmd_batch_begin)

    s = sub.add_parser("batch-end", help="close a generation batch")
    s.add_argument("episode_dir")
    s.add_argument("--batch-id", required=True)
    s.add_argument("--summary", default="")
    s.set_defaults(func=cmd_batch_end)

    s = sub.add_parser("audit", help="audit ledger invariants and asset hashes")
    s.add_argument("episode_dir")
    s.add_argument("--require-passed", action="store_true")
    s.set_defaults(func=cmd_audit)

    s = sub.add_parser("show")
    s.add_argument("episode_dir")
    s.add_argument("--frame")
    s.set_defaults(func=cmd_show)
    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
