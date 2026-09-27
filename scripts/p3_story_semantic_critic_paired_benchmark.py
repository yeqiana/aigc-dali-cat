#!/usr/bin/env python3
"""Prepare a frozen, labelled Story Semantic Critic paired sample set.

This initial command is intentionally read-only and does not run either
reviewer. Paired execution is a separate later operation after sample review.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _sha(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_samples(root: Path, episodes: list[Path]) -> tuple[list[dict], list[dict]]:
    candidates: list[dict] = []
    seen_story_sha: set[str] = set()
    for episode in sorted(episodes, key=lambda p: p.as_posix()):
        try:
            rel_ep = episode.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        state_doc = _read_json(episode / "meta/episode-state.json") or {}
        manifest = _read_json(episode / "meta/release-manifest.json") or {}
        review_path = episode / "meta/story-semantic-review.json"
        review_source = "canonical_review_record"
        review = _read_json(review_path)
        if review is None:
            review_path = episode / "meta/runtime/review-exports/story-semantic.json"
            review = _read_json(review_path)
            review_source = "canonical_review_export"
        artifacts = manifest.get("artifacts") or {}
        story_raw, board_raw = artifacts.get("story"), artifacts.get("storyboard")
        if not isinstance(story_raw, str) or not isinstance(board_raw, str) or not isinstance(review, dict):
            continue
        story_path = (root / story_raw).resolve()
        board_path = (root / board_raw).resolve()
        try:
            story_path.relative_to(root.resolve())
            board_path.relative_to(root.resolve())
        except ValueError:
            continue
        story_sha, board_sha = _sha(story_path), _sha(board_path)
        story_bound = str(review.get("story_sha256") or "").lower()
        board_bound = str(review.get("storyboard_sha256") or "").lower()
        summary = review.get("summary") or {}
        label = summary.get("passed") if isinstance(summary, dict) else None
        provenance = review.get("critic_provenance") or {}
        source_exact = bool(story_sha and board_sha and story_sha == story_bound and board_sha == board_bound)
        valid_label = type(label) is bool and isinstance(provenance, dict) and bool(provenance)
        if not source_exact or not valid_label or story_sha in seen_story_sha:
            continue
        seen_story_sha.add(story_sha)
        candidates.append({
            "sample_id": f"story-review-{len(candidates) + 1:02d}",
            "episode": rel_ep,
            "episode_state": state_doc.get("current_state"),
            "review_path": review_path.relative_to(root).as_posix(),
            "review_source": review_source,
            "review_label": "PASS" if label is True else "FAIL",
            "ground_truth_type": "frozen_historical_authoritative_review",
            "story_path": story_raw,
            "story_sha256": story_sha,
            "storyboard_path": board_raw,
            "storyboard_sha256": board_sha,
            "review_attempt": provenance.get("attempt"),
            "reviewed_at": provenance.get("reviewed_at"),
            "source_sha_consistent": True,
            "canonical_files_modified": False,
            "image_generation_invoked": False,
        })
    selected = candidates[:7]
    return candidates, selected


def prepare_sample_set() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "episodes" / "_system"))
    from scripts.phase9_runtime_launcher import load_runtime_env_file

    runtime_env, env_keys = load_runtime_env_file(
        ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ)
    )
    os.environ.update(runtime_env)
    import episode_discovery

    candidates, selected = _collect_samples(ROOT, episode_discovery.iter_episode_roots())
    labels = {"PASS": 0, "FAIL": 0}
    for row in selected:
        labels[row["review_label"]] += 1
    return {
        "schema_version": 1,
        "kind": "p3_story_semantic_critic_paired_benchmark_sample_set",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "runtime_env_loaded_keys": list(env_keys),
        "sample_selection": "unique current Story and Storyboard SHA with a frozen canonical review label",
        "candidate_count": len(candidates),
        "selected_sample_count": len(selected),
        "minimum_sample_count": 5,
        "minimum_sample_count_met": len(selected) >= 5,
        "label_counts": labels,
        "label_diversity_complete": labels["PASS"] > 0 and labels["FAIL"] > 0,
        "quality_limitations": [
            "historical canonical review labels are the frozen benchmark labels, not independent new ground truth",
            "PASS-only sample sets cannot measure false-accept reduction; add a frozen FAIL-label case before claiming that value",
        ] if labels["FAIL"] == 0 else [
            "historical canonical review labels are frozen labels, not independent new ground truth",
        ],
        "samples": selected,
        "paired_run_started": False,
        "model_calls": 0,
        "host_requests_created": False,
        "image_generation_invoked": False,
    }


def _write_immutable(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path
    attempt = 0
    while True:
        try:
            with candidate.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            return candidate
        except FileExistsError:
            attempt += 1
            candidate = path.with_name(f"{path.stem}-retry{attempt}{path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare"])
    args = parser.parse_args()
    if args.command == "prepare":
        report = prepare_sample_set()
        path = _write_immutable(
            ROOT / "reports/p3-story-semantic-critic-paired-benchmark-sample-set-20260927.json",
            report,
        )
        print(json.dumps({
            "path": path.relative_to(ROOT).as_posix(),
            "selected_sample_count": report["selected_sample_count"],
            "label_counts": report["label_counts"],
            "paired_run_started": False,
        }, ensure_ascii=False))
        return 0 if report["minimum_sample_count_met"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
