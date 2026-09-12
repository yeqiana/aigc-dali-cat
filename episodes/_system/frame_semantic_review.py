#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

from PIL import Image

from story_os_contract import story_os_version
import codex_critic_runner as critic_runner
import environment_contract as phase3_env
import frame_contract as phase4_contract
import fast_frame_scout as phase7_scout
import runtime_router
import runtime_provenance
import product_review_adapter
import production_ledger
import story_json
import runtime_timeout_policy

ROOT = Path(__file__).resolve().parents[2]
REVIEW_DIR = Path("meta/frame-reviews")
SUMMARY_REL = Path("meta/frame-semantic-review.json")
CANDIDATE_REL = Path("meta/.frame-semantic-review.candidate.json")
EXCEPTION_CANDIDATE_REL = Path("meta/.frame-semantic-exception-review.candidate.json")
EXCEPTION_PENDING_REL = Path("meta/frame-semantic-exception-pending-attempt-3.json")
AUDIT_REL = Path("meta/frame-semantic-audit.json")
PENDING_REQUEST_PREFIX = "frame-semantic-pending-attempt-"
TARGET_CONTRACT = (2, 0, 3, 3)
SCHEMA_VERSION = 2

CHECKS = [
    "scene_storyboard_fidelity",
    "story_beat_fidelity",
    "key_prop_fidelity",
    "character_identity",
    "wardrobe_continuity",
    "pov_photographer_legality",
    "spatial_continuity",
    "temporal_continuity",
    "anomaly_readability",
    "caption_image_support",
    "actual_information_gain",
]

V22_VISUAL_NARRATIVE_CHECKS = [
    "camera_authorship_physical",
    "moment_capture_credibility",
    "narrative_evidence_gain",
    "shot_grammar_diversity",
    "camera_defect_physics",
    "screen_content_physics",
    "visual_memory_continuity",
]  # STORY_OS_V22_R2_VERSION_GATED

V21_PHASE3_CHECKS = [
    "environment_physics_fidelity",
    "anomaly_escalation_fidelity",
    "scale_reference_fidelity",
]

V221_WORLD_IDENTITY_CHECKS = [
    "world_identity_fidelity",
    "character_appearance_anchor_fidelity",
    "cultural_environment_fidelity",
]

DIRECTING_V3_CHECKS = [
    "shot_scale_fidelity",
    "scene_position_uniqueness_fidelity",
    "cinematic_structure_translation_fidelity",
    "practical_lighting_design_fidelity",
    "anomaly_concealment_fidelity",
]

def directing_v3_required(ep: Path) -> bool:
    p=Path(ep)/"meta/shot-progression-review.json"
    if not p.is_file(): return False
    try: return int(read_json(p).get("schema_version") or 0) >= 3
    except Exception: return False

def checks_for_version(version: str, directing_v3: bool = False) -> list[str]:
    checks = CHECKS + (V21_PHASE3_CHECKS if version_tuple(version) >= (2, 1, 0) else [])
    if version_tuple(version) >= (2, 2, 0):
        checks += V22_VISUAL_NARRATIVE_CHECKS
    if version_tuple(version) >= (2, 2, 1):
        checks += V221_WORLD_IDENTITY_CHECKS
    if directing_v3:
        checks += DIRECTING_V3_CHECKS
    return checks

