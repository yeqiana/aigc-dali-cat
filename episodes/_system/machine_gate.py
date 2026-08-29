#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from story_os_contract import canonical_stages
from incremental_frame_review import review_required as semantic_frame_review_required, verify_episode as verify_frame_semantic_episode

STATES = canonical_stages()
STATE_MIN = {name: idx for idx, name in enumerate(STATES)}
HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
CALIBRATION_ROLES = ("baseline", "worst_condition", "first_major_anomaly")
HARD_REVIEW_FIELDS = (
    "viewpoint_physics",
    "capture_profile_match",
    "not_cinematic",
    "album_test",
)
OPTIONAL_REVIEW_FIELDS = (
    "unplanned_recorder_absent",
    "identity_match",
    "key_prop_match",
    "location_match",
    "continuity_match",
    "defects_are_causal",
)
RED_FLAGS = {
    "centered_subject",
    "direct_gaze",
    "perfect_face_light",
    "clean_edges",
    "everything_fully_shown",
    "commercial_sharpness",
    "cinematic_or_promo",
}
HARD_FAILURES = {
    "impossible_viewpoint",
    "unexplained_camera_visible",
    "identity_drift",
    "key_prop_drift",
    "location_structure_drift",
    "sudden_cinematic_shift",
    "critical_text_error",
    "unexplained_third_person",
}


@dataclass
class Finding:
    level: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.code}: {self.message}"


def load_json(path: Path, findings: list[Finding], required: bool = True) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if required:
            findings.append(Finding("FAIL", "missing_json", str(path)))
        return None
    except json.JSONDecodeError as exc:
        findings.append(Finding("FAIL", "invalid_json", f"{path}: {exc}"))
        return None
    if not isinstance(data, dict):
        findings.append(Finding("FAIL", "invalid_json_root", f"{path}: top-level must be object"))
        return None
    return data


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_relative_path(repo_root: Path, raw: object, findings: list[Finding], where: str) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        findings.append(Finding("FAIL", "required_path", f"{where} must be a repository-relative path"))
        return None
    value = raw.strip()
    if "\\" in value or re.match(r"^[A-Za-z]:", value) or Path(value).is_absolute():
        findings.append(Finding("FAIL", "non_portable_path", f"{where}: {value}"))
        return None
    root = repo_root.resolve()
    path = (root / value).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError:
        findings.append(Finding("FAIL", "path_outside_repo", f"{where}: {value}"))
        return None
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_hashed_asset(
    repo_root: Path,
    item: dict,
    findings: list[Finding],
    where: str,
    *,
    metadata_only: bool,
) -> None:
    path = repo_relative_path(repo_root, item.get("path") or item.get("asset_path"), findings, f"{where}.path")
    expected = str(item.get("sha256") or "")
    if not HEX64_RE.match(expected):
        findings.append(Finding("FAIL", "invalid_sha256", f"{where}.sha256 must be 64 hex chars"))
    if path is None or metadata_only:
        return
    if not path.is_file():
        findings.append(Finding("FAIL", "missing_asset", f"{where}: {path}"))
        return
    actual = sha256_file(path)
    if HEX64_RE.match(expected) and actual.lower() != expected.lower():
        findings.append(Finding("FAIL", "asset_hash_drift", f"{where}: expected={expected}, actual={actual}"))


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_authenticity_card(gates: dict, manifest: dict, findings: list[Finding]) -> None:
    visual = gates.get("visual") if isinstance(gates.get("visual"), dict) else {}
    card = visual.get("authenticity_card")
    if not isinstance(card, dict):
        findings.append(Finding("FAIL", "authenticity_card", "visual.authenticity_card must be object"))
        return
    for key in ("story_era", "location", "photographer", "shooting_reason"):
        if not nonempty(card.get(key)):
            findings.append(Finding("FAIL", "authenticity_field", f"visual.authenticity_card.{key} is required"))
    primary = card.get("primary_capture")
    if not isinstance(primary, dict) or not nonempty(primary.get("id")) or not nonempty(primary.get("device")):
        findings.append(Finding("FAIL", "primary_capture", "primary_capture requires non-empty id + device"))
    secondary = card.get("secondary_captures")
    if not isinstance(secondary, list):
        findings.append(Finding("FAIL", "secondary_captures", "secondary_captures must be array"))
    elif len(secondary) > 2:
        findings.append(Finding("FAIL", "secondary_capture_limit", "辅助采集设备最多 2 种"))
    elif secondary and not nonempty(card.get("secondary_source_explanation")):
        findings.append(Finding("FAIL", "secondary_capture_reason", "存在辅助采集源时必须解释剧情来源"))
    ratio = ((manifest.get("episode") or {}).get("aspect_ratio"))
    if card.get("aspect_ratio") != ratio:
        findings.append(Finding("FAIL", "authenticity_ratio", f"authenticity_card.aspect_ratio must equal manifest aspect_ratio={ratio!r}"))
    states = card.get("capture_states")
    if not isinstance(states, dict):
        findings.append(Finding("FAIL", "capture_states", "capture_states must be object"))
    else:
        for key in ("stable", "restricted", "lost_control"):
            if not nonempty(states.get(key)):
                findings.append(Finding("FAIL", "capture_state", f"capture_states.{key} is required"))
    rules = card.get("camera_rules")
    if not isinstance(rules, dict):
        findings.append(Finding("FAIL", "camera_rules", "camera_rules must be object"))
    else:
        if rules.get("current_device_may_be_fully_visible") is True and not nonempty(rules.get("current_device_visibility_explanation")):
            findings.append(Finding("FAIL", "camera_visibility", "当前第一视角设备完整入镜必须有物理解释"))
        if rules.get("photographer_may_be_fully_visible") is True and not nonempty(rules.get("photographer_visibility_explanation")):
            findings.append(Finding("FAIL", "photographer_visibility", "拍摄者完整入镜必须有镜面/固定机位/接拍等解释"))


