#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from episode_state import MANIFEST_FILE, STATE_FILE, STATES

STATE_MIN = {name: idx for idx, name in enumerate(STATES)}
PRODUCTION_DECISIONS = {"pending", "pass", "fail"}
PROPAGATION_DECISIONS = {"pending", "strong", "publishable", "conditional", "not_recommended"}
PUBLISH_DECISIONS = {"hold", "go"}


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


def resolve_repo_path(repo_root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    p = Path(value)
    return p if p.is_absolute() else repo_root / p


def require_string(obj: dict, key: str, findings: list[Finding], where: str) -> str | None:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.append(Finding("FAIL", "required_field", f"{where}.{key} must be a non-empty string"))
        return None
    return value


def require_repo_path(
    repo_root: Path,
    obj: dict,
    key: str,
    findings: list[Finding],
    where: str,
    *,
    metadata_only: bool,
    asset_path: bool = False,
) -> Path | None:
    value = require_string(obj, key, findings, where)
    if value is None:
        return None
    p = resolve_repo_path(repo_root, value)
    if metadata_only and asset_path:
        return p
    if p is not None and not p.exists():
        findings.append(Finding("FAIL", "missing_path", f"{where}.{key}: {value}"))
    return p


def check_common(state: dict, manifest: dict, findings: list[Finding]) -> str | None:
    if state.get("schema_version") != 1:
        findings.append(Finding("FAIL", "state_schema", "episode-state.json schema_version must be 1"))
    if manifest.get("schema_version") != 1:
        findings.append(Finding("FAIL", "manifest_schema", "release-manifest.json schema_version must be 1"))

    current = state.get("current_state")
    if current not in STATES:
        findings.append(Finding("FAIL", "invalid_state", f"current_state={current!r}"))
        current = None

    for key in ("episode_id", "series", "title", "updated_at"):
        require_string(state, key, findings, "state")

    history = state.get("history")
    if not isinstance(history, list) or not history:
        findings.append(Finding("FAIL", "state_history", "state.history must be a non-empty array"))
    elif current and history[-1].get("state") != current:
        findings.append(Finding("FAIL", "state_history_tail", "last history state must equal current_state"))

    episode = manifest.get("episode")
    if not isinstance(episode, dict):
        findings.append(Finding("FAIL", "manifest_episode", "manifest.episode must be an object"))
    else:
        for key in ("id", "series", "title", "format", "aspect_ratio"):
            require_string(episode, key, findings, "manifest.episode")
        if episode.get("id") != state.get("episode_id"):
            findings.append(Finding("FAIL", "id_drift", "state episode_id != manifest episode.id"))
        if episode.get("series") != state.get("series"):
            findings.append(Finding("FAIL", "series_drift", "state series != manifest episode.series"))
        if episode.get("title") != state.get("title"):
            findings.append(Finding("FAIL", "title_drift", "state title != manifest episode.title"))

    release = manifest.get("release")
    if not isinstance(release, dict):
        findings.append(Finding("FAIL", "manifest_release", "manifest.release must be an object"))
    else:
        count = release.get("body_frame_count")
        if not isinstance(count, int) or count <= 0:
            findings.append(Finding("FAIL", "frame_count", "release.body_frame_count must be > 0"))

    quality = manifest.get("quality")
    if not isinstance(quality, dict):
        findings.append(Finding("FAIL", "manifest_quality", "manifest.quality must be an object"))
    else:
        if quality.get("production_gate") not in PRODUCTION_DECISIONS:
            findings.append(Finding("FAIL", "production_gate", "invalid quality.production_gate"))
        if quality.get("propagation_decision") not in PROPAGATION_DECISIONS:
            findings.append(Finding("FAIL", "propagation_decision", "invalid quality.propagation_decision"))
        if quality.get("publish_decision") not in PUBLISH_DECISIONS:
            findings.append(Finding("FAIL", "publish_decision", "invalid quality.publish_decision"))
    return current


def check_stage(repo_root: Path, episode_dir: Path, manifest: dict, current: str, findings: list[Finding], *, metadata_only: bool) -> None:
    idx = STATE_MIN[current]
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    release = manifest.get("release") if isinstance(manifest.get("release"), dict) else {}
    quality = manifest.get("quality") if isinstance(manifest.get("quality"), dict) else {}
    publication = manifest.get("publication") if isinstance(manifest.get("publication"), dict) else {}
    data_review = manifest.get("data_review") if isinstance(manifest.get("data_review"), dict) else {}

    if idx >= STATE_MIN["STORYBOARD_LOCKED"]:
        require_repo_path(repo_root, artifacts, "storyboard", findings, "manifest.artifacts", metadata_only=metadata_only)

    if idx >= STATE_MIN["VISUAL_CALIBRATED"]:
        require_repo_path(repo_root, artifacts, "visual_spec", findings, "manifest.artifacts", metadata_only=metadata_only)

    if idx >= STATE_MIN["PRODUCTION_PASSED"]:
        require_repo_path(repo_root, artifacts, "production_review", findings, "manifest.artifacts", metadata_only=metadata_only)
        if quality.get("production_gate") != "pass":
            findings.append(Finding("FAIL", "production_not_passed", "quality.production_gate must be 'pass'"))

    if idx >= STATE_MIN["PUBLISH_READY"]:
        require_string(release, "version", findings, "manifest.release")
        publish_dir = require_repo_path(repo_root, release, "publish_dir", findings, "manifest.release", metadata_only=metadata_only, asset_path=True)
        require_repo_path(repo_root, release, "cover_path", findings, "manifest.release", metadata_only=metadata_only, asset_path=True)
        body_glob = require_string(release, "body_glob", findings, "manifest.release")
        require_repo_path(repo_root, artifacts, "captions", findings, "manifest.artifacts", metadata_only=metadata_only)
        require_repo_path(repo_root, artifacts, "publish_copy", findings, "manifest.artifacts", metadata_only=metadata_only)
        require_repo_path(repo_root, artifacts, "propagation_card", findings, "manifest.artifacts", metadata_only=metadata_only)

        score = quality.get("propagation_score")
        if not isinstance(score, (int, float)) or not (0 <= float(score) <= 10):
            findings.append(Finding("FAIL", "propagation_score", "quality.propagation_score must be 0..10"))
        if quality.get("propagation_decision") == "pending":
            findings.append(Finding("FAIL", "propagation_pending", "propagation decision cannot be pending"))
        if quality.get("publish_decision") != "go":
            findings.append(Finding("FAIL", "publish_hold", "quality.publish_decision must be 'go'"))
        if quality.get("propagation_decision") in {"conditional", "not_recommended"}:
            note = quality.get("decision_note")
            if not isinstance(note, str) or not note.strip():
                findings.append(Finding("FAIL", "decision_note", "conditional/not_recommended release requires decision_note"))

        for key in ("actual_title", "description"):
            require_string(publication, key, findings, "manifest.publication")
        topics = publication.get("topics")
        if not isinstance(topics, list) or not topics or not all(isinstance(x, str) and x.strip() for x in topics):
            findings.append(Finding("FAIL", "topics", "publication.topics must be a non-empty string array"))

        if not metadata_only and publish_dir and publish_dir.exists() and body_glob:
            files = [p for p in publish_dir.glob(body_glob) if p.is_file()]
            expected = release.get("body_frame_count")
            if isinstance(expected, int) and len(files) != expected:
                findings.append(Finding("FAIL", "body_count_mismatch", f"{publish_dir}: expected {expected}, found {len(files)} by {body_glob!r}"))

    if idx >= STATE_MIN["PUBLISHED"]:
        require_string(publication, "published_at", findings, "manifest.publication")

    if idx >= STATE_MIN["DATA_REVIEWED"]:
        require_repo_path(repo_root, data_review, "report_path", findings, "manifest.data_review", metadata_only=metadata_only)
        completed = data_review.get("completed_checkpoints")
        if not isinstance(completed, list) or "48h" not in completed:
            findings.append(Finding("FAIL", "missing_48h_review", "DATA_REVIEWED requires completed_checkpoints to include '48h'"))

    readme = episode_dir / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="replace")
        if current == "PUBLISHED" and "可发布" in text and "已发布" not in text:
            findings.append(Finding("WARN", "readme_state_drift", "machine state is PUBLISHED but episode README still says 可发布"))
        if idx < STATE_MIN["PUBLISHED"] and "已发布" in text:
            findings.append(Finding("WARN", "readme_state_drift", f"machine state is {current} but episode README says 已发布"))