ISSUE_CODES = {
    "FRAME_SCENE_MISMATCH",
    "STORY_BEAT_NOT_VISIBLE",
    "KEY_PROP_DRIFT",
    "IDENTITY_DRIFT",
    "WARDROBE_DRIFT",
    "POV_ILLEGAL",
    "SPATIAL_CONTINUITY_BROKEN",
    "TEMPORAL_CONTRADICTION",
    "ANOMALY_UNREADABLE",
    "CAPTION_DEPENDENCY",
    "ACTUAL_INFORMATION_GAIN_MISSING",
    "NEAR_DUPLICATE_ACTUAL_FRAMES",
    "UNEXPLAINED_THIRD_PERSON",
    "UNPLANNED_RECORDER",
    "WEATHER_PHYSICS_MISMATCH",
    "WEATHER_CONTINUITY_BROKEN",
    "ANOMALY_SCALE_UNDERDELIVERED",
    "SCALE_REFERENCE_MISSING",
    "GHOST_CAMERA",
    "CAMERA_OWNER_UNRESOLVED",
    "MOMENT_RESULT_ONLY",
    "NARRATIVE_REDUNDANCY",
    "SHOT_GRAMMAR_REPEAT",
    "CAMERA_DEFECT_UNMOTIVATED",
    "SCREEN_CONTENT_PHYSICS_BROKEN",
    "VISUAL_MEMORY_BROKEN",
    "WORLD_IDENTITY_DRIFT",
    "CHARACTER_APPEARANCE_DRIFT",
    "CULTURAL_CONTEXT_DRIFT",
    "SHOT_SCALE_MISMATCH",
    "SCENE_POSITION_VISUAL_REPEAT",
    "CINEMATIC_TRANSLATION_FAILED",
    "LIGHTING_DESIGN_MISMATCH",
    "ANOMALY_CONCEALMENT_MISSING",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    return story_json.read_json(path)


def write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(data: object) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def review_required(ep: Path) -> bool:
    for rel in ("meta/episode-state.json", "meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            if version_tuple(read_json(p).get("tool_version")) >= TARGET_CONTRACT:
                return True
        except Exception:
            continue
    return False


def episode_contract_version(ep: Path) -> str:
    versions: list[tuple[tuple[int, ...], str]] = []
    for rel in ("meta/episode-state.json", "meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    if versions:
        return max(versions, key=lambda x: x[0])[1]
    return story_os_version()


def repo_path(raw: object, where: str, *, require_file: bool = True) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{where} missing")
    rel = Path(raw.strip())
    p = rel.resolve() if rel.is_absolute() else (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{where} escapes repository") from exc
    if require_file and not p.is_file():
        raise ValueError(f"{where} missing: {raw}")
    return p


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def episode_files(ep: Path) -> tuple[Path, Path]:
    manifest = read_json(ep / "meta/release-manifest.json")
    artifacts = manifest.get("artifacts") or {}
    return (
        repo_path(artifacts.get("story"), "manifest.artifacts.story"),
        repo_path(artifacts.get("storyboard"), "manifest.artifacts.storyboard"),
    )


def stable_visual_contract(ep: Path) -> dict:
    gates = read_json(ep / "meta/story-gates.json")
    visual = gates.get("visual") or {}
    return {
        "visual_profile": gates.get("visual_profile") or {},
        "authenticity_card": visual.get("authenticity_card") or {},
        "continuity": visual.get("continuity") or {},
        "references": visual.get("references") or {},
    }


def context_hashes(ep: Path) -> dict:
    story, storyboard = episode_files(ep)
    return {
        "story_sha256": sha256_file(story),
        "storyboard_sha256": sha256_file(storyboard),
        "visual_contract_sha256": sha256_json(stable_visual_contract(ep)),
    }


def phase3_context_hashes(ep: Path, frame: str) -> dict:
    out = phase3_env.frame_hashes(ep, frame) if phase3_env.required(ep) else {}
    if phase4_contract.required(ep):
        contract = phase4_contract.compile_frame(ep, frame, write_cache=False)
        out["frame_contract_sha256"] = contract["contract_sha256"]
    return out


def source_binding(ep: Path, frame: str) -> dict:
    """Stable Story/Storyboard source footprint used by frame reviews."""
    if not phase4_contract.required(ep):
        return {}
    return phase4_contract.source_binding(ep, frame)


def review_source_bindings(ep: Path, frames: list[dict]) -> dict:
    """Freeze semantic inputs, not regenerated cache files with wall-clock stamps."""
    return {
        "story_os_version": episode_contract_version(ep),
        "contexts": context_hashes(ep),
        "frames": {row["frame"]: {
            "asset_path": row["path_rel"], "asset_sha256": row["sha256"],
            **phase3_context_hashes(ep, row["frame"]),
            "source_binding": source_binding(ep, row["frame"]),
        } for row in frames},
    }


def phase4_binding_errors(ep: Path, frames: list[dict]) -> list[str]:
    if not phase4_contract.required(ep):
        return []
    errors: list[str] = []
    for frame in frames:
        errors.extend(phase4_contract.verify_approved_asset_binding(ep, frame["frame"], frame["sha256"]))
    return errors



def frame_records(ep: Path, *, require_files: bool) -> list[dict]:
    ledger = read_json(ep / "meta/production-ledger.json")
    frames = ledger.get("frames")
    if not isinstance(frames, dict) or not frames:
        raise ValueError("production ledger frames missing")
    rows: list[dict] = []
    for key in sorted(frames):
        frame = frames[key]
        if not isinstance(frame, dict):
            raise ValueError(f"ledger frame {key} invalid")
        if frame.get("status") not in production_ledger.ACCEPTED_LEDGER_STATES:
            raise ValueError(f"frame {key} not production-passed: {frame.get('status')!r}")
        asset = frame.get("approved_asset")
        if not isinstance(asset, dict):
            raise ValueError(f"frame {key} approved_asset missing")
        raw_path = asset.get("path") or asset.get("asset_path")
        expected_sha = str(asset.get("sha256") or "").lower()
        if len(expected_sha) != 64:
            raise ValueError(f"frame {key} approved asset sha256 invalid")
        path = repo_path(raw_path, f"frame {key} approved_asset.path", require_file=require_files)
        if require_files:
            actual = sha256_file(path)
            if actual.lower() != expected_sha:
                raise ValueError(f"frame {key} approved asset SHA drift: ledger={expected_sha}, actual={actual}")
        rows.append({
            "frame": key.zfill(2),
            "path": path,
            "path_rel": repo_rel(path),
            "sha256": expected_sha,
        })
    return rows


def reviewable_frame_records(ep: Path, *, require_files: bool) -> list[dict]:
    """Return the complete production frame set before final promotion.

    Final semantic review is the authority that grants Production PASS.  It
    therefore must be able to inspect the current candidate before
    ``approved_asset`` exists; otherwise approval and review wait on each
    other.  Already-approved rows are reused by SHA.
    """
    ledger = read_json(ep / "meta/production-ledger.json")
    frames = ledger.get("frames")
    if not isinstance(frames, dict) or not frames:
        raise ValueError("production ledger frames missing")
    rows: list[dict] = []
    for key in sorted(frames):
        frame = frames[key]
        if not isinstance(frame, dict):
            raise ValueError(f"ledger frame {key} invalid")
        status = str(frame.get("status") or "")
        approved = frame.get("approved_asset") if isinstance(frame.get("approved_asset"), dict) else None
        candidate = frame.get("current_candidate") if isinstance(frame.get("current_candidate"), dict) else None
        if approved and status in production_ledger.ACCEPTED_LEDGER_STATES:
            asset = approved
            source_kind = "approved"
        elif candidate and status in production_ledger.READY_LEDGER_STATES:
            asset = candidate
            source_kind = "candidate"
        else:
            raise ValueError(f"frame {key} has no reviewable production asset: status={status!r}")
        raw_path = asset.get("path") or asset.get("asset_path")
        expected_sha = str(asset.get("sha256") or "").lower()
        if len(expected_sha) != 64:
            raise ValueError(f"frame {key} reviewable asset sha256 invalid")
        path = repo_path(raw_path, f"frame {key} {source_kind}.path", require_file=require_files)
        if require_files:
            actual = sha256_file(path)
            if actual.lower() != expected_sha:
                raise ValueError(f"frame {key} {source_kind} SHA drift: ledger={expected_sha}, actual={actual}")
        rows.append({
            "frame": key.zfill(2),
            "path": path,
            "path_rel": repo_rel(path),
            "sha256": expected_sha,
            "source_kind": source_kind,
            "ledger_status": status,
        })
    return rows


def reviewable_phase4_binding_errors(ep: Path, frames: list[dict]) -> list[str]:
    """Verify generation-contract binding for approved assets or live candidates."""
    if not phase4_contract.required(ep):
        return []
    ledger = read_json(ep / "meta/production-ledger.json")
    errors: list[str] = []
    for row in frames:
        key = row["frame"]
        if row.get("source_kind") == "approved":
            errors.extend(phase4_contract.verify_approved_asset_binding(ep, key, row["sha256"]))
            continue
        frame = ((ledger.get("frames") or {}).get(key) or {})
        candidate = frame.get("current_candidate") or {}
        attempt_id = str(candidate.get("attempt_id") or "")
        attempt = next((x for x in (frame.get("attempts") or []) if str(x.get("attempt_id") or "") == attempt_id), None)
        if not isinstance(attempt, dict):
            errors.append(f"frame {key} candidate generation attempt missing")
            continue
        expected = str(phase4_contract.compile_frame(ep, int(key), write_cache=False).get("contract_sha256") or "").lower()
        requested = str(((attempt.get("request") or {}).get("frame_contract_sha256")) or "").lower()
        if not requested or requested != expected:
            errors.append(f"frame {key} candidate Frame Contract drift: attempt={requested or 'missing'} current={expected}")
    return errors


def _bits_to_hex(bits: Iterable[bool]) -> str:
    value = 0
    count = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
        count += 1
    width = max(1, (count + 3) // 4)
    return f"{value:0{width}x}"


def _flat_pixels(image: Image.Image) -> list[int]:
    getter = getattr(image, "get_flattened_data", None)
    return list(getter() if callable(getter) else image.getdata())


def dhash256(path: Path) -> str:
    with Image.open(path) as im:
        gray = im.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
        px = _flat_pixels(gray)
    bits = []
    for y in range(16):
        row = y * 17
        for x in range(16):
            bits.append(px[row + x] > px[row + x + 1])
    return _bits_to_hex(bits)


def ahash256(path: Path) -> str:
    with Image.open(path) as im:
        gray = im.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
        px = _flat_pixels(gray)
    avg = sum(px) / len(px)
    return _bits_to_hex(v >= avg for v in px)


def hamming_hex(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def perceptual_rows(frames: list[dict]) -> list[dict]:
    out = []
    for row in frames:
        out.append({
            "frame": row["frame"],
            "asset_sha256": row["sha256"],
            "dhash256": dhash256(row["path"]),
            "ahash256": ahash256(row["path"]),
        })
    return out


def duplicate_pairs(phashes: list[dict]) -> list[dict]:
    by_frame = {row["frame"]: row for row in phashes}
    keys = sorted(by_frame)
    pairs: list[dict] = []
    for idx, key in enumerate(keys):
        left = by_frame[key]
        # Adjacent near-duplicates are a hard production failure.
        if idx + 1 < len(keys):
            right = by_frame[keys[idx + 1]]
            d = hamming_hex(left["dhash256"], right["dhash256"])
            a = hamming_hex(left["ahash256"], right["ahash256"])
            if d <= 8 and a <= 12:
                pairs.append({"frames": [key, right["frame"]], "dhash_distance": d, "ahash_distance": a, "kind": "adjacent_near_duplicate"})
        # Non-adjacent exact/virtually exact duplicates are also forbidden.
        for other_key in keys[idx + 2:]:
            right = by_frame[other_key]
            d = hamming_hex(left["dhash256"], right["dhash256"])
            a = hamming_hex(left["ahash256"], right["ahash256"])
            if d <= 2 and a <= 3:
                pairs.append({"frames": [key, other_key], "dhash_distance": d, "ahash_distance": a, "kind": "nonadjacent_near_duplicate"})
    return pairs


def validate_candidate_rows(rows: object, expected_frames: list[dict], version: str = "2.0.3.6", directing_v3: bool = False) -> list[str]:
    errors: list[str] = []
    expected = {row["frame"] for row in expected_frames}
    if not isinstance(rows, list) or len(rows) != len(expected_frames):
        return [f"critic must return exactly {len(expected_frames)} frame rows"]
    seen: set[str] = set()
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"frames[{idx}] must be object")
            continue
        key = str(row.get("frame") or "").zfill(2)
        if key not in expected:
            errors.append(f"unexpected frame row: {key}")
            continue
        if key in seen:
            errors.append(f"duplicate frame row: {key}")
        seen.add(key)
        checks = row.get("checks") or {}
        for check in checks_for_version(version, directing_v3):
            if checks.get(check) is not True:
                errors.append(f"frame {key} checks.{check} must be true")
        codes = row.get("issue_codes")
        if not isinstance(codes, list):
            errors.append(f"frame {key} issue_codes must be list")
        elif codes:
            unknown = [x for x in codes if x not in ISSUE_CODES]
            if unknown:
                errors.append(f"frame {key} unknown issue_codes: {unknown}")
            errors.append(f"frame {key} issue_codes must be empty for PASS: {codes}")
        if row.get("decision") != "pass":
            errors.append(f"frame {key} decision must be pass")
    if seen != expected:
        errors.append(f"critic frame set mismatch: expected={sorted(expected)}, actual={sorted(seen)}")
    return errors


def validate_candidate_gate_rows(rows: object, expected_frames: list[dict], version: str, directing_v3: bool) -> list[str]:
    """Validate a final critic result before it is allowed to mutate the ledger.

    Unlike ``validate_candidate_rows`` this accepts both pass and fail rows so
    failed candidates can enter the existing repair flow.  Schema/provenance
    errors never change Production Ledger state.
    """
    errors: list[str] = []
    expected = {row["frame"] for row in expected_frames}
    if not isinstance(rows, list) or len(rows) != len(expected_frames):
        return [f"critic must return exactly {len(expected_frames)} frame rows"]
    seen: set[str] = set()
    required_checks = checks_for_version(version, directing_v3)
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"frames[{idx}] must be object")
            continue
        key = str(row.get("frame") or "").zfill(2)
        if key not in expected:
            errors.append(f"unexpected frame row: {key}")
            continue
        if key in seen:
            errors.append(f"duplicate frame row: {key}")
        seen.add(key)
        checks = row.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"frame {key} checks must be object")
            continue
        missing = [name for name in required_checks if not isinstance(checks.get(name), bool)]
        if missing:
            errors.append(f"frame {key} checks missing/non-bool: {missing}")
        codes = row.get("issue_codes")
        if not isinstance(codes, list):
            errors.append(f"frame {key} issue_codes must be list")
            codes = []
        unknown = [x for x in codes if x not in ISSUE_CODES]
        if unknown:
            errors.append(f"frame {key} unknown issue_codes: {unknown}")
        decision = str(row.get("decision") or "")
        if decision not in {"pass", "fail"}:
            errors.append(f"frame {key} decision must be pass or fail")
        elif decision == "pass" and (codes or any(checks.get(name) is not True for name in required_checks)):
            errors.append(f"frame {key} pass requires all checks true and no issue_codes")
        elif decision == "fail" and not codes and all(checks.get(name) is True for name in required_checks):
            errors.append(f"frame {key} fail requires a visible failed check or issue_code")
    if seen != expected:
        errors.append(f"critic frame set mismatch: expected={sorted(expected)}, actual={sorted(seen)}")
    return errors


def pending_request_path(ep: Path, attempt: int) -> Path:
    return ep / "meta" / f"{PENDING_REQUEST_PREFIX}{attempt}.json"


def _pending_request_payload(ep: Path, frames: list[dict], attempt: int) -> dict:
    return {
        "schema_version": 1,
        "attempt": attempt,
        "recorded_at": now(),
        "contexts": context_hashes(ep),
        "assets": [
            {"frame": row["frame"], "path": row["path_rel"], "sha256": row["sha256"]}
            for row in frames
        ],
    }


def _ledger_frame(ep: Path, frame: str) -> dict:
    return ((read_json(ep / "meta/production-ledger.json").get("frames") or {}).get(str(frame).zfill(2)) or {})


def _apply_candidate_gate(
    ep: Path,
    *,
    data: dict,
    reviewed: list[dict],
    contexts: dict,
    provenance: dict,
    attempt: int,
) -> int:
    """Let the final semantic critic close candidate -> PASS -> approved -> lock."""
    version = episode_contract_version(ep)
    directing_v3 = directing_v3_required(ep)
    errors = validate_candidate_gate_rows(data.get("frames"), reviewed, version, directing_v3)
    global_codes = data.get("issue_codes")
    if not isinstance(global_codes, list):
        errors.append("global issue_codes must be list")
    elif any(code not in ISSUE_CODES for code in global_codes):
        errors.append(f"global issue_codes contain unknown values: {global_codes}")
    if errors:
        print("FRAME SEMANTIC CANDIDATE GATE INVALID")
        for error in errors:
            print("FAIL:", error)
        return 3

    rows = {str(row.get("frame") or "").zfill(2): row for row in data.get("frames") or []}
    failures: list[str] = []
    for source in reviewed:
        key = source["frame"]
        review = rows[key]
        status = str(_ledger_frame(ep, key).get("status") or "")
        notes = "Final semantic critic candidate review: " + str(review.get("notes") or review.get("issue_codes") or "")
        if review.get("decision") == "pass":
            if status in {"ORIGINAL_READY", "REPAIR_READY"}:
                production_ledger.cmd_review(SimpleNamespace(
                    episode_dir=str(ep), frame=key, decision="pass", notes=notes[:500]))
                status = str(_ledger_frame(ep, key).get("status") or "")
            if status == "PASSED":
                production_ledger.cmd_promote(SimpleNamespace(episode_dir=str(ep), frame=key))
                production_ledger.cmd_lock(SimpleNamespace(
                    episode_dir=str(ep), frame=key,
                    reason=f"final semantic critic attempt {attempt} PASS"))
            elif status != "LOCKED":
                raise RuntimeError(f"frame {key} cannot close PASS from status={status}")
        else:
            failures.append(key)
            if status in {"ORIGINAL_READY", "REPAIR_READY"}:
                production_ledger.cmd_review(SimpleNamespace(
                    episode_dir=str(ep), frame=key, decision="repair", notes=notes[:500]))
                status = str(_ledger_frame(ep, key).get("status") or "")
            if status == "CONTENT_FAILED":
                production_ledger.cmd_authorize_repair(SimpleNamespace(
                    episode_dir=str(ep), frame=key,
                    note=notes[:500], delegated_auto=True))
            elif status == "LOCKED":
                production_ledger.cmd_authorize_repair(SimpleNamespace(
                    episode_dir=str(ep), frame=key,
                    note=notes[:500], delegated_auto=True))
            elif status == "PASSED":
                raise RuntimeError(f"frame {key} final critic failed a pre-lock PASSED candidate; delegated PASSED reopen is not implemented")

    evidence = {
        "schema_version": 1,
        "attempt": attempt,
        "review_scope": "CANDIDATE_FULL_FRAME_SET",
        "critic_provenance": provenance,
        "reviewed_assets": [{"frame": x["frame"], "path": x["path_rel"], "sha256": x["sha256"]} for x in reviewed],
        "critic_result": data,
        "failed_frames": failures,
        "recorded_at": now(),
    }
    write_json(ep / "meta" / f"frame-semantic-candidate-attempt-{attempt}.json", evidence)
    if failures:
        print("FRAME SEMANTIC REVIEW FAIL: repair required frames=" + ",".join(failures))
        return 2

    approved = frame_records(ep, require_files=True)
    before_sha = {row["frame"]: row["sha256"] for row in reviewed}
    after_sha = {row["frame"]: row["sha256"] for row in approved}
    if before_sha != after_sha:
        raise RuntimeError("candidate -> approved promotion changed reviewed pixels")
    binding_errors = phase4_binding_errors(ep, approved)
    if binding_errors:
        raise RuntimeError("approved Frame Contract binding failed: " + "; ".join(binding_errors))
    approved_sources = review_source_bindings(ep, approved)
    provenance = dict(provenance)
    provenance["review_scope"] = "FULL_FRAME_SET"
    provenance["reviewed_candidate_assets"] = evidence["reviewed_assets"]
    return _persist_candidate(
        ep,
        data=data,
        current=approved,
        contexts=contexts,
        phashes=perceptual_rows(approved),
        provenance=provenance,
        frozen_sources=approved_sources,
    )


def apply_pending_candidate(ep: Path, *, attempt: int) -> int:
    """Resume a critic whose parent process vanished after the model wrote JSON."""
    request_path = pending_request_path(ep, attempt)
    candidate = ep / CANDIDATE_REL
    log = ep / "meta" / f"frame-semantic-critic-attempt-{attempt}.jsonl"
    if not request_path.is_file():
        raise RuntimeError(f"pending semantic request missing: {request_path}")
    if not candidate.is_file():
        raise RuntimeError(f"semantic candidate missing: {candidate}")
    if not log.is_file():
        raise RuntimeError(f"semantic critic log missing: {log}")
    pending = read_json(request_path)
    current = reviewable_frame_records(ep, require_files=True)
    expected_assets = pending.get("assets")
    actual_assets = [{"frame": x["frame"], "path": x["path_rel"], "sha256": x["sha256"]} for x in current]
    if expected_assets != actual_assets:
        raise RuntimeError("pending semantic request asset set drifted; refuse orphan recovery")
    if pending.get("contexts") != context_hashes(ep):
        raise RuntimeError("pending semantic request Story/Storyboard/visual context drifted")
    binding_errors = reviewable_phase4_binding_errors(ep, current)
    if binding_errors:
        raise RuntimeError("pending semantic request Frame Contract drifted: " + "; ".join(binding_errors))
    data = read_json(candidate)
    log_rel = log.relative_to(ROOT).as_posix() if log.stat().st_size > 0 else None
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, log=log_rel
    )
    provenance["review_scope"] = "FULL_FRAME_SET"
    provenance["recovered_after_parent_timeout"] = True
    provenance["candidate_sha256"] = sha256_file(candidate)
    if log.stat().st_size <= 0:
        provenance["critic_stdout_log_empty_after_parent_timeout"] = True
    return _apply_candidate_gate(
        ep,
        data=data,
        reviewed=current,
        contexts=context_hashes(ep),
        provenance=provenance,
        attempt=attempt,
    )


def validate_bound_review(data: dict, *, frame: dict, contexts: dict, version: str, metadata_only: bool, phase3_contexts: dict | None = None, directing_v3: bool = False, ep: Path | None = None) -> list[str]:
    errors: list[str] = []
    key = frame["frame"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"frame {key} schema_version must be {SCHEMA_VERSION}")
    if data.get("story_os_version") != version:
        errors.append(f"frame {key} story_os_version mismatch")
    if str(data.get("frame") or "").zfill(2) != key:
        errors.append(f"frame review number mismatch for {key}")
    if str(data.get("asset_sha256") or "").lower() != frame["sha256"].lower():
        errors.append(f"frame {key} asset_sha256 does not bind current approved asset")
    if str(data.get("asset_path") or "") != frame["path_rel"]:
        errors.append(f"frame {key} asset_path mismatch")
    for field, expected in contexts.items():
        if str(data.get(field) or "").lower() != str(expected).lower():
            errors.append(f"frame {key} {field} mismatch")
    for field, expected in (phase3_contexts or {}).items():
        if str(data.get(field) or "").lower() != str(expected).lower():
            errors.append(f"frame {key} {field} mismatch")
    expected_binding = source_binding(ep, frame["frame"]) if ep is not None else None
    if expected_binding and data.get("source_binding") != expected_binding:
        errors.append(f"frame {key} source_binding mismatch")
    provenance = data.get("critic_provenance") or {}
    for error in runtime_provenance.validate_critic_provenance(provenance):
        errors.append(f"frame {key} {error}")
    if provenance.get("review_scope") not in {"FULL_FRAME_SET", "INCREMENTAL_CONTEXT_SET"}:
        errors.append(f"frame {key} critic review_scope must be FULL_FRAME_SET or INCREMENTAL_CONTEXT_SET")
    attempt = provenance.get("attempt")
    if attempt not in {1, 2} and not (attempt == 3 and provenance.get("direct_user_exception_review") is True):
        errors.append(f"frame {key} critic attempt must be 1/2, or 3 for a direct-user-exception re-review")
    checks = data.get("checks") or {}
    for check in checks_for_version(version, directing_v3):
        if checks.get(check) is not True:
            errors.append(f"frame {key} checks.{check} must be true")
    codes = data.get("issue_codes")
    if not isinstance(codes, list):
        errors.append(f"frame {key} issue_codes must be list")
    elif codes:
        errors.append(f"frame {key} issue_codes not empty: {codes}")
    if data.get("decision") != "pass":
        errors.append(f"frame {key} decision must be pass")
    if not metadata_only:
        path = frame["path"]
        if not path.is_file():
            errors.append(f"frame {key} approved asset missing")
        else:
            actual = sha256_file(path)
            if actual.lower() != frame["sha256"].lower():
                errors.append(f"frame {key} actual asset SHA drift")
    return errors


def verify_episode(ep: Path, *, metadata_only: bool = False, write_audit: bool = False) -> list[str]:
    if not review_required(ep):
        return []
    errors: list[str] = []
    try:
        frames = frame_records(ep, require_files=not metadata_only)
        contexts = context_hashes(ep)
        errors.extend(phase4_binding_errors(ep, frames))
    except Exception as exc:
        return [str(exc)]

    summary_path = ep / SUMMARY_REL
    if not summary_path.is_file():
        errors.append("meta/frame-semantic-review.json missing")
        summary = None
    else:
        try:
            summary = read_json(summary_path)
        except Exception as exc:
            errors.append(str(exc))
            summary = None

    expected_version = episode_contract_version(ep)
    if summary is not None:
        if summary.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"frame semantic summary schema_version must be {SCHEMA_VERSION}")
        if summary.get("story_os_version") != expected_version:
            errors.append("frame semantic summary story_os_version mismatch")
        for field, expected in contexts.items():
            if str(summary.get(field) or "").lower() != str(expected).lower():
                errors.append(f"frame semantic summary {field} mismatch")
        provenance = summary.get("critic_provenance") or {}
        for error in runtime_provenance.validate_critic_provenance(provenance):
            errors.append("frame semantic summary critic provenance invalid: " + error)
        if provenance.get("review_scope") not in {"FULL_FRAME_SET", "BASELINE_PLUS_PATCHES"}:
            errors.append("frame semantic summary must prove FULL_FRAME_SET or BASELINE_PLUS_PATCHES review")
        bound = summary.get("frames")
        expected_bound = [{"frame": row["frame"], "asset_sha256": row["sha256"]} for row in frames]
        if bound != expected_bound:
            errors.append("frame semantic summary asset set does not match current approved frame set")
        if (summary.get("summary") or {}).get("passed") is not True:
            errors.append("frame semantic summary is not PASS")
        if summary.get("issue_codes") not in ([], None):
            errors.append(f"frame semantic summary issue_codes not empty: {summary.get('issue_codes')}")

    directing_v3 = directing_v3_required(ep)
    for frame in frames:
        path = ep / REVIEW_DIR / f"{frame['frame']}.json"
        if not path.is_file():
            errors.append(f"missing frame semantic review: {path.relative_to(ep)}")
            continue
        try:
            data = read_json(path)
            errors.extend(validate_bound_review(data, frame=frame, contexts=contexts, version=expected_version, metadata_only=metadata_only, phase3_contexts=phase3_context_hashes(ep, frame["frame"]), directing_v3=directing_v3, ep=ep))
        except Exception as exc:
            errors.append(f"frame {frame['frame']} review source validation failed: {exc}")

    phashes: list[dict] = []
    duplicates: list[dict] = []
    if not metadata_only and not errors:
        try:
            phashes = perceptual_rows(frames)
            duplicates = duplicate_pairs(phashes)
            if duplicates:
                for pair in duplicates:
                    errors.append(
                        "near-duplicate actual frames forbidden: "
                        + "/".join(pair["frames"])
                        + f" dhash={pair['dhash_distance']} ahash={pair['ahash_distance']}"
                    )
        except Exception as exc:
            errors.append(f"perceptual duplicate audit failed: {exc}")

    if write_audit:
        audit = {
            "schema_version": 1,
            "story_os_version": expected_version,
            "checked_at": now(),
            "metadata_only": metadata_only,
            "frame_count": len(frames),
            "perceptual_hashes": phashes,
            "near_duplicate_pairs": duplicates,
            "errors": errors,
            "summary": {"passed": not errors},
        }
        # Keep the audit reproducible: snapshot verification may re-run this
        # audit repeatedly, so do not rewrite (and re-hash) the evidence file
        # when only the wall-clock checked_at would change.
        audit_path = ep / AUDIT_REL
        changed = True
        if audit_path.is_file():
            try:
                old = read_json(audit_path)
                old.pop("checked_at", None)
                fresh = dict(audit)
                fresh.pop("checked_at", None)
                changed = old != fresh
            except Exception:
                changed = True
        if changed:
            write_json(audit_path, audit)
    return errors


resolve_codex = critic_runner.resolve_codex
command_prefix = critic_runner.prefix


def critic_prompt(ep: Path, frames: list[dict], candidate: Path, attempt: int) -> str:
    rel_ep = ep.relative_to(ROOT).as_posix()
    story, storyboard = episode_files(ep)
    rel_story = story.relative_to(ROOT).as_posix()
    rel_storyboard = storyboard.relative_to(ROOT).as_posix()
    rel_gates = (ep / "meta/story-gates.json").relative_to(ROOT).as_posix()
    rel_out = candidate.relative_to(ROOT).as_posix()
    mapping = "\n".join(f"- attachment/frame {row['frame']}: {row['path_rel']}" for row in frames)
    version = episode_contract_version(ep)
    directing_v3 = directing_v3_required(ep)
    # STORY_OS_V221_PROMPT_ALIGN: the Required-shape sample must list exactly the
    # checks enforced by validate_* for this episode version, otherwise every
    # critic attempt fails with "checks.X must be true" for keys never requested.
    required_checks = checks_for_version(version, directing_v3)
    checks_block = ",\n".join(f'        "{name}": true' for name in required_checks)
    return f"""You are an adversarial Production Frame Semantic Critic in a FRESH isolated session.
Do NOT generate or edit images. Do NOT rewrite the story. Do NOT trust previous PASS labels.
You are reviewing the COMPLETE final approved frame set for exactly {rel_ep}.

Read these locked sources before judging:
- {rel_story}
- {rel_storyboard}
- {rel_gates}
- standards/制作规范_正式版.md
- standards/生产帧语义强制规范_V1.0.md
- standards/Resolved_Frame_Contract规范_V1.0.md
- standards/Fast_Frame_Scout_与_Final_Candidate_Snapshot规范_V1.0.md
Fast Scout evidence is triage only. Do NOT trust PASS_FAST as a final pass; independently judge every supplied actual frame.
Resolved Frame Contracts: {rel_ep}/meta/runtime/contracts/frames/NN.json. The frame review must honor the SAME contract SHA used by the generation attempt.

Attached images are in numeric order and map as follows:
{mapping}

This is critic attempt {attempt}. Judge the ACTUAL pixels against Story Lock + storyboard + authenticity/continuity anchors.
Episode contract version: {episode_contract_version(ep)}. V2.2-only Visual Narrative checks and issue codes apply ONLY when version >= 2.2.0. Earlier episodes must not fail on V2.2-only criteria.
The visual-profile critic is a different job. A frame can look perfectly M00 and STILL FAIL here if it depicts the wrong person, wrong wardrobe, wrong timeline, illegal camera viewpoint, wrong prop, unreadable anomaly, or merely lets the caption claim evidence that the pixels do not show.

Hard rules for EVERY frame:
1. scene_storyboard_fidelity: the actual place/action/composition must be the storyboarded scene, not a generic substitute.
2. story_beat_fidelity: the image must visibly carry the intended narrative beat. Do not let prose rescue a missing event.
3. key_prop_fidelity: locked prop structure, material, scale, count and state must match. A generic green beer bottle cannot stand in for a locked thick micro-city glass vessel if the story depends on the city being visibly inside it.
4. character_identity + wardrobe_continuity: character age/sex/identity/garment anchors must not drift. If a frame suddenly shows another protagonist, FAIL.
5. pov_photographer_legality: obey the authenticity card. If the first-person photographer is fully visible or both hands are occupied while no legal second capture source exists, FAIL. Unexplained third-person coverage is a hard failure.
6. spatial_continuity + temporal_continuity: location relationships and timeline must agree with neighboring frames. A father who already left for hospital cannot silently reappear in the factory.
7. anomaly_readability: the abnormal fact the frame is supposed to prove must be visually legible. If the caption says a river tilted, a red mark aligned with a chimney, or old photos all contain one white arc, those relationships must actually be readable in pixels.
8. caption_image_support: planned text may add context but must not invent the core visual evidence.
9. actual_information_gain: compare ACTUAL adjacent images, not just storyboard descriptions.
10. environment_physics_fidelity: V2.1 weather/environment must obey the resolved physical conditions; weather is not a blanket filter.
11. anomaly_escalation_fidelity: impact 3-4 / anomaly_amplified / climax_impact must visibly exceed escalation_from; caption-only escalation fails.
12. scale_reference_fidelity: high-impact frames must visibly use the locked real-world scale reference so abnormal size is readable.
13. camera_authorship_physical: photographer/camera source must exist physically; ghost/floating/omniscient coverage is a hard failure.
14. moment_capture_credibility: frame must feel captured during an action with a plausible save reason, not posed after the event.
15. narrative_evidence_gain: each frame after the opening must add real story/evidence information; another angle of the same unchanged fact is NARRATIVE_REDUNDANCY.
16. shot_grammar_diversity: first-person is diegetic camera logic, not a repeated hand+phone+distant-anomaly template.
17. camera_defect_physics: blur/noise/reflection/underexposure must have a plausible physical cause.
18. screen_content_physics: phone/map/dashboard/time/camera UI must be internally, perspectivally and narratively coherent.
19. visual_memory_continuity: character/wardrobe/vehicle/props/route/weather/light/anomaly evidence must persist unless explicitly changed.
20. For shot-progression schema_version >=3 only: shot_scale_fidelity must match the locked shot_scale; scene_position_uniqueness_fidelity must not collapse different planned positions into visibly repeated camera setups; cinematic_structure_translation_fidelity must use the locked structural technique without becoming an exact film-still recreation; practical_lighting_design_fidelity must honor the declared real light source/contrast/suspense function; anomaly_concealment_fidelity must visibly use the locked mirror/water/glass/fog/light-shadow/screen/occlusion carrier when declared.
21. PASS only if all required checks are true, issue_codes is empty and decision=pass.

Use issue codes only from this set:
{', '.join(sorted(ISSUE_CODES))}

Write ONLY valid JSON to {rel_out}. Do not modify any other repository file.
Required shape:
{{
  "frames": [
    {{
      "frame": "01",
      "checks": {{
{checks_block}
      }},
      "issue_codes": [],
      "notes": "specific pixel-level evidence",
      "decision": "pass"
    }}
  ],
  "issue_codes": [],
  "summary": {{"passed": true, "notes": "overall continuity/payoff judgment"}}
}}
Return one row for EVERY attached frame. If any hard check fails, mark it false, add the specific issue code, set that frame decision=fail and summary.passed=false.
"""


def _rebind_incremental_captions(ep: Path) -> None:
    """Keep the V2.0.3.4 caption binding fresh for frame semantic evidence.

    Caption binding is a release/delivery concern. A verified formal review may
    exist before ``release-manifest.json`` is created; in that state the reuse
    path must stay metadata-only and must not rescan frame assets.
    """
    if not (ep / "meta/release-manifest.json").is_file():
        return
    try:
        import incremental_frame_review as incremental

        if not incremental.review_required(ep):
            return
        result = incremental.rebind_captions(ep)
        if not result.get("rebound"):
            print(f"WARN: incremental caption rebind skipped ({result.get('reason')})")
        elif result.get("errors"):
            for error in result["errors"]:
                print("WARN: incremental caption rebind verify:", error)
    except Exception as exc:  # pragma: no cover - defensive, never fails the review
        print(f"WARN: incremental caption rebind failed: {exc}")


def _persist_candidate(
    ep: Path,
    *,
    data: dict,
    current: list[dict],
    contexts: dict,
    phashes: list[dict],
    provenance: dict,
    frozen_sources: dict,
) -> int:
    if review_source_bindings(ep, current) != frozen_sources:
        raise RuntimeError("frame semantic review sources drifted during review; candidate cannot be rebound")
    version = episode_contract_version(ep)
    directing_v3 = directing_v3_required(ep)
    candidate_errors = validate_candidate_rows(data.get("frames"), current, version=version, directing_v3=directing_v3)
    global_codes = data.get("issue_codes")
    if not isinstance(global_codes, list):
        candidate_errors.append("global issue_codes must be list")
        global_codes = []
    elif global_codes:
        candidate_errors.append(f"global issue_codes must be empty for PASS: {global_codes}")
    if (data.get("summary") or {}).get("passed") is not True:
        candidate_errors.append("critic summary.passed must be true")

    rows_by_frame = {str(row.get("frame") or "").zfill(2): row for row in (data.get("frames") or []) if isinstance(row, dict)}
    review_dir = ep / REVIEW_DIR
    review_dir.mkdir(parents=True, exist_ok=True)
    for frame in current:
        source = rows_by_frame.get(frame["frame"], {})
        bound = {
            "schema_version": SCHEMA_VERSION,
            "story_os_version": version,
            "frame": frame["frame"],
            "asset_path": frame["path_rel"],
            "asset_sha256": frame["sha256"],
            **contexts,
            **frozen_sources["frames"][frame["frame"]],
            "critic_provenance": provenance,
            "checks": source.get("checks") or {},
            "issue_codes": source.get("issue_codes") if isinstance(source.get("issue_codes"), list) else ["FRAME_SCENE_MISMATCH"],
            "notes": source.get("notes") or "",
            "decision": source.get("decision") or "fail",
        }
        write_json(review_dir / f"{frame['frame']}.json", bound)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "story_os_version": version,
        **contexts,
        "critic_provenance": provenance,
        "frames": [{"frame": row["frame"], "asset_sha256": row["sha256"]} for row in current],
        "perceptual_hashes": phashes,
        "near_duplicate_pairs": [],
        "issue_codes": global_codes,
        "critic_summary": data.get("summary") or {},
        "summary": {"passed": not candidate_errors},
    }
    write_json(ep / SUMMARY_REL, summary)
    (ep / CANDIDATE_REL).unlink(missing_ok=True)
    _rebind_incremental_captions(ep)

    verify_errors = verify_episode(ep, metadata_only=False, write_audit=True)
    errors = candidate_errors + [x for x in verify_errors if x not in candidate_errors]
    if errors:
        print("FRAME SEMANTIC REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        return 2
    print("FRAME SEMANTIC REVIEW PASS")
    return 0


def finalize_product_review(ep: Path, *, attempt: int, runtime: str) -> int:
    frames = frame_records(ep, require_files=True)
    contexts = context_hashes(ep)
    frozen_sources = review_source_bindings(ep, frames)
    binding_errors = phase4_binding_errors(ep, frames)
    if binding_errors:
        for error in binding_errors:
            print("FAIL:", error)
        return 2
    phashes = perceptual_rows(frames)
    duplicates = duplicate_pairs(phashes)
    if duplicates:
        for pair in duplicates:
            print("FRAME SEMANTIC REVIEW FAIL: NEAR_DUPLICATE_ACTUAL_FRAMES", pair)
        return 2
    candidate = ep / CANDIDATE_REL
    data, provenance = product_review_adapter.finalize_candidate(
        ep,
        kind="frame-semantic",
        runtime=runtime,
        attempt=attempt,
        candidate_path=candidate,
        source_bindings=frozen_sources,
    )
    provenance["review_scope"] = "FULL_FRAME_SET"
    rc = _persist_candidate(
        ep,
        data=data,
        current=frames,
        contexts=contexts,
        phashes=phashes,
        provenance=provenance,
        frozen_sources=frozen_sources,
    )
    if rc == 0:
        product_review_adapter.mark_complete(ep, "frame-semantic", attempt=attempt, final_path=ep / SUMMARY_REL)
    return rc


def run_critic(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int | None = None) -> int:
    if timeout is None:
        timeout = runtime_timeout_policy.seconds("deep_semantic_review")
    if attempt not in {1, 2}:
        raise RuntimeError("attempt must be 1 or 2; only one automatic content-repair round is permitted")
    if (ep / SUMMARY_REL).is_file() and review_required(ep) and not verify_episode(ep):
        _rebind_incremental_captions(ep)
        print("FRAME SEMANTIC REVIEW REUSED: current assets, contracts and critic evidence verified")
        return 0
    candidate_gate = False
    try:
        frames = frame_records(ep, require_files=True)
    except ValueError:
        frames = reviewable_frame_records(ep, require_files=True)
        candidate_gate = True
    contexts = context_hashes(ep)
    binding_errors = reviewable_phase4_binding_errors(ep, frames) if candidate_gate else phase4_binding_errors(ep, frames)
    if binding_errors:
        print("FRAME SEMANTIC REVIEW FAIL: stale/missing generation Frame Contract")
        for error in binding_errors:
            print("FAIL:", error)
        return 2

    # Cheap deterministic failure before spending a critic call.
    phashes = perceptual_rows(frames)
    duplicates = duplicate_pairs(phashes)
    if duplicates:
        write_json(ep / AUDIT_REL, {
            "schema_version": 1,
            "story_os_version": story_os_version(),
            "checked_at": now(),
            "frame_count": len(frames),
            "perceptual_hashes": phashes,
            "near_duplicate_pairs": duplicates,
            "errors": ["NEAR_DUPLICATE_ACTUAL_FRAMES"],
            "summary": {"passed": False},
        })
        for pair in duplicates:
            print("FRAME SEMANTIC REVIEW FAIL: NEAR_DUPLICATE_ACTUAL_FRAMES", pair)
        return 2

    candidate = ep / CANDIDATE_REL
    frozen_sources = review_source_bindings(ep, frames)
    before = {row["frame"]: sha256_file(row["path"]) for row in frames}
    story, storyboard = episode_files(ep)
    stable_before = {
        "story": sha256_file(story),
        "storyboard": sha256_file(storyboard),
        "visual": sha256_json(stable_visual_contract(ep)),
    }

    active_runtime, _ = runtime_router.detect()
    if active_runtime in {"WORK", "WEB"} and not codex_raw:
        sources = [
            story,
            storyboard,
            ep / "meta/story-gates.json",
            ROOT / "standards/制作规范_正式版.md",
            ROOT / "standards/生产帧语义强制规范_V1.0.md",
            ROOT / "standards/Resolved_Frame_Contract规范_V1.0.md",
            ROOT / "standards/Fast_Frame_Scout_与_Final_Candidate_Snapshot规范_V1.0.md",
            *[row["path"] for row in frames],
        ]
        request = product_review_adapter.prepare(
            ep,
            kind="frame-semantic",
            runtime=active_runtime,
            attempt=attempt,
            prompt=critic_prompt(ep, frames, candidate, attempt),
            source_paths=sources,
            candidate_path=candidate,
            source_bindings=frozen_sources,
        )
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC

    candidate.unlink(missing_ok=True)
    write_json(pending_request_path(ep, attempt), _pending_request_payload(ep, frames, attempt))
    codex = resolve_codex(codex_raw)
    log = ep / "meta" / f"frame-semantic-critic-attempt-{attempt}.jsonl"
    completed = critic_runner.launch(
        critic_prompt(ep, frames, candidate, attempt),
        codex=codex,
        root=ROOT,
        timeout=timeout,
        sandbox="workspace-write",
        reasoning_effort_literal='model_reasoning_effort="high"',
        attachments=[row["path"] for row in frames],
        log_path=log,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"isolated frame semantic critic failed rc={completed.returncode}; log={log}")
    if not candidate.is_file():
        raise RuntimeError(f"frame semantic critic did not produce {candidate}")

    current = reviewable_frame_records(ep, require_files=True) if candidate_gate else frame_records(ep, require_files=True)
    if {row["frame"]: sha256_file(row["path"]) for row in current} != before:
        raise RuntimeError("frame semantic critic modified reviewed image assets")
    stable_after = {
        "story": sha256_file(story),
        "storyboard": sha256_file(storyboard),
        "visual": sha256_json(stable_visual_contract(ep)),
    }
    if stable_after != stable_before:
        raise RuntimeError("frame semantic critic modified Story Lock / storyboard / visual continuity context")

    data = read_json(candidate)
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, log=log.relative_to(ROOT).as_posix()
    )
    provenance["review_scope"] = "FULL_FRAME_SET"
    if candidate_gate:
        return _apply_candidate_gate(
            ep,
            data=data,
            reviewed=current,
            contexts=contexts,
            provenance=provenance,
            attempt=attempt,
        )
    return _persist_candidate(
        ep,
        data=data,
        current=current,
        contexts=contexts,
        phashes=phashes,
        provenance=provenance,
        frozen_sources=frozen_sources,
    )


