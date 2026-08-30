#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image

from story_os_contract import story_os_version
import environment_contract as phase3_env
import frame_contract as phase4_contract
import fast_frame_scout as phase7_scout

ROOT = Path(__file__).resolve().parents[2]
REVIEW_DIR = Path("meta/frame-reviews")
SUMMARY_REL = Path("meta/frame-semantic-review.json")
CANDIDATE_REL = Path("meta/.frame-semantic-review.candidate.json")
AUDIT_REL = Path("meta/frame-semantic-audit.json")
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

V21_PHASE3_CHECKS = [
    "environment_physics_fidelity",
    "anomaly_escalation_fidelity",
    "scale_reference_fidelity",
]

def checks_for_version(version: str) -> list[str]:
    return CHECKS + (V21_PHASE3_CHECKS if version_tuple(version) >= (2, 1, 0) else [])

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
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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
        if frame.get("status") not in {"PASSED", "LOCKED"}:
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


def validate_candidate_rows(rows: object, expected_frames: list[dict], version: str = "2.0.3.6") -> list[str]:
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
        for check in checks_for_version(version):
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


def validate_bound_review(data: dict, *, frame: dict, contexts: dict, version: str, metadata_only: bool, phase3_contexts: dict | None = None) -> list[str]:
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
    provenance = data.get("critic_provenance") or {}
    if provenance.get("runtime") != "CODEX_ISOLATED":
        errors.append(f"frame {key} critic runtime must be CODEX_ISOLATED")
    if provenance.get("isolated_session") is not True:
        errors.append(f"frame {key} critic must be isolated")
    if provenance.get("review_scope") not in {"FULL_FRAME_SET", "INCREMENTAL_CONTEXT_SET"}:
        errors.append(f"frame {key} critic review_scope must be FULL_FRAME_SET or INCREMENTAL_CONTEXT_SET")
    if provenance.get("attempt") not in {1, 2}:
        errors.append(f"frame {key} critic attempt must be 1 or 2")
    checks = data.get("checks") or {}
    for check in checks_for_version(version):
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
        if provenance.get("runtime") != "CODEX_ISOLATED" or provenance.get("isolated_session") is not True:
            errors.append("frame semantic summary critic provenance invalid")
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

    for frame in frames:
        path = ep / REVIEW_DIR / f"{frame['frame']}.json"
        if not path.is_file():
            errors.append(f"missing frame semantic review: {path.relative_to(ep)}")
            continue
        try:
            data = read_json(path)
        except Exception as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_bound_review(data, frame=frame, contexts=contexts, version=expected_version, metadata_only=metadata_only, phase3_contexts=phase3_context_hashes(ep, frame["frame"])))

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
        write_json(ep / AUDIT_REL, {
            "schema_version": 1,
            "story_os_version": expected_version,
            "checked_at": now(),
            "metadata_only": metadata_only,
            "frame_count": len(frames),
            "perceptual_hashes": phashes,
            "near_duplicate_pairs": duplicates,
            "errors": errors,
            "summary": {"passed": not errors},
        })
    return errors


def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"Codex CLI not found: {path}")
    return path


def command_prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]


def critic_prompt(ep: Path, frames: list[dict], candidate: Path, attempt: int) -> str:
    rel_ep = ep.relative_to(ROOT).as_posix()
    story, storyboard = episode_files(ep)
    rel_story = story.relative_to(ROOT).as_posix()
    rel_storyboard = storyboard.relative_to(ROOT).as_posix()
    rel_gates = (ep / "meta/story-gates.json").relative_to(ROOT).as_posix()
    rel_out = candidate.relative_to(ROOT).as_posix()
    mapping = "\n".join(f"- attachment/frame {row['frame']}: {row['path_rel']}" for row in frames)
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
13. PASS only if all required checks are true, issue_codes is empty and decision=pass.

Use issue codes only from this set:
{', '.join(sorted(ISSUE_CODES))}

Write ONLY valid JSON to {rel_out}. Do not modify any other repository file.
Required shape:
{{
  "frames": [
    {{
      "frame": "01",
      "checks": {{
        "scene_storyboard_fidelity": true,
        "story_beat_fidelity": true,
        "key_prop_fidelity": true,
        "character_identity": true,
        "wardrobe_continuity": true,
        "pov_photographer_legality": true,
        "spatial_continuity": true,
        "temporal_continuity": true,
        "anomaly_readability": true,
        "caption_image_support": true,
        "actual_information_gain": true,
        "environment_physics_fidelity": true,
        "anomaly_escalation_fidelity": true,
        "scale_reference_fidelity": true
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


def run_critic(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int) -> int:
    if attempt not in {1, 2}:
        raise RuntimeError("attempt must be 1 or 2; only one automatic content-repair round is permitted")
    frames = frame_records(ep, require_files=True)
    contexts = context_hashes(ep)
    binding_errors = phase4_binding_errors(ep, frames)
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
    candidate.unlink(missing_ok=True)
    before = {row["frame"]: sha256_file(row["path"]) for row in frames}
    story, storyboard = episode_files(ep)
    stable_before = {
        "story": sha256_file(story),
        "storyboard": sha256_file(storyboard),
        "visual": sha256_json(stable_visual_contract(ep)),
    }

    codex = resolve_codex(codex_raw)
    cmd = command_prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", "workspace-write", "-C", str(ROOT), "--json"
    ]
    for row in frames:
        cmd += ["-i", str(row["path"])]
    cmd += ["-"]
    log = ep / "meta" / f"frame-semantic-critic-attempt-{attempt}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(
            cmd,
            input=critic_prompt(ep, frames, candidate, attempt),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"isolated frame semantic critic failed rc={completed.returncode}; log={log}")
    if not candidate.is_file():
        raise RuntimeError(f"frame semantic critic did not produce {candidate}")

    current = frame_records(ep, require_files=True)
    if {row["frame"]: sha256_file(row["path"]) for row in current} != before:
        raise RuntimeError("frame semantic critic modified approved image assets")
    stable_after = {
        "story": sha256_file(story),
        "storyboard": sha256_file(storyboard),
        "visual": sha256_json(stable_visual_contract(ep)),
    }
    if stable_after != stable_before:
        raise RuntimeError("frame semantic critic modified Story Lock / storyboard / visual continuity context")

    data = read_json(candidate)
    candidate_errors = validate_candidate_rows(data.get("frames"), current, version=episode_contract_version(ep))
    global_codes = data.get("issue_codes")
    if not isinstance(global_codes, list):
        candidate_errors.append("global issue_codes must be list")
        global_codes = []
    elif global_codes:
        candidate_errors.append(f"global issue_codes must be empty for PASS: {global_codes}")
    if (data.get("summary") or {}).get("passed") is not True:
        candidate_errors.append("critic summary.passed must be true")

    provenance = {
        "runtime": "CODEX_ISOLATED",
        "isolated_session": True,
        "review_scope": "FULL_FRAME_SET",
        "attempt": attempt,
        "reviewed_at": now(),
        "log": log.relative_to(ROOT).as_posix(),
    }
    version = episode_contract_version(ep)
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
            **phase3_context_hashes(ep, frame["frame"]),
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
    candidate.unlink(missing_ok=True)

    verify_errors = verify_episode(ep, metadata_only=False, write_audit=True)
    errors = candidate_errors + [x for x in verify_errors if x not in candidate_errors]
    if errors:
        print("FRAME SEMANTIC REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        return 2
    print("FRAME SEMANTIC REVIEW PASS")
    return 0


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
    p.add_argument("--timeout", type=int, default=1800)
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