def validate_episode(episode_dir: Path, repo_root: Path, metadata_only: bool, target_state: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    state = load_json(episode_dir / STATE_FILE, findings)
    manifest = load_json(episode_dir / MANIFEST_FILE, findings)
    if state is None or manifest is None:
        return findings
    current = check_common(state, manifest, findings)
    effective_state = target_state or current
    if target_state is not None and target_state not in STATES:
        findings.append(Finding("FAIL", "invalid_target_state", f"target_state={target_state!r}"))
        effective_state = None
    if effective_state:
        check_stage(repo_root, episode_dir, manifest, effective_state, findings, metadata_only=metadata_only)
    return findings


def discover_episode_dirs(episodes_root: Path) -> Iterable[Path]:
    for state_path in episodes_root.rglob(str(STATE_FILE)):
        if "_system" not in state_path.parts:
            yield state_path.parents[1]


def print_result(episode_dir: Path, findings: list[Finding]) -> bool:
    failed = any(f.level == "FAIL" for f in findings)
    print(f"\n=== {'FAIL' if failed else 'PASS'} {episode_dir} ===")
    if not findings:
        print("[PASS] clean")
    else:
        for finding in findings:
            print(finding)
    return not failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate episode state + manifest + release gates")
    parser.add_argument("episode_dir", nargs="?")
    parser.add_argument("--all", action="store_true", help="validate every episode that has meta/episode-state.json")
    parser.add_argument("--repo-root", help="override repository root")
    parser.add_argument("--metadata-only", action="store_true", help="skip existence/count checks for ignored image assets")
    parser.add_argument("--target", choices=STATES, help="validate prerequisites for a future target state without changing state")
    args = parser.parse_args()

    if bool(args.episode_dir) == bool(args.all):
        parser.error("provide exactly one episode_dir or --all")
    if args.all and args.target:
        parser.error("--target is only valid for a single episode")

    repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_script()
    episodes_root = repo_root / "episodes"
    dirs = sorted(set(discover_episode_dirs(episodes_root))) if args.all else [Path(args.episode_dir).resolve()]
    if not dirs:
        print("no episode state files found")
        return 0

    ok = True
    for episode_dir in dirs:
        ok = print_result(episode_dir, validate_episode(episode_dir, repo_root, args.metadata_only, args.target)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