def _parse_exception_frames(raw: str) -> list[str]:
    frames: list[str] = []
    for part in str(raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"invalid exception frame: {part!r}")
        key = f"{int(part):02d}"
        if key not in frames:
            frames.append(key)
    if not frames:
        raise ValueError("at least one exception frame is required")
    if len(frames) > 5:
        raise ValueError("exception semantic review is limited to at most 5 target frames")
    return sorted(frames)


def _exception_context_keys(all_keys: list[str], targets: list[str]) -> list[str]:
    nums = sorted(int(x) for x in all_keys)
    allowed = set(nums)
    total = max(nums) if nums else 0
    selected: set[int] = set()
    for raw in targets:
        n = int(raw)
        radius = 2 if n >= max(1, total - 2) else 1
        for value in range(n - radius, n + radius + 1):
            if value in allowed:
                selected.add(value)
    return [f"{x:02d}" for x in sorted(selected)]


def _exception_review_records(ep: Path, targets: list[str], *, require_files: bool = True) -> tuple[list[dict], list[str]]:
    ledger = read_json(ep / "meta/production-ledger.json")
    frames = ledger.get("frames") or {}
    all_keys = sorted(k for k in frames if str(k).isdigit())
    missing = [key for key in targets if key not in frames]
    if missing:
        raise ValueError(f"unknown exception review frames: {missing}")
    context_keys = _exception_context_keys(all_keys, targets)
    rows: list[dict] = []
    for key in context_keys:
        frame = frames.get(key) or {}
        status = str(frame.get("status") or "")
        is_target = key in targets
        if is_target:
            if status != "REPAIR_READY":
                raise ValueError(f"exception review target {key} requires REPAIR_READY, got {status}")
            if int(frame.get("content_repairs_used") or 0) != 1 or int(frame.get("user_exception_repairs_used") or 0) != 1:
                raise ValueError(f"exception review target {key} requires one ordinary and one direct-user exception repair")
            asset = frame.get("current_candidate")
            source_kind = "candidate"
        else:
            if status not in production_ledger.ACCEPTED_LEDGER_STATES:
                raise ValueError(f"exception review context {key} must already be approved/locked, got {status}")
            asset = frame.get("approved_asset")
            source_kind = "approved"
        if not isinstance(asset, dict):
            raise ValueError(f"exception review {source_kind} missing for frame {key}")
        raw_path = asset.get("path") or asset.get("asset_path")
        sha = str(asset.get("sha256") or "").lower()
        if len(sha) != 64:
            raise ValueError(f"exception review frame {key} sha256 invalid")
        path = repo_path(raw_path, f"exception review frame {key} {source_kind}", require_file=require_files)
        if require_files and sha256_file(path).lower() != sha:
            raise ValueError(f"exception review frame {key} asset SHA drift")
        rows.append({
            "frame": key,
            "path": path,
            "path_rel": repo_rel(path),
            "sha256": sha,
            "source_kind": source_kind,
            "ledger_status": status,
            "exception_target": is_target,
        })
    return rows, context_keys