def frame_total(manifest: dict) -> int | None:
    value = ((manifest.get("release") or {}).get("body_frame_count"))
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def check_calibration(repo_root: Path, gates: dict, manifest: dict, findings: list[Finding], *, metadata_only: bool) -> None:
    visual = gates.get("visual") if isinstance(gates.get("visual"), dict) else {}
    calibration = visual.get("calibration")
    if not isinstance(calibration, dict):
        findings.append(Finding("FAIL", "calibration", "visual.calibration must be object"))
        return
    total = frame_total(manifest)
    admissions = visual.get("admission_frames") if isinstance(visual.get("admission_frames"), list) else []
    seen: list[int] = []
    for role in CALIBRATION_ROLES:
        item = calibration.get(role)
        where = f"visual.calibration.{role}"
        if not isinstance(item, dict):
            findings.append(Finding("FAIL", "calibration_role", f"{where} must be object"))
            continue
        frame = item.get("frame")
        if total is None or isinstance(frame, bool) or not isinstance(frame, int) or not 1 <= frame <= total:
            findings.append(Finding("FAIL", "calibration_frame", f"{where}.frame must be within body frame range"))
        else:
            seen.append(frame)
            if frame not in admissions:
                findings.append(Finding("FAIL", "calibration_not_admission", f"frame {frame:02d} must be one of four visual admission frames"))
        if item.get("decision") != "passed":
            findings.append(Finding("FAIL", "calibration_not_passed", f"{where}.decision must be 'passed'"))
        check_hashed_asset(repo_root, item, findings, where, metadata_only=metadata_only)
    if len(seen) == 3 and len(set(seen)) != 3:
        findings.append(Finding("FAIL", "calibration_duplicate", "三张真实性校准必须是三个不同图号"))
    sheet = visual.get("calibration_contact_sheet")
    if not isinstance(sheet, dict):
        findings.append(Finding("FAIL", "calibration_sheet", "visual.calibration_contact_sheet must be object"))
    else:
        check_hashed_asset(repo_root, sheet, findings, "visual.calibration_contact_sheet", metadata_only=metadata_only)


def check_references(repo_root: Path, gates: dict, findings: list[Finding], *, metadata_only: bool) -> None:
    visual = gates.get("visual") if isinstance(gates.get("visual"), dict) else {}
    refs = visual.get("references")
    if not isinstance(refs, dict):
        findings.append(Finding("FAIL", "reference_registry", "visual.references must be object"))
        return
    items = refs.get("items")
    if not isinstance(items, list):
        findings.append(Finding("FAIL", "reference_items", "visual.references.items must be array"))
        return
    ids: set[str] = set()
    passed_anchors: set[str] = set()
    for idx, item in enumerate(items):
        where = f"visual.references.items[{idx}]"
        if not isinstance(item, dict):
            findings.append(Finding("FAIL", "reference_item", f"{where} must be object"))
            continue
        rid = item.get("id")
        if not nonempty(rid) or rid in ids:
            findings.append(Finding("FAIL", "reference_id", f"{where}.id must be unique non-empty string"))
        else:
            ids.add(rid)
        if item.get("kind") not in {"identity", "prop", "location", "capture_style"}:
            findings.append(Finding("FAIL", "reference_kind", f"{where}.kind invalid"))
        if not nonempty(item.get("anchor")):
            findings.append(Finding("FAIL", "reference_anchor", f"{where}.anchor required"))
        if item.get("decision") != "passed":
            findings.append(Finding("FAIL", "reference_not_passed", f"{where}.decision must be passed"))
        else:
            passed_anchors.add(str(item.get("anchor")))
        check_hashed_asset(repo_root, item, findings, where, metadata_only=metadata_only)
    if refs.get("required") is True:
        required = refs.get("required_anchors")
        if not isinstance(required, list) or not required:
            findings.append(Finding("FAIL", "required_reference_anchors", "references.required=true requires required_anchors"))
        else:
            for anchor in required:
                if anchor not in passed_anchors:
                    findings.append(Finding("FAIL", "missing_reference_anchor", f"required reference anchor not passed: {anchor}"))


