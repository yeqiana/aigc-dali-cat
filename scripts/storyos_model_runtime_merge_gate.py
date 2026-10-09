#!/usr/bin/env python3
"""Read-only StoryOS model-runtime integration risk gate.

Compatible with git 2.34 (no newer merge-tree --write-tree requirement).
Never merges, updates refs, stages, stashes, resets, or touches production data.
This gate only assesses whether a SEPARATE integration rehearsal is reasonable.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAIN = "story-platform-v3-rever"
FEATURE = "feature/storyos-model-runtime-v1"
COMPANIONS = (
    "storyos-native-image-repair-20261008",
    "storyos-main-integration-20261009",
)
SAFE_REF = re.compile(r"^[A-Za-z0-9_.\/-]+$")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError("GIT_READ_FAILED: " + " ".join(args[:2]))
    return result


def names(repo: Path, base: str, other: str) -> set[str]:
    out = git(repo, "diff", "--name-only", base, other).stdout
    return set(out.decode("utf-8", "replace").splitlines()) - {""}


def canonical_main_worktree(repo: Path, branch: str) -> Path | None:
    out = git(repo, "worktree", "list", "--porcelain").stdout.decode("utf-8", "replace")
    for block in out.split("\n\n"):
        rows = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if rows.get("branch") == "refs/heads/" + branch and rows.get("worktree"):
            return Path(rows["worktree"])
    return None


def diff_conflicts(repo: Path, base: str, feature: str, companion: str, files: set[str]) -> list[dict]:
    """Three-way textual merge, in an OS TEMP directory only, never in Git worktrees."""
    problems = []
    for name in sorted(files):
        try:
            blobs = [git(repo, "show", rev + ":" + name).stdout
                     for rev in (feature, base, companion)]
        except RuntimeError:
            problems.append({"file": name, "kind": "missing_merge_blob"})
            continue
        with tempfile.TemporaryDirectory(prefix="storyos-merge-audit-") as scratch:
            paths = [Path(scratch) / x for x in ("ours", "base", "theirs")]
            for dest, raw in zip(paths, blobs):
                dest.write_bytes(raw)
            merged = subprocess.run(
                ["git", "merge-file", "--diff3", "-p",
                 *map(str, paths)],
                capture_output=True, check=False,
            )
            # git merge-file returns the NUMBER of conflict hunks (1..127).
            if merged.returncode != 0:
                markers = merged.stdout.count(b"<<<<<<< ")
                problems.append({"file": name,
                                 "kind": "content_conflict" if markers else "merge_error",
                                 "conflict_hunks": markers})
    return problems


def inspect(repo: Path, *, main: str = MAIN, feature: str = FEATURE,
            companions: tuple[str, ...] = COMPANIONS) -> dict:
    for ref in (main, feature, *companions):
        if not isinstance(ref, str) or not SAFE_REF.fullmatch(ref) or ref.startswith("-"):
            raise ValueError("UNSAFE_GIT_REF")
    for ref in (main, feature, *companions):
        git(repo, "rev-parse", "--verify", ref + "^{commit}")
    main_worktree = canonical_main_worktree(repo, main)
    if main_worktree is None:
        raise RuntimeError("MAIN_WORKTREE_NOT_FOUND")
    main_base = git(repo, "merge-base", main, feature).stdout.decode().strip()
    main_head = git(repo, "rev-parse", "--short", main).stdout.decode().strip()
    feature_head = git(repo, "rev-parse", "--short", feature).stdout.decode().strip()
    changed = names(repo, main_base, feature)
    main_dirty = git(main_worktree, "status", "--porcelain", "--untracked-files=normal").stdout
    main_dirty_entries = main_dirty.decode("utf-8", "replace").splitlines()
    main_tracked_modified = set(git(main_worktree, "diff", "--name-only").stdout.decode("utf-8", "replace").splitlines())
    main_staged_modified = set(git(main_worktree, "diff", "--cached", "--name-only").stdout.decode("utf-8", "replace").splitlines())
    overlaps = sorted(changed & (main_tracked_modified | main_staged_modified))
    companions_report = {}
    for comp in companions:
        common = git(repo, "merge-base", feature, comp).stdout.decode().strip()
        overlap = names(repo, common, feature) & names(repo, common, comp)
        companions_report[comp] = {
            "head": git(repo, "rev-parse", "--short", comp).stdout.decode().strip(),
            "shared_modified_files": len(overlap),
            "content_conflicts": diff_conflicts(repo, common, feature, comp, overlap),
        }
    blockers = []
    if main_dirty_entries:
        blockers.append("MAIN_WORKTREE_DIRTY")
    if overlaps:
        blockers.append("MAIN_UNCOMMITTED_FEATURE_OVERLAP")
    if any(row["content_conflicts"] for row in companions_report.values()):
        blockers.append("COMPANION_SEMANTIC_MERGE_REQUIRED")
    # This gate NEVER certifies full test coverage, model capability or Review Authority.
    # A clean conflict rehearsal is only a CANDIDATE, not a release approval.
    return {
        "schema_version": 1,
        "status": "NOT_READY_TO_MERGE_MAIN" if blockers else "REHEARSAL_CANDIDATE_ONLY",
        "main": main, "main_head": main_head,
        "feature": feature, "feature_head": feature_head,
        "main_worktree_dirty_entries": len(main_dirty_entries),
        "feature_changed_files": len(changed),
        "main_dirty_overlapping_files": overlaps,
        "companions": companions_report,
        "blockers": blockers,
        "requires_integration_full_regression": True,
        "production_cutover_verified": False,
        "model_capability_attested": False,
        "mysql_authority_e2e_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        outcome = inspect(args.repo.resolve())
    except (RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"status": "AUDIT_UNAVAILABLE",
                          "reason": str(exc).split(":")[0]}, ensure_ascii=False))
        return 3
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 2 if outcome["status"] == "NOT_READY_TO_MERGE_MAIN" else 0


if __name__ == "__main__":
    sys.exit(main())