def _exception_review_prompt(ep: Path, rows: list[dict], targets: list[str], candidate: Path) -> str:
    story, storyboard = episode_files(ep)
    version = episode_contract_version(ep)
    directing_v3 = directing_v3_required(ep)
    checks = checks_for_version(version, directing_v3)
    checks_block = ",\n".join(f'        "{name}": true' for name in checks)
    mapping = "\n".join(
        f"- {'TARGET' if row['exception_target'] else 'CONTEXT'} frame {row['frame']}: {row['path_rel']}"
        for row in rows
    )
    return f"""You are a FRESH isolated final Production Frame Semantic Critic.
This is a DIRECT-USER-EXCEPTION re-review. Do NOT generate or edit images and do NOT trust earlier PASS/FAIL labels.
Only the TARGET frames may change Production Ledger state. CONTEXT frames are already locked and are supplied only to judge continuity.
Targets: {', '.join(targets)}.

Read these locked authorities before judging:
- {story.relative_to(ROOT).as_posix()}
- {storyboard.relative_to(ROOT).as_posix()}
- {(ep / 'meta/story-gates.json').relative_to(ROOT).as_posix()}
- standards/制作规范_正式版.md
- standards/生产帧语义强制规范_V1.0.md
- standards/Resolved_Frame_Contract规范_V1.0.md
Resolved Frame Contracts live at {(ep / 'meta/runtime/contracts/frames').relative_to(ROOT).as_posix()}/NN.json.

Attached mapping:
{mapping}

Judge ACTUAL pixels against Story Lock, storyboard, Frame Contract, camera-authorship physics, world identity, continuity and anomaly readability.
PASS only when every required check is true and issue_codes is empty. Context rows must also remain valid; if a context row is inconsistent with a target, fail the relevant row rather than hiding the conflict.
Use issue codes only from: {', '.join(sorted(ISSUE_CODES))}

Write ONLY valid JSON to {candidate.relative_to(ROOT).as_posix()} with exactly one row for every attached frame:
{{
  "frames": [{{
    "frame": "01",
    "checks": {{
{checks_block}
    }},
    "issue_codes": [],
    "notes": "specific pixel-level evidence",
    "decision": "pass"
  }}],
  "issue_codes": [],
  "summary": {{"passed": true, "notes": "exception patch judgment"}}
}}
If any supplied row fails, set that row decision=fail and summary.passed=false.
"""