def review_path(repo_root: Path, episode_dir: Path, gates: dict, key: str) -> Path:
    evidence = gates.get("production_evidence") if isinstance(gates.get("production_evidence"), dict) else {}
    raw = evidence.get("frame_review_dir", "meta/frame-reviews")
    base = Path(raw)
    if base.is_absolute():
        return base / f"{key}.json"
    return episode_dir / base / f"{key}.json"


def check_frame_review(path: Path, key: str, findings: list[Finding]) -> None:
    data = load_json(path, findings)
    if data is None:
        return
    if data.get("schema_version") != 1:
        findings.append(Finding("FAIL", "frame_review_schema", f"{path}: schema_version must be 1"))
    frame = str(data.get("frame") or "")
    if frame.zfill(2) != key:
        findings.append(Finding("FAIL", "frame_review_number", f"{path}: frame must be {key}"))
    for field in HARD_REVIEW_FIELDS:
        if data.get(field) != "pass":
            findings.append(Finding("FAIL", "frame_review_hard_fail", f"{key}.{field} must be pass"))
    for field in OPTIONAL_REVIEW_FIELDS:
        if data.get(field) not in {"pass", "fail", "na"}:
            findings.append(Finding("FAIL", "frame_review_field", f"{key}.{field} must be pass/fail/na"))
        elif data.get(field) == "fail":
            findings.append(Finding("FAIL", "frame_review_fail", f"{key}.{field}=fail"))
    hard_failures = data.get("hard_failures_detected")
    if not isinstance(hard_failures, list) or any(x not in HARD_FAILURES for x in hard_failures):
        findings.append(Finding("FAIL", "hard_failures", f"{key}.hard_failures_detected contains invalid values"))
    elif hard_failures:
        findings.append(Finding("FAIL", "hard_failure_detected", f"{key}: hard failures detected: {hard_failures}"))
    detected = data.get("red_flags_detected")
    exempted = data.get("red_flags_exempted")
    if not isinstance(detected, list) or any(x not in RED_FLAGS for x in detected):
        findings.append(Finding("FAIL", "red_flags", f"{key}.red_flags_detected contains invalid values"))
        detected = []
    if not isinstance(exempted, list) or any(x not in RED_FLAGS for x in exempted):
        findings.append(Finding("FAIL", "red_flags", f"{key}.red_flags_exempted contains invalid values"))
        exempted = []
    if not set(exempted).issubset(set(detected)):
        findings.append(Finding("FAIL", "red_flag_exemption", f"{key}: exemptions must be a subset of detected flags"))
    if exempted:
        exc = data.get("intentional_exception")
        if not isinstance(exc, dict) or exc.get("enabled") is not True or not nonempty(exc.get("reason")):
            findings.append(Finding("FAIL", "red_flag_exception_reason", f"{key}: red-flag exemption requires pre-registered reason"))
    effective = len(set(detected) - set(exempted))
    if effective >= 3:
        findings.append(Finding("FAIL", "red_flag_threshold", f"{key}: effective photography red flags={effective} >= 3"))
    if data.get("decision") not in {"pass", "warning"}:
        findings.append(Finding("FAIL", "frame_review_decision", f"{key}.decision must be pass or warning before production gate"))


