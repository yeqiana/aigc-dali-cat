#!/usr/bin/env python3
"""Read-only provenance audit for frozen Story Semantic Review sources.

The only files this command may create are its immutable audit report and, when
both byte-exact historical sources are recovered, a runtime-only source bundle.
It never rewrites Episode authority or canonical Story/Storyboard files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
sys.path[:0] = [str(ROOT), str(SYSTEM)]

TEXT_SUFFIXES = {
    ".json", ".jsonl", ".md", ".txt", ".yaml", ".yml", ".toml", ".csv", ".py",
}
SKIP_DIRS = {
    ".git", ".pytest_cache", "__pycache__", "node_modules", ".venv", "venv",
    "images", "media", "publish", "release", "frames", "subtitled",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_set_status(story_exact: bool, storyboard_exact: bool) -> str:
    if story_exact and storyboard_exact:
        return "RECOVERABLE_EXACT"
    if story_exact or storyboard_exact:
        return "PARTIALLY_RECOVERABLE"
    return "UNRECOVERABLE"


def recovery_is_exact(recovery: dict[str, Any], review_sha: str) -> bool:
    content = recovery.get("bytes")
    return isinstance(content, bytes) and sha256_bytes(content).lower() == str(review_sha).lower()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _load_runtime_environment() -> tuple[str, ...]:
    from scripts.phase9_runtime_launcher import load_runtime_env_file

    env_path = ROOT / ".storyos/runtime-launcher/runtime.env"
    loaded, keys = load_runtime_env_file(env_path, dict(os.environ))
    os.environ.update(loaded)
    return keys


def _iter_text_files(roots: list[Path]):
    seen: set[Path] = set()
    for root in roots:
        root = root.resolve()
        if root.is_file():
            paths = [root]
        elif root.is_dir():
            paths = root.rglob("*")
        else:
            continue
        for path in paths:
            try:
                resolved = path.resolve()
                if resolved in seen or not resolved.is_file():
                    continue
                if any(part in SKIP_DIRS for part in resolved.parts):
                    continue
                if resolved.suffix.lower() not in TEXT_SUFFIXES or resolved.stat().st_size > 32 * 1024 * 1024:
                    continue
                seen.add(resolved)
                yield resolved
            except OSError:
                continue


def _scan_exact_files(target_sha: str, roots: list[Path]) -> list[dict[str, str]]:
    matches = []
    for path in _iter_text_files(roots):
        try:
            actual = sha256_file(path)
        except OSError:
            continue
        if actual.lower() == target_sha.lower():
            matches.append({"path": path.as_posix(), "sha256": actual})
    return matches


def _git_bytes(commit: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _git_path_candidates(original_path: str, target_sha: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["git", "log", "--all", "--format=%H", "--", original_path], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", check=False,
    )
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    # Detached worktree HEADs may not be reachable from a named ref.
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", check=False,
    )
    for line in worktrees.stdout.splitlines():
        if line.startswith("HEAD "):
            commits.append(line.split(maxsplit=1)[1])
    matches: list[dict[str, Any]] = []
    for commit in dict.fromkeys(commits):
        content = _git_bytes(commit, original_path)
        if content is not None and sha256_bytes(content).lower() == target_sha.lower():
            matches.append({
                "found": True,
                "origin": "git_exact_blob",
                "path": original_path,
                "git_commit": commit,
                "sha256": sha256_bytes(content),
                "bytes": content,
            })
    return matches


def _find_recovery(
    *, target_sha: str, original_path: str, current_path: Path, episode: Path,
    review_export: Path, review_record: dict[str, Any] | None,
) -> dict[str, Any]:
    if current_path.is_file():
        current_bytes = current_path.read_bytes()
        if sha256_bytes(current_bytes).lower() == target_sha.lower():
            return {"found": True, "origin": "current_canonical_file", "path": current_path.as_posix(),
                    "sha256": target_sha, "bytes": current_bytes}

    # Request, candidate, runtime contract, export, persisted record and
    # historical archive locations are searched as exact byte sources.
    request_dirs = [episode / "meta/runtime/reviews", episode / "meta/runtime/host-requests"]
    archive_roots = [
        episode / "meta/runtime", episode / "meta", episode / "docs",
        ROOT / "reports", ROOT / "episodes/_archive", ROOT / ".storyos",
    ]
    if review_export.is_file():
        archive_roots.append(review_export.parent)
    evidence_paths = []
    if isinstance(review_record, dict):
        provenance = review_record.get("critic_provenance") or {}
        request_rel = provenance.get("request_path") if isinstance(provenance, dict) else None
        if request_rel:
            evidence_paths.append(ROOT / str(request_rel))
    for root in request_dirs:
        if root.is_dir():
            evidence_paths.extend(root.glob("*story-semantic*request*.json"))
    archived = _scan_exact_files(target_sha, [*evidence_paths, *archive_roots])
    if archived:
        path = Path(archived[0]["path"])
        return {"found": True, "origin": "immutable_runtime_or_archive_copy", "path": path.as_posix(),
                "sha256": target_sha, "bytes": path.read_bytes()}

    # Also inspect the same relative path in every registered worktree before
    # using Git objects; this catches a detached checkout with uncommitted source.
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", check=False,
    )
    for line in worktrees.stdout.splitlines():
        if not line.startswith("worktree "):
            continue
        worktree_root = Path(line.split(maxsplit=1)[1])
        candidate = worktree_root / Path(original_path)
        try:
            content = candidate.read_bytes()
        except OSError:
            continue
        if sha256_bytes(content).lower() == target_sha.lower():
            return {"found": True, "origin": "registered_worktree_exact_file", "path": candidate.as_posix(),
                    "sha256": target_sha, "bytes": content}

    git_matches = _git_path_candidates(original_path, target_sha)
    if git_matches:
        return git_matches[0]
    return {"found": False, "origin": None, "path": None, "sha256": None, "bytes": None}


def _bundle_exact_sources(episode: Path, story: dict, storyboard: dict,
                          story_review_sha: str, storyboard_review_sha: str) -> Path:
    if not story.get("bytes") or not storyboard.get("bytes"):
        raise ValueError("historical bundle requires both exact source byte streams")
    if sha256_bytes(story["bytes"]) != story_review_sha or sha256_bytes(storyboard["bytes"]) != storyboard_review_sha:
        raise ValueError("historical bundle source hashes do not match canonical Story Review")
    parent = episode / "meta/runtime/agent-shadow/story-semantic-critic"
    bundle = parent / "frozen-source-20260927"
    index = 0
    while bundle.exists():
        index += 1
        bundle = parent / f"frozen-source-20260927-retry{index}"
    bundle.mkdir(parents=True, exist_ok=False)
    (bundle / "story.md").write_bytes(story["bytes"])
    (bundle / "storyboard.md").write_bytes(storyboard["bytes"])
    manifest = {
        "schema_version": 1,
        "source_type": "historical_frozen_story_review_source_set",
        "not_canonical": True,
        "candidate_authority": "runtime_evidence_only",
        "canonical_write": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sources": {
            "story": {
                "original_path": story.get("path"),
                "review_bound_sha256": story_review_sha,
                "recovered_sha256": sha256_bytes(story["bytes"]),
                "recovery_origin": story.get("origin"),
                "git_commit": story.get("git_commit"),
                "evidence_path": story.get("path"),
            },
            "storyboard": {
                "original_path": storyboard.get("path"),
                "review_bound_sha256": storyboard_review_sha,
                "recovered_sha256": sha256_bytes(storyboard["bytes"]),
                "recovery_origin": storyboard.get("origin"),
                "git_commit": storyboard.get("git_commit"),
                "evidence_path": storyboard.get("path"),
            },
        },
    }
    with (bundle / "source-manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return bundle


def audit_episode(episode: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    episode = Path(episode).resolve()
    manifest_path = episode / "meta/release-manifest.json"
    export_path = episode / "meta/runtime/review-exports/story-semantic.json"
    initial_immutable_paths = [manifest_path, export_path]
    before_hashes = {
        p.as_posix(): sha256_file(p) for p in initial_immutable_paths if p.is_file()
    }
    initial_manifest = _read_json(manifest_path) or {}
    initial_artifacts = initial_manifest.get("artifacts") or {}
    for rel in (initial_artifacts.get("story"), initial_artifacts.get("storyboard")):
        if rel:
            path = (ROOT / str(rel)).resolve()
            if path.is_file():
                before_hashes[path.as_posix()] = sha256_file(path)
    export = _read_json(export_path) or {}
    review = export
    review_sha_before = None
    state_before = None
    persistence_status = "NOT_READ"
    env_keys: tuple[str, ...] = ()
    try:
        env_keys = _load_runtime_environment()
        import episode_state_persistence
        import story_review

        state_before = episode_state_persistence.load(episode)
        loaded_review = story_review.load_review(episode)
        if isinstance(loaded_review, dict):
            review = loaded_review
            review_sha_before = story_review.review_authority_sha256(episode)
        persistence_status = "AVAILABLE"
    except Exception as exc:
        persistence_status = f"PERSISTENCE_UNAVAILABLE:{type(exc).__name__}"

    manifest = initial_manifest
    artifacts = manifest.get("artifacts") or {}
    original_story = str(artifacts.get("story") or "")
    original_board = str(artifacts.get("storyboard") or "")
    story_path = (ROOT / original_story).resolve() if original_story else episode / "__missing_story__"
    board_path = (ROOT / original_board).resolve() if original_board else episode / "__missing_storyboard__"
    review_story_sha = str(review.get("story_sha256") or "").lower()
    review_board_sha = str(review.get("storyboard_sha256") or "").lower()
    current_story_sha = sha256_file(story_path) if story_path.is_file() else None
    current_board_sha = sha256_file(board_path) if board_path.is_file() else None
    story_match = bool(review_story_sha and current_story_sha == review_story_sha)
    board_match = bool(review_board_sha and current_board_sha == review_board_sha)

    story_recovery = _find_recovery(
        target_sha=review_story_sha, original_path=original_story, current_path=story_path,
        episode=episode, review_export=export_path, review_record=review,
    ) if review_story_sha else {"found": False, "origin": None, "path": None, "sha256": None, "bytes": None}
    board_recovery = _find_recovery(
        target_sha=review_board_sha, original_path=original_board, current_path=board_path,
        episode=episode, review_export=export_path, review_record=review,
    ) if review_board_sha else {"found": False, "origin": None, "path": None, "sha256": None, "bytes": None}
    story_exact = story_recovery.get("found") is True and recovery_is_exact(story_recovery, review_story_sha)
    board_exact = board_recovery.get("found") is True and recovery_is_exact(board_recovery, review_board_sha)
    status = source_set_status(story_exact, board_exact)
    immutable_unchanged = all(
        Path(path).is_file() and sha256_file(Path(path)) == digest
        for path, digest in before_hashes.items()
    )
    try:
        import episode_state_persistence
        import story_review
        review_sha_after = story_review.review_authority_sha256(episode)
        state_after = episode_state_persistence.load(episode) or {}
    except Exception:
        review_sha_after = None
        state_after = {}
    report = {
        "schema_version": 1,
        "kind": "p3_story_semantic_frozen_source_audit",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "episode": episode.relative_to(ROOT).as_posix(),
        "episode_state": (state_before or {}).get("current_state"),
        "persistence_status": persistence_status,
        "runtime_env_loaded_keys": list(env_keys),
        "review_export_path": export_path.relative_to(ROOT).as_posix(),
        "review_record_authority_sha256_before": review_sha_before,
        "review_story_sha256": review_story_sha or None,
        "current_story_sha256": current_story_sha,
        "story_match": story_match,
        "review_storyboard_sha256": review_board_sha or None,
        "current_storyboard_sha256": current_board_sha,
        "storyboard_match": board_match,
        "recovered_story": {
            "found": bool(story_recovery.get("found")), "origin": story_recovery.get("origin"),
            "path": story_recovery.get("path"), "sha256": story_recovery.get("sha256"),
            "exact_match": story_exact, "git_commit": story_recovery.get("git_commit"),
        },
        "recovered_storyboard": {
            "found": bool(board_recovery.get("found")), "origin": board_recovery.get("origin"),
            "path": board_recovery.get("path"), "sha256": board_recovery.get("sha256"),
            "exact_match": board_exact, "git_commit": board_recovery.get("git_commit"),
        },
        "source_set_status": status,
        "search_scopes": [
            "current_episode_files", "review_export", "product_review_requests_and_host_requests",
            "review_record_persistence", "story_review_candidates", "runtime_contracts",
            "release_manifest_history", "reports_and_archives", "registered_worktrees",
            "git_path_history_and_exact_blobs", "local_storyos_runtime_snapshots",
        ],
        "canonical_files_modified": not immutable_unchanged,
        "review_modified": review_sha_before != review_sha_after,
        "episode_state_modified": (state_before or {}).get("current_state") != state_after.get("current_state"),
        "image_generation_invoked": False,
    }
    return report, {"story": story_recovery, "storyboard": board_recovery}


def scan_candidate_episodes() -> dict[str, Any]:
    """Find other real Episodes whose canonical review and current sources agree."""
    _load_runtime_environment()
    import episode_discovery
    import episode_state_persistence
    import story_review

    rows = []
    persistence_error = None
    try:
        episodes = episode_discovery.iter_episode_roots()
        for episode in episodes:
            try:
                state = episode_state_persistence.load(episode) or {}
                review = story_review.load_review(episode)
                if not isinstance(review, dict):
                    # In MySQL-authoritative mode, old canonical JSON review
                    # records remain the supported fallback when no DB row is
                    # present. Read the canonical path directly for discovery;
                    # never materialize or rewrite it.
                    review = _read_json(episode / story_review.REVIEW_REL)
                manifest = _read_json(episode / "meta/release-manifest.json") or {}
                artifacts = manifest.get("artifacts") or {}
                story = (ROOT / str(artifacts.get("story") or "missing")).resolve()
                board = (ROOT / str(artifacts.get("storyboard") or "missing")).resolve()
                summary = (review or {}).get("summary") or {}
                review_decision = str((review or {}).get("decision") or (
                    "PASS" if summary.get("passed") is True else
                    "FAIL" if summary.get("passed") is False else ""
                ))
                legal_review = (
                    isinstance(review, dict)
                    and review_decision in {"PASS", "FAIL"}
                    and isinstance(summary.get("passed"), bool)
                )
                story_sha_match = bool(
                    legal_review and story.is_file()
                    and sha256_file(story).lower() == str(review.get("story_sha256") or "").lower()
                )
                board_sha_match = bool(
                    legal_review and board.is_file()
                    and sha256_file(board).lower() == str(review.get("storyboard_sha256") or "").lower()
                )
                current_state = state.get("current_state")
                safe_state = current_state in {"IDEA_LOCKED", "STORYBOARD_LOCKED"}
                rows.append({
                    "episode": episode.relative_to(ROOT).as_posix(),
                    "state": current_state,
                    "review_decision": review_decision or None,
                    "story_sha_match": story_sha_match,
                    "storyboard_sha_match": board_sha_match,
                    "safe_read_only_state": safe_state,
                    "eligible": bool(legal_review and story_sha_match and board_sha_match and safe_state),
                })
            except Exception as exc:
                rows.append({
                    "episode": episode.relative_to(ROOT).as_posix(),
                    "state": None, "review_decision": None,
                    "story_sha_match": False, "storyboard_sha_match": False,
                    "safe_read_only_state": False, "eligible": False,
                    "error_class": type(exc).__name__,
                })
    except Exception as exc:
        persistence_error = {"class": type(exc).__name__, "detail": str(exc)}
    return {
        "schema_version": 1,
        "kind": "p3_story_semantic_real_smoke_episode_candidates",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "persistence_status": "AVAILABLE" if persistence_error is None else "PERSISTENCE_UNAVAILABLE",
        "persistence_error": persistence_error,
        "candidates": rows,
        "selected": next((row["episode"] for row in rows if row.get("eligible")), None),
        "image_generation_invoked": False,
    }


def _write_immutable(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _unused_report_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    index = 1
    while True:
        candidate = path.with_name(f"{stem}-retry{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", help="target Episode path relative to repository")
    args = parser.parse_args()
    episode = Path(args.episode)
    if not episode.is_absolute():
        episode = ROOT / episode
    report, recoveries = audit_episode(episode)
    if report["source_set_status"] == "RECOVERABLE_EXACT" and not (
        report["story_match"] and report["storyboard_match"]
    ):
        bundle = _bundle_exact_sources(
            episode.resolve(), recoveries["story"], recoveries["storyboard"],
            report["review_story_sha256"], report["review_storyboard_sha256"],
        )
        report["historical_frozen_source_bundle"] = bundle.relative_to(ROOT).as_posix()
    report.pop("_canonical_before_hashes", None)
    report.pop("_review_after_hash", None)
    report.pop("_state_after", None)
    path = _unused_report_path(ROOT / "reports/p3-story-semantic-frozen-source-audit-20260927.json")
    _write_immutable(path, report)
    if report["source_set_status"] != "RECOVERABLE_EXACT":
        candidates = scan_candidate_episodes()
        candidate_path = _unused_report_path(
            ROOT / "reports/p3-story-semantic-real-smoke-episode-candidates-20260927.json"
        )
        _write_immutable(candidate_path, candidates)
        print(json.dumps({
            "source_set_status": report["source_set_status"],
            "audit_report": path.relative_to(ROOT).as_posix(),
            "candidate_report": candidate_path.relative_to(ROOT).as_posix(),
            "selected_episode": candidates.get("selected"),
            "persistence_status": candidates.get("persistence_status"),
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "source_set_status": report["source_set_status"],
            "audit_report": path.relative_to(ROOT).as_posix(),
            "historical_frozen_source_bundle": report.get("historical_frozen_source_bundle"),
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