def _exception_pending_payload(ep: Path, rows: list[dict], targets: list[str]) -> dict:
    return {
        "schema_version": 1,
        "attempt": 3,
        "recorded_at": now(),
        "targets": targets,
        "contexts": context_hashes(ep),
        "assets": [{"frame": r["frame"], "path": r["path_rel"], "sha256": r["sha256"]} for r in rows],
    }


def _apply_exception_review(ep: Path, *, data: dict, rows: list[dict], targets: list[str], provenance: dict) -> int:
    version = episode_contract_version(ep)
    directing_v3 = directing_v3_required(ep)
    errors = validate_candidate_gate_rows(data.get("frames"), rows, version, directing_v3)
    codes = data.get("issue_codes")
    if not isinstance(codes, list):
        errors.append("global issue_codes must be list")
    elif any(code not in ISSUE_CODES for code in codes):
        errors.append(f"global issue_codes contain unknown values: {codes}")
    if errors:
        print("EXCEPTION FRAME SEMANTIC REVIEW INVALID")
        for error in errors:
            print("FAIL:", error)
        return 3

    by_key = {str(row.get("frame") or "").zfill(2): row for row in data.get("frames") or []}
    context_failures = [row["frame"] for row in rows if not row["exception_target"] and by_key[row["frame"]].get("decision") != "pass"]
    evidence = {
        "schema_version": 1,
        "attempt": 3,
        "review_scope": "DIRECT_USER_EXCEPTION_PATCH",
        "targets": targets,
        "critic_provenance": provenance,
        "reviewed_assets": [{"frame": r["frame"], "path": r["path_rel"], "sha256": r["sha256"]} for r in rows],
        "critic_result": data,
        "context_failures": context_failures,
        "recorded_at": now(),
    }
    write_json(ep / "meta/frame-semantic-exception-attempt-3.json", evidence)
    if context_failures:
        print("EXCEPTION FRAME SEMANTIC REVIEW FAIL: locked context failed=" + ",".join(context_failures))
        return 2

    contexts = context_hashes(ep)
    frozen = review_source_bindings(ep, rows)
    failures: list[str] = []
    for source in rows:
        key = source["frame"]
        if key not in targets:
            continue
        result = by_key[key]
        status = str(_ledger_frame(ep, key).get("status") or "")
        if status != "REPAIR_READY":
            raise RuntimeError(f"exception target {key} drifted from REPAIR_READY to {status}")
        note = "Direct-user exception semantic critic attempt 3: " + str(result.get("notes") or result.get("issue_codes") or "")
        if result.get("decision") == "pass":
            production_ledger.cmd_review(SimpleNamespace(
                episode_dir=str(ep), frame=key, decision="pass", notes=note[:500]))
            production_ledger.cmd_promote(SimpleNamespace(episode_dir=str(ep), frame=key))
            production_ledger.cmd_lock(SimpleNamespace(
                episode_dir=str(ep), frame=key, reason="direct-user exception semantic critic attempt 3 PASS"))
            locked = _ledger_frame(ep, key)
            approved = locked.get("approved_asset") or {}
            if str(approved.get("sha256") or "").lower() != source["sha256"].lower():
                raise RuntimeError(f"exception target {key} promotion changed reviewed pixels")
            bound = {
                "schema_version": SCHEMA_VERSION,
                "story_os_version": version,
                "frame": key,
                "asset_path": str(approved.get("path") or ""),
                "asset_sha256": str(approved.get("sha256") or "").lower(),
                **contexts,
                **phase3_context_hashes(ep, key),
                "source_binding": source_binding(ep, key),
                "critic_provenance": provenance,
                "checks": result.get("checks") or {},
                "issue_codes": result.get("issue_codes") or [],
                "notes": result.get("notes") or "",
                "decision": "pass",
            }
            review_dir = ep / REVIEW_DIR
            review_dir.mkdir(parents=True, exist_ok=True)
            write_json(review_dir / f"{key}.json", bound)
        else:
            production_ledger.cmd_review(SimpleNamespace(
                episode_dir=str(ep), frame=key, decision="repair", notes=note[:500]))
            failures.append(key)

    evidence["failed_targets"] = failures
    evidence["completed_at"] = now()
    write_json(ep / "meta/frame-semantic-exception-attempt-3.json", evidence)
    if failures:
        print("EXCEPTION FRAME SEMANTIC REVIEW FAIL: targets=" + ",".join(failures))
        return 2
    print("EXCEPTION FRAME SEMANTIC REVIEW PASS: targets=" + ",".join(targets))
    return 0