def check_production(repo_root: Path, episode_dir: Path, gates: dict, manifest: dict, findings: list[Finding], *, metadata_only: bool) -> None:
    semantic_required = semantic_frame_review_required(episode_dir)
    ledger = load_json(episode_dir / "meta/production-ledger.json", findings)
    if ledger is None:
        return
    total = frame_total(manifest)
    frames = ledger.get("frames")
    if not isinstance(frames, dict) or total is None:
        findings.append(Finding("FAIL", "production_frames", "production ledger frames/body count invalid"))
        return
    if len(frames) != total:
        findings.append(Finding("FAIL", "production_frame_count", f"ledger frames={len(frames)}, manifest body_frame_count={total}"))
    for number in range(1, total + 1):
        key = f"{number:02d}"
        frame = frames.get(key)
        if not isinstance(frame, dict):
            findings.append(Finding("FAIL", "missing_production_frame", f"ledger missing frame {key}"))
            continue
        if frame.get("status") not in {"PASSED", "LOCKED"}:
            findings.append(Finding("FAIL", "production_status", f"{key}: status={frame.get('status')!r}, expected PASSED/LOCKED"))
        if frame.get("content_repairs_used", 0) > 1:
            findings.append(Finding("FAIL", "repair_limit", f"{key}: content_repairs_used > 1"))
        approved = frame.get("approved_asset")
        if not isinstance(approved, dict):
            findings.append(Finding("FAIL", "approved_asset", f"{key}: approved_asset required"))
        else:
            check_hashed_asset(repo_root, approved, findings, f"production.frames.{key}.approved_asset", metadata_only=metadata_only)
        if frame.get("status") == "LOCKED":
            lock = frame.get("lock")
            if not isinstance(lock, dict) or not isinstance(approved, dict) or lock.get("sha256") != approved.get("sha256"):
                findings.append(Finding("FAIL", "lock_hash", f"{key}: lock hash must equal approved asset hash"))
        if not semantic_required and not metadata_only:
            check_frame_review(review_path(repo_root, episode_dir, gates, key), key, findings)

    if semantic_required:
        for error in verify_frame_semantic_episode(episode_dir, metadata_only=metadata_only, write_audit=False):
            findings.append(Finding("FAIL", "frame_semantic_review", error))


def validate(episode_dir: Path, target: str, *, metadata_only: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    gates = load_json(episode_dir / "meta/story-gates.json", findings)
    manifest = load_json(episode_dir / "meta/release-manifest.json", findings)
    if gates is None or manifest is None:
        return findings
    contract = gates.get("machine_contract")
    if not isinstance(contract, dict) or contract.get("strict") is not True:
        findings.append(Finding("WARN", "machine_gate_legacy", "machine_contract.strict is not enabled; legacy compatibility mode"))
        return findings
    if contract.get("version") != 1:
        findings.append(Finding("FAIL", "machine_contract", "machine_contract.version must be 1"))
        return findings
    if target not in STATE_MIN:
        findings.append(Finding("FAIL", "target", f"unknown target state: {target}"))
        return findings
    idx = STATE_MIN[target]
    repo_root = repo_root_from_script()
    if idx >= STATE_MIN["VISUAL_CALIBRATED"]:
        check_authenticity_card(gates, manifest, findings)
        check_calibration(repo_root, gates, manifest, findings, metadata_only=metadata_only)
        check_references(repo_root, gates, findings, metadata_only=metadata_only)
    if idx >= STATE_MIN["PRODUCTION_PASSED"]:
        check_production(repo_root, episode_dir, gates, manifest, findings, metadata_only=metadata_only)
    return findings


def current_state(episode_dir: Path) -> str:
    data = json.loads((episode_dir / "meta/episode-state.json").read_text(encoding="utf-8"))
    state = data.get("current_state")
    if state not in STATE_MIN:
        raise SystemExit(f"invalid current_state in {episode_dir}: {state!r}")
    return state


def discover_episode_dirs(repo_root: Path) -> list[Path]:
    return sorted({p.parents[1] for p in (repo_root / "episodes").rglob("meta/story-gates.json")})


def print_findings(ep: Path, target: str, findings: list[Finding]) -> bool:
    failed = any(x.level == "FAIL" for x in findings)
    print(f"=== {'FAIL' if failed else 'PASS'} MACHINE GATE {target} :: {ep} ===")
    if findings:
        for item in findings:
            print(item)
    else:
        print("[PASS] clean")
    return not failed


def main() -> int:
    p = argparse.ArgumentParser(description="DALI CAT Story OS V1.5 machine-enforced evidence gate")
    p.add_argument("episode_dir", nargs="?")
    p.add_argument("--all", action="store_true", help="validate all tracked episodes at their current state")
    p.add_argument("--target", choices=STATES)
    p.add_argument("--metadata-only", action="store_true")
    args = p.parse_args()
    if bool(args.episode_dir) == bool(args.all):
        p.error("provide exactly one episode_dir or --all")
    if args.all and args.target:
        p.error("--target is only valid for one episode")
    ok = True
    if args.all:
        episodes = discover_episode_dirs(repo_root_from_script())
        for ep in episodes:
            target = current_state(ep)
            ok = print_findings(ep, target, validate(ep, target, metadata_only=args.metadata_only)) and ok
    else:
        ep = Path(args.episode_dir).resolve()
        target = args.target or current_state(ep)
        ok = print_findings(ep, target, validate(ep, target, metadata_only=args.metadata_only))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
