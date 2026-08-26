#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from episode_state import MANIFEST_FILE, STATE_FILE, STATES, SYSTEM_VERSION

STATE_MIN = {name: idx for idx, name in enumerate(STATES)}
PRODUCTION_DECISIONS = {"pending", "pass", "fail"}
PROPAGATION_DECISIONS = {"pending", "strong", "publishable", "conditional", "not_recommended"}
PUBLISH_DECISIONS = {"hold", "go"}
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


@dataclass
class Finding:
    level: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.code}: {self.message}"


def load_json(path: Path, findings: list[Finding]) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        findings.append(Finding("FAIL", "missing_json", str(path)))
    except json.JSONDecodeError as e:
        findings.append(Finding("FAIL", "invalid_json", f"{path}: {e}"))
    return None


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def is_number_0_10(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and 0 <= float(value) <= 10


def resolve_repo_relative_path(repo_root: Path, value: object, findings: list[Finding], where: str) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    p = Path(raw)
    # Manifest paths are portable Git-style repository paths, not OS-native paths.
    # Reject drive-qualified paths (both C:\\x and C:x), UNC/Windows separators,
    # POSIX absolute paths, and traversal that resolves outside repo_root.
    if p.is_absolute() or WINDOWS_DRIVE_RE.match(raw):
        findings.append(Finding("FAIL", "absolute_path", f"{where} must be repository-root relative: {raw}"))
        return None
    if "\\" in raw:
        findings.append(Finding("FAIL", "non_portable_path", f"{where} must use '/' separators: {raw}"))
        return None
    root = repo_root.resolve()
    resolved = (root / p).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        findings.append(Finding("FAIL", "path_outside_repo", f"{where} escapes repository root: {raw}"))
        return None
    return resolved


def require_string(obj: dict, key: str, findings: list[Finding], where: str) -> str | None:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.append(Finding("FAIL", "required_field", f"{where}.{key} must be a non-empty string"))
        return None
    return value


def require_repo_path(repo_root: Path, obj: dict, key: str, findings: list[Finding], where: str, *, metadata_only: bool, asset_path: bool = False) -> Path | None:
    value = require_string(obj, key, findings, where)
    if value is None:
        return None
    p = resolve_repo_relative_path(repo_root, value, findings, f"{where}.{key}")
    if p is None:
        return None
    if metadata_only and asset_path:
        return p
    if not p.exists():
        findings.append(Finding("FAIL", "missing_path", f"{where}.{key}: {value}"))
    return p


def derive_propagation_decision(score: object, s_min: object) -> str | None:
    if not is_number_0_10(score) or not is_number_0_10(s_min):
        return None
    score = float(score); s_min = float(s_min)
    if score < 8.3 or s_min < 7.0:
        return "not_recommended"
    if score < 8.7 or s_min < 7.5:
        return "conditional"
    if score >= 9.2 and s_min >= 8.5:
        return "strong"
    return "publishable"


def check_history(state: dict, current: str | None, findings: list[Finding]) -> None:
    history = state.get("history")
    if not isinstance(history, list) or not history:
        findings.append(Finding("FAIL", "state_history", "state.history must be a non-empty array"))
        return

    first = history[0]
    if not isinstance(first, dict) or first.get("state") not in STATES:
        findings.append(Finding("FAIL", "state_history_entry", "history[0] has invalid state"))
    elif first.get("mode") != "migration" and first.get("state") != "IDEA_LOCKED":
        findings.append(Finding("FAIL", "state_history_origin", "history must start at IDEA_LOCKED unless first entry mode=migration"))

    previous_valid_state: str | None = None
    for i, entry in enumerate(history):
        if not isinstance(entry, dict):
            findings.append(Finding("FAIL", "state_history_entry", f"history[{i}] must be an object"))
            previous_valid_state = None
            continue
        cur = entry.get("state")
        if cur not in STATES:
            findings.append(Finding("FAIL", "state_history_entry", f"history[{i}] has invalid state"))
            previous_valid_state = None
            continue
        if not isinstance(entry.get("at"), str) or not entry.get("at", "").strip():
            findings.append(Finding("FAIL", "state_history_at", f"history[{i}].at must be non-empty"))
        if i == 0:
            previous_valid_state = cur
            continue

        mode = entry.get("mode")
        if mode not in {"advance", "rewind"}:
            findings.append(Finding("FAIL", "state_history_mode", f"history[{i}].mode must be advance or rewind"))
        elif previous_valid_state is not None:
            if mode == "advance" and STATE_MIN[cur] != STATE_MIN[previous_valid_state] + 1:
                findings.append(Finding("FAIL", "illegal_state_history", f"history transition {previous_valid_state} -> {cur} is not adjacent advance"))
            elif mode == "rewind" and STATE_MIN[cur] >= STATE_MIN[previous_valid_state]:
                findings.append(Finding("FAIL", "illegal_state_history", f"history transition {previous_valid_state} -> {cur} is not a rewind"))
        previous_valid_state = cur

    tail = history[-1]
    tail_state = tail.get("state") if isinstance(tail, dict) else None
    if current and tail_state != current:
        findings.append(Finding("FAIL", "state_history_tail", "last history state must equal current_state"))


def check_populated_manifest_paths(repo_root: Path, manifest: dict, findings: list[Finding]) -> None:
    groups = {
        "manifest.release": (manifest.get("release"), ("publish_dir", "cover_path", "contact_sheet_path")),
        "manifest.artifacts": (manifest.get("artifacts"), ("story", "storyboard", "visual_spec", "captions", "publish_copy", "production_review", "propagation_card")),
        "manifest.data_review": (manifest.get("data_review"), ("report_path",)),
    }
    for where, (obj, keys) in groups.items():
        if not isinstance(obj, dict):
            continue
        for key in keys:
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                resolve_repo_relative_path(repo_root, value, findings, f"{where}.{key}")


def check_common(repo_root: Path, state: dict, manifest: dict, findings: list[Finding]) -> str | None:
    if state.get("schema_version") != 1: findings.append(Finding("FAIL", "state_schema", "episode-state.json schema_version must be 1"))
    if manifest.get("schema_version") != 1: findings.append(Finding("FAIL", "manifest_schema", "release-manifest.json schema_version must be 1"))
    for obj, where in ((state,"state"),(manifest,"manifest")):
        tv = obj.get("tool_version")
        if tv is not None and tv != SYSTEM_VERSION:
            findings.append(Finding("WARN", "tool_version", f"{where}.tool_version={tv!r}; current tool is {SYSTEM_VERSION}"))
    current = state.get("current_state")
    if current not in STATES:
        findings.append(Finding("FAIL", "invalid_state", f"current_state={current!r}")); current=None
    for key in ("episode_id","series","title","updated_at"): require_string(state,key,findings,"state")
    check_history(state,current,findings)
    episode = manifest.get("episode")
    if not isinstance(episode,dict): findings.append(Finding("FAIL","manifest_episode","manifest.episode must be an object"))
    else:
        for key in ("id","series","title","format","aspect_ratio"): require_string(episode,key,findings,"manifest.episode")
        if episode.get("id") != state.get("episode_id"): findings.append(Finding("FAIL","id_drift","state episode_id != manifest episode.id"))
        if episode.get("series") != state.get("series"): findings.append(Finding("FAIL","series_drift","state series != manifest episode.series"))
        if episode.get("title") != state.get("title"): findings.append(Finding("FAIL","title_drift","state title != manifest episode.title"))
    release=manifest.get("release")
    if not isinstance(release,dict): findings.append(Finding("FAIL","manifest_release","manifest.release must be an object"))
    elif not isinstance(release.get("body_frame_count"),int) or isinstance(release.get("body_frame_count"),bool) or release.get("body_frame_count")<=0:
        findings.append(Finding("FAIL","frame_count","release.body_frame_count must be > 0"))
    check_populated_manifest_paths(repo_root, manifest, findings)
    quality=manifest.get("quality")
    if not isinstance(quality,dict): findings.append(Finding("FAIL","manifest_quality","manifest.quality must be an object"))
    else:
        if quality.get("production_gate") not in PRODUCTION_DECISIONS: findings.append(Finding("FAIL","production_gate","invalid quality.production_gate"))
        if quality.get("propagation_decision") not in PROPAGATION_DECISIONS: findings.append(Finding("FAIL","propagation_decision","invalid quality.propagation_decision"))
        if quality.get("publish_decision") not in PUBLISH_DECISIONS: findings.append(Finding("FAIL","publish_decision","invalid quality.publish_decision"))
    return current


def check_stage(repo_root: Path, episode_dir: Path, manifest: dict, current: str, findings: list[Finding], *, metadata_only: bool) -> None:
    idx=STATE_MIN[current]
    artifacts=manifest.get("artifacts") if isinstance(manifest.get("artifacts"),dict) else {}
    release=manifest.get("release") if isinstance(manifest.get("release"),dict) else {}
    quality=manifest.get("quality") if isinstance(manifest.get("quality"),dict) else {}
    publication=manifest.get("publication") if isinstance(manifest.get("publication"),dict) else {}
    data_review=manifest.get("data_review") if isinstance(manifest.get("data_review"),dict) else {}
    if idx>=STATE_MIN["STORYBOARD_LOCKED"]: require_repo_path(repo_root,artifacts,"storyboard",findings,"manifest.artifacts",metadata_only=metadata_only)
    if idx>=STATE_MIN["VISUAL_CALIBRATED"]: require_repo_path(repo_root,artifacts,"visual_spec",findings,"manifest.artifacts",metadata_only=metadata_only)
    if idx>=STATE_MIN["PRODUCTION_PASSED"]:
        require_repo_path(repo_root,artifacts,"production_review",findings,"manifest.artifacts",metadata_only=metadata_only)
        require_repo_path(repo_root,artifacts,"captions",findings,"manifest.artifacts",metadata_only=metadata_only)
        if quality.get("production_gate")!="pass": findings.append(Finding("FAIL","production_not_passed","quality.production_gate must be 'pass'"))
    if idx>=STATE_MIN["PUBLISH_READY"]:
        require_string(release,"version",findings,"manifest.release")
        publish_dir=require_repo_path(repo_root,release,"publish_dir",findings,"manifest.release",metadata_only=metadata_only,asset_path=True)
        require_repo_path(repo_root,release,"cover_path",findings,"manifest.release",metadata_only=metadata_only,asset_path=True)
        body_glob=require_string(release,"body_glob",findings,"manifest.release")
        require_repo_path(repo_root,artifacts,"captions",findings,"manifest.artifacts",metadata_only=metadata_only)
        require_repo_path(repo_root,artifacts,"publish_copy",findings,"manifest.artifacts",metadata_only=metadata_only)
        require_repo_path(repo_root,artifacts,"propagation_card",findings,"manifest.artifacts",metadata_only=metadata_only)
        score=quality.get("propagation_score"); s_min=quality.get("s_min_score")
        if not is_number_0_10(score): findings.append(Finding("FAIL","propagation_score","quality.propagation_score must be 0..10"))
        if not is_number_0_10(s_min): findings.append(Finding("FAIL","s_min_score","quality.s_min_score must be 0..10"))
        expected=derive_propagation_decision(score,s_min); actual=quality.get("propagation_decision")
        if actual=="pending": findings.append(Finding("FAIL","propagation_pending","propagation decision cannot be pending"))
        elif expected is not None and actual != expected:
            findings.append(Finding("FAIL","propagation_decision_mismatch",f"score={score}, s_min_score={s_min} => expected {expected}, got {actual}"))
        if quality.get("publish_decision")!="go": findings.append(Finding("FAIL","publish_hold","quality.publish_decision must be 'go'"))
        if actual in {"conditional","not_recommended"} and (not isinstance(quality.get("decision_note"),str) or not quality.get("decision_note","").strip()):
            findings.append(Finding("FAIL","decision_note","conditional/not_recommended release requires decision_note"))
        for key in ("actual_title","description"): require_string(publication,key,findings,"manifest.publication")
        topics=publication.get("topics")
        if not isinstance(topics,list) or not topics or not all(isinstance(x,str) and x.strip() for x in topics): findings.append(Finding("FAIL","topics","publication.topics must be a non-empty string array"))
        if not metadata_only and publish_dir and publish_dir.exists() and body_glob:
            files=[p for p in publish_dir.glob(body_glob) if p.is_file()]; expected_count=release.get("body_frame_count")
            if isinstance(expected_count,int) and len(files)!=expected_count: findings.append(Finding("FAIL","body_count_mismatch",f"{publish_dir}: expected {expected_count}, found {len(files)} by {body_glob!r}"))
    if idx>=STATE_MIN["PUBLISHED"]: require_string(publication,"published_at",findings,"manifest.publication")
    if idx>=STATE_MIN["DATA_REVIEWED"]:
        require_repo_path(repo_root,data_review,"report_path",findings,"manifest.data_review",metadata_only=metadata_only)
        completed=data_review.get("completed_checkpoints")
        if not isinstance(completed,list) or "48h" not in completed: findings.append(Finding("FAIL","missing_48h_review","DATA_REVIEWED requires completed_checkpoints to include '48h'"))
    readme=episode_dir/"README.md"
    if readme.exists():
        text=readme.read_text(encoding="utf-8",errors="replace")
        if current=="PUBLISHED" and "可发布" in text and "已发布" not in text: findings.append(Finding("WARN","readme_state_drift","machine state is PUBLISHED but episode README still says 可发布"))
        if idx<STATE_MIN["PUBLISHED"] and "已发布" in text: findings.append(Finding("WARN","readme_state_drift",f"machine state is {current} but episode README says 已发布"))


def validate_episode(episode_dir: Path, repo_root: Path, metadata_only: bool, target_state: str | None=None) -> list[Finding]:
    findings=[]; state=load_json(episode_dir/STATE_FILE,findings); manifest=load_json(episode_dir/MANIFEST_FILE,findings)
    if state is None or manifest is None: return findings
    current=check_common(repo_root,state,manifest,findings); effective=target_state or current
    if target_state is not None and target_state not in STATES: findings.append(Finding("FAIL","invalid_target_state",f"target_state={target_state!r}")); effective=None
    if effective: check_stage(repo_root,episode_dir,manifest,effective,findings,metadata_only=metadata_only)
    return findings


def discover_episode_dirs(episodes_root: Path) -> Iterable[Path]:
    for state_path in episodes_root.rglob(str(STATE_FILE)):
        if "_system" not in state_path.parts: yield state_path.parents[1]


def print_result(episode_dir: Path, findings: list[Finding]) -> bool:
    failed=any(f.level=="FAIL" for f in findings); print(f"\n=== {'FAIL' if failed else 'PASS'} {episode_dir} ===")
    if not findings: print("[PASS] clean")
    else:
        for finding in findings: print(finding)
    return not failed


def main() -> int:
    parser=argparse.ArgumentParser(description="Validate episode state + manifest + release gates V1.1")
    parser.add_argument("episode_dir",nargs="?"); parser.add_argument("--all",action="store_true"); parser.add_argument("--repo-root"); parser.add_argument("--metadata-only",action="store_true"); parser.add_argument("--target",choices=STATES)
    args=parser.parse_args()
    if bool(args.episode_dir)==bool(args.all): parser.error("provide exactly one episode_dir or --all")
    if args.all and args.target: parser.error("--target is only valid for a single episode")
    repo_root=Path(args.repo_root).resolve() if args.repo_root else repo_root_from_script(); episodes_root=repo_root/"episodes"
    dirs=sorted(set(discover_episode_dirs(episodes_root))) if args.all else [Path(args.episode_dir).resolve()]
    if not dirs: print("no episode state files found"); return 0
    ok=True
    for episode_dir in dirs: ok=print_result(episode_dir,validate_episode(episode_dir,repo_root,args.metadata_only,args.target)) and ok
    return 0 if ok else 1


if __name__ == "__main__": raise SystemExit(main())