def run_exception_critic(ep: Path, *, targets: list[str], codex_raw: str | None, timeout: int | None = None) -> int:
    if timeout is None:
        timeout = runtime_timeout_policy.seconds("deep_semantic_review")
    rows, _ = _exception_review_records(ep, targets, require_files=True)
    binding_errors = reviewable_phase4_binding_errors(ep, rows)
    if binding_errors:
        for error in binding_errors:
            print("FAIL:", error)
        return 2
    candidate = ep / EXCEPTION_CANDIDATE_REL
    candidate.unlink(missing_ok=True)
    write_json(ep / EXCEPTION_PENDING_REL, _exception_pending_payload(ep, rows, targets))
    log = ep / "meta/frame-semantic-exception-critic-attempt-3.jsonl"
    completed = critic_runner.launch(
        _exception_review_prompt(ep, rows, targets, candidate),
        codex=resolve_codex(codex_raw),
        root=ROOT,
        timeout=timeout,
        sandbox="workspace-write",
        reasoning_effort_literal='model_reasoning_effort="high"',
        attachments=[row["path"] for row in rows],
        log_path=log,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"isolated exception semantic critic failed rc={completed.returncode}; log={log}")
    if not candidate.is_file():
        raise RuntimeError(f"exception semantic critic did not produce {candidate}")
    current, _ = _exception_review_records(ep, targets, require_files=True)
    expected = [{"frame": r["frame"], "path": r["path_rel"], "sha256": r["sha256"]} for r in rows]
    actual = [{"frame": r["frame"], "path": r["path_rel"], "sha256": r["sha256"]} for r in current]
    if expected != actual:
        raise RuntimeError("exception semantic review assets drifted during review")
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=3, log=log.relative_to(ROOT).as_posix(), allow_user_exception_attempt=True)
    provenance["review_scope"] = "INCREMENTAL_CONTEXT_SET"
    provenance["direct_user_exception_frames"] = targets
    return _apply_exception_review(ep, data=read_json(candidate), rows=current, targets=targets, provenance=provenance)


def apply_exception_candidate(ep: Path) -> int:
    pending_path = ep / EXCEPTION_PENDING_REL
    candidate = ep / EXCEPTION_CANDIDATE_REL
    log = ep / "meta/frame-semantic-exception-critic-attempt-3.jsonl"
    if not pending_path.is_file() or not candidate.is_file():
        raise RuntimeError("exception semantic pending/candidate evidence missing")
    pending = read_json(pending_path)
    targets = [str(x).zfill(2) for x in (pending.get("targets") or [])]
    rows, _ = _exception_review_records(ep, targets, require_files=True)
    assets = [{"frame": r["frame"], "path": r["path_rel"], "sha256": r["sha256"]} for r in rows]
    if pending.get("assets") != assets:
        raise RuntimeError("exception semantic pending asset set drifted")
    if pending.get("contexts") != context_hashes(ep):
        raise RuntimeError("exception semantic Story/Storyboard/visual context drifted")
    binding_errors = reviewable_phase4_binding_errors(ep, rows)
    if binding_errors:
        raise RuntimeError("exception semantic Frame Contract drifted: " + "; ".join(binding_errors))
    log_rel = log.relative_to(ROOT).as_posix() if log.is_file() and log.stat().st_size > 0 else None
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=3, log=log_rel, allow_user_exception_attempt=True)
    provenance["review_scope"] = "INCREMENTAL_CONTEXT_SET"
    provenance["direct_user_exception_frames"] = targets
    provenance["recovered_after_parent_timeout"] = True
    provenance["candidate_sha256"] = sha256_file(candidate)
    if not log_rel:
        provenance["critic_stdout_log_empty_after_parent_timeout"] = True
    return _apply_exception_review(ep, data=read_json(candidate), rows=rows, targets=targets, provenance=provenance)


def self_test() -> None:
    h = "a" * 64
    contexts = {
        "story_sha256": "b" * 64,
        "storyboard_sha256": "c" * 64,
        "visual_contract_sha256": "d" * 64,
    }
    frame = {"frame": "01", "path_rel": "episodes/x/production/approved/01.png", "sha256": h, "path": Path("/tmp/no-file")}
    payload = {
        "schema_version": SCHEMA_VERSION,
        "story_os_version": story_os_version(),
        "frame": "01",
        "asset_path": frame["path_rel"],
        "asset_sha256": h,
        **contexts,
        "critic_provenance": {"runtime": "CODEX_ISOLATED", "isolated_session": True, "review_scope": "FULL_FRAME_SET", "attempt": 1},
        "checks": {key: True for key in checks_for_version(story_os_version())},
        "issue_codes": [],
        "decision": "pass",
        "source_binding": {},
    }
    assert validate_bound_review(payload, frame=frame, contexts=contexts, version=story_os_version(), metadata_only=True) == []
    payload["asset_sha256"] = "e" * 64
    assert any("asset_sha256" in x for x in validate_bound_review(payload, frame=frame, contexts=contexts, version=story_os_version(), metadata_only=True))
    candidate = [{"frame": "01", "checks": {key: True for key in checks_for_version(story_os_version())}, "issue_codes": [], "decision": "pass"}]
    assert validate_candidate_rows(candidate, [frame]) == []
    candidate[0]["checks"]["temporal_continuity"] = False
    assert validate_candidate_rows(candidate, [frame])
    assert hamming_hex("0" * 64, "0" * 64) == 0
    print("FRAME SEMANTIC REVIEW SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description="Story OS V2.0.3.3 actual-frame semantic fidelity critic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run-critic")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=None)
    p = sub.add_parser("apply-candidate")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p = sub.add_parser("exception-review")
    p.add_argument("episode_dir")
    p.add_argument("--frames", required=True, help="comma-separated direct-user-exception target frames")
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=None)
    p = sub.add_parser("apply-exception-candidate")
    p.add_argument("episode_dir")
    p = sub.add_parser("finalize-review")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--runtime", choices=["WORK", "WEB"], default="WORK")
    p = sub.add_parser("verify")
    p.add_argument("episode_dir")
    p.add_argument("--metadata-only", action="store_true")
    p = sub.add_parser("audit")
    p.add_argument("episode_dir")
    p = sub.add_parser("show")
    p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()

    if args.cmd == "self-test":
        self_test()
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    if args.cmd == "run-critic":
        try:
            return run_critic(ep, attempt=args.attempt, codex_raw=args.codex, timeout=args.timeout)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            print("FRAME SEMANTIC REVIEW ERROR:", exc)
            return 3
    if args.cmd == "apply-candidate":
        try:
            return apply_pending_candidate(ep, attempt=args.attempt)
        except (OSError, RuntimeError, ValueError) as exc:
            print("FRAME SEMANTIC RECOVERY ERROR:", exc)
            return 3
    if args.cmd == "exception-review":
        try:
            return run_exception_critic(
                ep, targets=_parse_exception_frames(args.frames), codex_raw=args.codex, timeout=args.timeout)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            print("EXCEPTION FRAME SEMANTIC REVIEW ERROR:", exc)
            return 3
    if args.cmd == "apply-exception-candidate":
        try:
            return apply_exception_candidate(ep)
        except (OSError, RuntimeError, ValueError) as exc:
            print("EXCEPTION FRAME SEMANTIC RECOVERY ERROR:", exc)
            return 3
    if args.cmd == "finalize-review":
        try:
            return finalize_product_review(ep, attempt=args.attempt, runtime=args.runtime)
        except (OSError, RuntimeError, ValueError) as exc:
            print("FRAME SEMANTIC REVIEW FINALIZE ERROR:", exc)
            return 3
    if args.cmd == "show":
        p = ep / SUMMARY_REL
        print(p.read_text(encoding="utf-8") if p.is_file() else "NO FRAME SEMANTIC REVIEW")
        return 0
    errors = verify_episode(ep, metadata_only=(args.cmd == "verify" and args.metadata_only), write_audit=(args.cmd == "audit"))
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("FRAME SEMANTIC REVIEW VERIFY PASS" if args.cmd == "verify" else "FRAME SEMANTIC AUDIT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
