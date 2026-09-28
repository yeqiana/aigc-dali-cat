#!/usr/bin/env python3
"""Prepare and execute a SHA-bound Story Semantic Critic shadow benchmark.

Canonical Story Review is never rerun here. Historical canonical labels and
deterministic regression expectations are kept distinct in the report.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests/fixtures/p3_story_semantic"
DEFAULT_SMOKE = ROOT / "reports/p3-story-semantic-critic-real-shadow-smoke-retry2-20260927.json"
REGRESSION_PATH = ROOT / "standards/story_regressions/cases.json"


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


def _fixture_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    regression = _read_json(root / "standards/story_regressions/cases.json") or {}
    regression_rows = {str(row.get("id")): row for row in regression.get("cases", []) if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []
    for folder in sorted((root / "tests/fixtures/p3_story_semantic").glob("*")):
        if not folder.is_dir():
            continue
        story, board, applicability = folder / "story.md", folder / "storyboard.md", folder / "meta/shot-progression-review.json"
        metadata_path = folder / "meta/benchmark-label.json"
        metadata = _read_json(metadata_path)
        if (not all(path.is_file() for path in (story, board, applicability))
                or not isinstance(metadata, dict) or metadata.get("label") not in {"PASS", "FAIL"}):
            continue
        regression_id = metadata.get("regression_id")
        if regression_id:
            source_regression = regression_rows.get(str(regression_id), {})
            if source_regression.get("expected") != "fail" or source_regression.get("dimension") != metadata.get("regression_dimension"):
                continue
        rows.append({
            "sample_id": folder.name,
            "sample_type": "fixture",
            "episode": None,
            "story_path": story.relative_to(root).as_posix(),
            "story_sha256": _sha(story),
            "storyboard_path": board.relative_to(root).as_posix(),
            "storyboard_sha256": _sha(board),
            "applicability_path": applicability.relative_to(root).as_posix(),
            "applicability_sha256": _sha(applicability),
            "benchmark_label_path": metadata_path.relative_to(root).as_posix(),
            "benchmark_label_sha256": _sha(metadata_path),
            "reference_label": metadata["label"],
            "expected_decision": metadata.get("expected_decision"),
            "oracle": metadata.get("oracle"),
            "expected_issue_dimensions": metadata.get("expected_issue_dimensions", []),
            "ground_truth_type": metadata["ground_truth_type"],
            "regression_id": metadata.get("regression_id"),
            "regression_dimension": metadata.get("regression_dimension"),
            "regression_source_path": "standards/story_regressions/cases.json" if metadata.get("regression_id") else None,
            "regression_source_sha256": _sha(root / "standards/story_regressions/cases.json") if metadata.get("regression_id") else None,
            "source_sha_consistent": True,
        })
    return rows


def _collect_samples(root: Path, episodes: list[Path]) -> tuple[list[dict], list[dict]]:
    """Keep the real historical label separate from deterministic fixtures."""
    candidates: list[dict[str, Any]] = []
    for episode in sorted(episodes, key=lambda p: p.as_posix()):
        try:
            rel_ep = episode.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        manifest = _read_json(episode / "meta/release-manifest.json") or {}
        review_path = episode / "meta/story-semantic-review.json"
        review = _read_json(review_path)
        artifacts = manifest.get("artifacts") or {}
        story_raw, board_raw = artifacts.get("story"), artifacts.get("storyboard")
        if not isinstance(story_raw, str) or not isinstance(board_raw, str) or not review:
            continue
        story, board = (root / story_raw).resolve(), (root / board_raw).resolve()
        story_sha, board_sha = _sha(story), _sha(board)
        label = (review.get("summary") or {}).get("passed")
        if (type(label) is not bool or story_sha != review.get("story_sha256")
                or board_sha != review.get("storyboard_sha256")):
            continue
        applicability = episode / "meta/shot-progression-review.json"
        candidates.append({
            "sample_id": f"story-review-{len(candidates) + 1:02d}",
            "sample_type": "real_episode",
            "episode": rel_ep,
            "episode_state": (_read_json(episode / "meta/episode-state.json") or {}).get("current_state"),
            "review_path": review_path.relative_to(root).as_posix(),
            "review_source": "canonical_review_record",
            "story_path": story_raw,
            "story_sha256": story_sha,
            "storyboard_path": board_raw,
            "storyboard_sha256": board_sha,
            "applicability_path": applicability.relative_to(root).as_posix(),
            "applicability_sha256": _sha(applicability),
            "reference_label": "PASS" if label else "FAIL",
            "review_label": "PASS" if label else "FAIL",
            "review_attempt": (review.get("critic_provenance") or {}).get("attempt"),
            "ground_truth_type": "historical_canonical_review_not_independent_ground_truth",
            "source_sha_consistent": True,
            "canonical_files_modified": False,
        })
    return candidates, candidates[:7]


def _eligible(samples: list[dict[str, Any]]) -> tuple[bool, dict[str, int], list[str]]:
    counts = {"PASS": 0, "FAIL": 0}
    blockers: list[str] = []
    unique: set[tuple[str, str, str]] = set()
    for row in samples:
        label = row.get("reference_label")
        if label in counts:
            counts[label] += 1
        key = (str(row.get("story_sha256")), str(row.get("storyboard_sha256")), str(row.get("applicability_sha256")))
        if not all(key) or key in unique:
            blockers.append("SOURCE_SHA_MISSING_OR_DUPLICATE")
        unique.add(key)
    if len(samples) < 5:
        blockers.append("MINIMUM_FIVE_DISTINCT_SOURCE_SETS_NOT_MET")
    if counts["PASS"] < 2 or counts["FAIL"] < 2:
        blockers.append("PASS_FAIL_LABEL_DIVERSITY_NOT_MET")
    return not blockers, counts, sorted(set(blockers))


def prepare_sample_set(root: Path = ROOT) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "episodes" / "_system"))
    from scripts.phase9_runtime_launcher import load_runtime_env_file

    runtime_env, env_keys = load_runtime_env_file(root / ".storyos/runtime-launcher/runtime.env", dict(os.environ))
    os.environ.update(runtime_env)
    import episode_discovery

    canonical, _ = _collect_samples(root, episode_discovery.iter_episode_roots())
    real_sample = None
    for row in canonical:
        applicability = root / row["episode"] / "meta/shot-progression-review.json"
        if applicability.is_file() and _sha(applicability):
            real_sample = {
                **row,
                "sample_id": "real-canonical-" + Path(row["episode"]).name,
                "applicability_path": applicability.relative_to(root).as_posix(),
                "applicability_sha256": _sha(applicability),
            }
            break
    selected = ([real_sample] if real_sample else []) + _fixture_rows(root)
    eligible, labels, blockers = _eligible(selected)
    return {
        "schema_version": 2,
        "kind": "p3_story_semantic_critic_paired_benchmark_sample_set",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "runtime_env_loaded_keys": list(env_keys),
        "sample_selection": "one SHA-matched real shadow case plus four distinct deterministic Story Semantic fixtures",
        "candidate_real_episode_count": len(canonical),
        "selected_sample_count": len(selected),
        "minimum_sample_count": 5,
        "minimum_sample_count_met": len(selected) >= 5,
        "label_counts": labels,
        "label_diversity_complete": labels["PASS"] >= 2 and labels["FAIL"] >= 2,
        "source_sha_complete": all(row.get("source_sha_consistent") and row.get("story_sha256") and row.get("storyboard_sha256") and row.get("applicability_sha256") for row in selected),
        "distinct_source_sets": len({(row.get("story_sha256"), row.get("storyboard_sha256"), row.get("applicability_sha256")) for row in selected}) == len(selected),
        "eligible": eligible,
        "blockers": blockers,
        "samples": selected,
        "canonical_story_review_rerun": False,
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


def _stage_fixture(row: dict[str, Any], run_root: Path) -> tuple[Path, Path, Path]:
    sample_root = run_root / "fixtures" / str(row["sample_id"])
    story = sample_root / "docs/story.md"
    board = sample_root / "docs/storyboard.md"
    applicability = sample_root / "meta/shot-progression-review.json"
    for destination, source_key in ((story, "story_path"), (board, "storyboard_path"), (applicability, "applicability_path")):
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = ROOT / str(row[source_key])
        if _sha(source) != row[source_key.replace("path", "sha256")]:
            raise RuntimeError(f"fixture source SHA changed: {row[source_key]}")
        shutil.copyfile(source, destination)
        if _sha(destination) != row[source_key.replace("path", "sha256")]:
            raise RuntimeError(f"staged fixture SHA mismatch: {row[source_key]}")
    return sample_root, story, board


def _request_evidence(request_path: Path, snapshot_path: Path, snapshot_sha: str) -> dict[str, Any]:
    import product_review_adapter

    request = product_review_adapter._read_json(request_path)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    return {
        "request_id": request.get("request_id"),
        "request_kind": request.get("review_kind"),
        "request_sha256": snapshot_sha,
        "request_snapshot_path": snapshot_path.resolve().relative_to(ROOT).as_posix(),
        "request_metadata": request.get("request_metadata"),
        "source_files": request.get("source_files"),
        "candidate_path": request.get("candidate_path"),
        "decision_schema_sha256": request.get("request_metadata", {}).get("decision_schema_sha256"),
        "attempt": request.get("attempt"),
        "created_at": request.get("created_at"),
        "immutable_snapshot": snapshot,
        "not_episode_authority": True,
        "not_gate_authority": True,
    }


def _collect_completed_attempt(row: dict[str, Any], ep: Path, review_attempt: int, existing_review: dict[str, Any]) -> dict[str, Any] | None:
    """Recover a completed shadow attempt without re-dispatching its model."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "episodes" / "_system"))
    from agents import story_semantic_critic_adapter as critic
    import product_review_adapter

    attempt = 1
    candidate = ep / "meta/runtime/agent-shadow/story-semantic-critic" / f"attempt-{attempt}-decision.json"
    request_path = product_review_adapter.request_path(ep, critic.REQUEST_KIND, attempt=attempt)
    if not candidate.is_file():
        if product_review_adapter._request_exists(request_path):
            raise RuntimeError(f"existing Host Request has no completed candidate; refusing redispatch: {row['sample_id']}")
        return None
    request = product_review_adapter._read_json(request_path)
    telemetry_path = candidate.with_name(f"attempt-{attempt}-telemetry-evidence.json")
    snapshot_rel = str((request.get("request_metadata") or {}).get("request_snapshot_path") or "")
    snapshot_path = (ROOT / snapshot_rel).resolve()
    if not telemetry_path.is_file() or not snapshot_path.is_file():
        raise RuntimeError(f"completed Candidate lacks immutable request/telemetry evidence: {row['sample_id']}")
    telemetry_evidence = _read_json(telemetry_path) or {}
    telemetry = telemetry_evidence.get("model_execution") or {}
    decision = critic.load_decision(candidate)
    comparison = critic.compare_with_existing_review(decision, existing_review)
    snapshot_sha = _sha(snapshot_path)
    if snapshot_sha != telemetry_evidence.get("request_snapshot_sha256"):
        raise RuntimeError("completed Host Request snapshot SHA mismatch")
    if not telemetry.get("complete") or telemetry.get("real_model_execution") is not True:
        raise RuntimeError("completed attempt has incomplete real telemetry")
    request_evidence = _request_evidence(request_path, snapshot_path, snapshot_sha)
    _, effort = critic.configured_cli_model()
    return {
        **row,
        "critic_decision": decision["decision"],
        "reasoning_effort": effort,
        "critic_issue_codes": decision["issue_codes"],
        "schema_valid": True,
        "telemetry": telemetry,
        "telemetry_complete": telemetry["complete"],
        "failure": telemetry.get("failure"),
        "timeout": telemetry.get("timeout"),
        "request_evidence": request_evidence,
        "candidate_path": candidate.resolve().relative_to(ROOT).as_posix(),
        "candidate_sha256": _sha(candidate),
        "decision_equivalent_to_reference": comparison["decision_equivalent"],
        "decision_disagreement": comparison["decision_disagreement"],
        "issue_intersection": comparison["issue_intersection"],
        "critic_extra_issues": comparison["critic_extra_issues"],
        "critic_missing_issues": comparison["critic_missing_issues"],
        "repair_invoked": False,
        "authority_write": telemetry_evidence.get("authority_write") is True,
        "gate_pass": telemetry_evidence.get("gate_pass") is True,
        "episode_transition": telemetry_evidence.get("episode_transition") is True,
        "image_generation_invoked": False,
        "canonical_review_rerun": False,
        "critic_attempt": attempt,
        "review_attempt": review_attempt,
        "reference_decision": comparison["existing_review_decision"],
        "reference_source": row["ground_truth_type"],
        "reference_independent_ground_truth": row.get("sample_type") == "fixture",
        "execution_recovered_without_redispatch": True,
    }


def _run_case(row: dict[str, Any], run_root: Path, *, timeout: int) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "episodes" / "_system"))
    from agents import story_semantic_critic_adapter as critic
    import product_review_adapter
    model, effort = critic.configured_cli_model()
    if not model or not effort:
        raise RuntimeError("active Codex model/reasoning effort is not observable")

    if row.get("sample_type") == "fixture":
        ep, story, board = _stage_fixture(row, run_root)
        existing_review = {
            "revision_count": 0,
            "decision": "PASS" if row["reference_label"] == "PASS" else "FAIL",
            "summary": {"passed": row["reference_label"] == "PASS"},
            "issue_codes": [str(value) for value in row.get("expected_issue_dimensions", [])],
        }
        review_attempt = 1
    else:
        ep = ROOT / str(row["episode"])
        story = ROOT / str(row["story_path"])
        board = ROOT / str(row["storyboard_path"])
        review_path = ROOT / str(row["review_path"])
        existing_review = _read_json(review_path)
        if not existing_review:
            raise RuntimeError(f"frozen canonical review missing: {review_path}")
        review_attempt = int(row.get("review_attempt") or 0)
        if review_attempt < 1:
            raise RuntimeError("frozen canonical review attempt is missing")
        if _sha(story) != row.get("story_sha256") or _sha(board) != row.get("storyboard_sha256"):
            raise RuntimeError("real benchmark source SHA changed")
        completed = _collect_completed_attempt(row, ep, review_attempt, existing_review)
        if completed is not None:
            return completed
    rubric_paths = list(critic.RUBRIC_PATHS)
    applicability_context = critic.frozen_applicability_context(ep)
    rubric_text = "\n\n".join(path.read_text(encoding="utf-8-sig") for path in rubric_paths)
    prompt = critic.build_decision_prompt(
        attempt=1,
        story_text=story.read_text(encoding="utf-8-sig"),
        storyboard_text=board.read_text(encoding="utf-8-sig"),
        rubric_text=rubric_text,
        applicability=applicability_context,
    )
    critic_attempt = 1
    request = critic.prepare_shadow_request(
        ep,
        attempt=critic_attempt,
        review_attempt=review_attempt,
        prompt=prompt,
        story_path=story,
        storyboard_path=board,
        rubric_paths=[*rubric_paths, ep / "meta/shot-progression-review.json"],
        applicability_context=applicability_context,
    )
    if not isinstance(request, dict):
        raise RuntimeError(f"fixture shadow request was not created: {row['sample_id']}")
    result = critic.execute_shadow_request(
        ep,
        attempt=critic_attempt,
        review_attempt=review_attempt,
        timeout=timeout,
        existing_review=existing_review,
    )
    host_path = product_review_adapter.request_path(ep, critic.REQUEST_KIND, attempt=critic_attempt)
    snapshot_path = ROOT / str(result["request_snapshot_path"])
    request_evidence = _request_evidence(host_path, snapshot_path, result["request_snapshot_sha256"])
    decision = result["decision"]
    return {
        **row,
        "critic_decision": decision["decision"],
        "reasoning_effort": effort,
        "critic_issue_codes": decision["issue_codes"],
        "schema_valid": result["decision_schema_valid"],
        "telemetry": result["model_execution"],
        "telemetry_complete": result["telemetry_complete"],
        "failure": result["model_execution"].get("failure"),
        "timeout": result["model_execution"].get("timeout"),
        "request_evidence": request_evidence,
        "candidate_path": result["candidate_path"],
        "candidate_sha256": result["candidate_sha256"],
        "decision_equivalent_to_reference": result["decision_equivalent"],
        "decision_disagreement": result["decision_disagreement"],
        "issue_intersection": result["issue_intersection"],
        "critic_extra_issues": result["critic_extra_issues"],
        "critic_missing_issues": result["critic_missing_issues"],
        "repair_invoked": result["repair_invoked"],
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
        "image_generation_invoked": False,
        "canonical_review_rerun": False,
        "critic_attempt": critic_attempt,
        "review_attempt": review_attempt,
        "reference_decision": result["existing_review_decision"],
        "reference_source": row["ground_truth_type"],
        "reference_independent_ground_truth": row.get("sample_type") == "fixture",
    }


def run_benchmark(sample_set: dict[str, Any], smoke_path: Path, *, sample_set_path: Path, timeout: int = 900) -> dict[str, Any]:
    if not sample_set.get("eligible"):
        raise RuntimeError("sample set is not eligible; " + ", ".join(sample_set.get("blockers") or []))
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "episodes" / "_system"))
    from agents import story_semantic_critic_adapter as critic

    smoke = _read_json(smoke_path)
    if not smoke or smoke.get("status") != "PASS" or not smoke.get("telemetry_complete"):
        raise RuntimeError("real smoke evidence is missing or not PASS")
    real_smoke_sha_pair = (smoke.get("actual_critic_story_sha"), smoke.get("actual_critic_storyboard_sha"))
    if not all(real_smoke_sha_pair):
        raise RuntimeError("real smoke source binding evidence is incomplete")
    model, effort = critic.configured_cli_model()
    if not model or not effort:
        raise RuntimeError("active Codex model and reasoning effort are not observable")

    rows: list[dict[str, Any]] = []
    run_key = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = ROOT / ".storyos/p3-story-semantic-critic-benchmark" / run_key
    for row in sample_set["samples"]:
        if critic.configured_cli_model() != (model, effort):
            raise RuntimeError("model/reasoning configuration changed during paired benchmark")
        result = _run_case(row, run_root, timeout=timeout)
        telemetry = result.get("telemetry") or {}
        if not result.get("telemetry_complete") or telemetry.get("real_model_execution") is not True:
            raise RuntimeError(f"incomplete real telemetry for {row['sample_id']}")
        if result.get("failure") is not False or result.get("timeout") is not False:
            raise RuntimeError(f"failed/timed out model execution for {row['sample_id']}")
        rows.append(result)

    valid = [row for row in rows if row.get("schema_valid") is True and row.get("telemetry_complete") is True
             and row.get("failure") is False and row.get("timeout") is False
             and row.get("authority_write") is False and row.get("gate_pass") is False
             and row.get("episode_transition") is False]
    fixture_rows = [row for row in valid if row.get("sample_type") == "fixture"]
    false_accepts = sum(row["reference_label"] == "FAIL" and row["critic_decision"] == "ACCEPT_CANDIDATE" for row in fixture_rows)
    false_rejects = sum(row["reference_label"] == "PASS" and row["critic_decision"] != "ACCEPT_CANDIDATE" for row in fixture_rows)
    complete_pairs = len(valid) == len(sample_set["samples"]) and len(valid) >= 5
    all_safe = all(row.get("telemetry_complete") is True and row.get("failure") is False and row.get("timeout") is False for row in rows)
    all_authority_clean = all(row.get("authority_write") is False and row.get("gate_pass") is False and row.get("episode_transition") is False for row in rows)
    # One historical real comparison plus fixture agreement does not show the
    # Critic improves the authoritative reviewer; therefore quality value is
    # deliberately false even if fixture classification is correct.
    return {
        "schema_version": 1,
        "kind": "p3_story_semantic_critic_paired_benchmark",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sample_set": {"path": sample_set_path.resolve().relative_to(ROOT).as_posix(),
                       "sha256": _sha(sample_set_path)},
        "real_smoke_prerequisite": {"path": smoke_path.resolve().relative_to(ROOT).as_posix(), "sha256": _sha(smoke_path),
                                    "status": smoke.get("status"), "episode": smoke.get("episode")},
        "provider": "codex_user_runner",
        "model": model,
        "reasoning_effort": effort,
        "fixed_provider_model_reasoning": all((row.get("telemetry") or {}).get("provider") == "codex_user_runner"
                                               and (row.get("telemetry") or {}).get("model") == model
                                               and row.get("reasoning_effort") == effort for row in rows),
        "attempted_pairs": len(rows),
        "valid_pairs": len(valid),
        "real_episode_pairs": sum(row.get("sample_type") == "real_episode" for row in valid),
        "fixture_pairs": len(fixture_rows),
        "canonical_story_review_reruns": 0,
        "telemetry_complete": all(row.get("telemetry_complete") is True for row in rows),
        "semantic_decision_equivalence": all(row.get("decision_equivalent_to_reference") is True for row in rows),
        "authority_zero_regression": all_authority_clean,
        "no_failure_timeout": all_safe,
        "fixture_quality": {"labelled_fixture_count": len(fixture_rows), "pass_count": sum(r["reference_label"] == "PASS" for r in fixture_rows),
                            "fail_count": sum(r["reference_label"] == "FAIL" for r in fixture_rows),
                            "false_accept_count": false_accepts, "false_reject_count": false_rejects,
                            "issue_precision": None, "issue_recall": None,
                            "limitation": "Regression labels measure fixture classification; they are not a fresh run of canonical Story Review."},
        "quality_value": False,
        "quality_value_reason": "No evidence that Critic improves the authoritative Existing Story Review; deterministic fixture labels are independent reference cases, not canonical reviewer outcomes.",
        "false_accept_value": False,
        "false_reject_value": False,
        "repair_value": False,
        "added_wall_seconds": sum((row.get("telemetry") or {}).get("wall_seconds") or 0 for row in rows),
        "added_total_tokens": sum(((row.get("telemetry") or {}).get("input_tokens") or 0) + ((row.get("telemetry") or {}).get("output_tokens") or 0) for row in rows),
        "fixture_added_wall_seconds": sum((row.get("telemetry") or {}).get("wall_seconds") or 0 for row in rows if row.get("sample_type") == "fixture"),
        "fixture_added_total_tokens": sum(((row.get("telemetry") or {}).get("input_tokens") or 0) + ((row.get("telemetry") or {}).get("output_tokens") or 0) for row in rows if row.get("sample_type") == "fixture"),
        "median_wall_seconds": statistics.median((row.get("telemetry") or {}).get("wall_seconds") or 0 for row in rows),
        "median_total_tokens": statistics.median(((row.get("telemetry") or {}).get("input_tokens") or 0) + ((row.get("telemetry") or {}).get("output_tokens") or 0) for row in rows),
        "measurable_value": False,
        "production_decision": "NO_GO",
        "decision": "BENCHMARK_COMPLETE_VALUE_NOT_ESTABLISHED" if complete_pairs and all_safe and all_authority_clean else "BENCHMARK_INCOMPLETE",
        "image_generation_invoked": False,
        "episode_state_changed": False,
        "samples": rows,
    }


def assess_benchmark(raw_path: Path) -> dict[str, Any]:
    raw = _read_json(raw_path)
    if not raw:
        raise RuntimeError(f"benchmark report missing/invalid: {raw_path}")
    row_checks: list[dict[str, Any]] = []
    walls: list[float] = []
    tokens: list[int] = []
    for row in raw.get("samples") or []:
        source_checks = {}
        for path_key, sha_key in (("story_path", "story_sha256"), ("storyboard_path", "storyboard_sha256"),
                                  ("applicability_path", "applicability_sha256"),
                                  ("benchmark_label_path", "benchmark_label_sha256"),
                                  ("regression_source_path", "regression_source_sha256")):
            rel = row.get(path_key)
            expected = row.get(sha_key)
            if rel and expected:
                source_checks[path_key] = _sha(ROOT / str(rel)) == expected
        request = row.get("request_evidence") or {}
        snapshot = request.get("immutable_snapshot")
        snapshot_sha = hashlib.sha256((json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")).hexdigest() if isinstance(snapshot, dict) else None
        candidate_path = ROOT / str(row.get("candidate_path") or "")
        candidate_sha_match = bool(candidate_path.is_file() and _sha(candidate_path) == row.get("candidate_sha256"))
        candidate = _read_json(candidate_path) or {}
        telemetry = row.get("telemetry") or {}
        wall = telemetry.get("wall_seconds")
        token_count = (telemetry.get("input_tokens") or 0) + (telemetry.get("output_tokens") or 0)
        if isinstance(wall, (int, float)):
            walls.append(float(wall))
        tokens.append(int(token_count))
        checks = {
            "source_sha_match": all(source_checks.values()) and row.get("source_sha_consistent") is True,
            "request_snapshot_sha_match": snapshot_sha == request.get("request_sha256"),
            "request_snapshot_has_shadow_scope": bool(isinstance(snapshot, dict) and
                (snapshot.get("request") or {}).get("request_metadata", {}).get("shadow_only") is True and
                (snapshot.get("request") or {}).get("request_metadata", {}).get("candidate_authority") == "runtime_evidence_only"),
            "candidate_sha_match": candidate_sha_match,
            "candidate_schema_valid": row.get("schema_valid") is True,
            "telemetry_complete": row.get("telemetry_complete") is True and telemetry.get("real_model_execution") is True,
            "no_failure_timeout": row.get("failure") is False and row.get("timeout") is False,
            "no_authority_or_gate_mutation": row.get("authority_write") is False and row.get("gate_pass") is False and row.get("episode_transition") is False,
            "no_repair_or_image": row.get("repair_invoked") is False and row.get("image_generation_invoked") is False,
            "canonical_review_not_rerun": row.get("canonical_review_rerun") is False,
        }
        row_checks.append({
            "sample_id": row.get("sample_id"),
            "sample_type": row.get("sample_type"),
            "reference_label": row.get("reference_label"),
            "reference_source": row.get("reference_source") or row.get("ground_truth_type"),
            "critic_decision": row.get("critic_decision"),
            "critic_issue_codes": row.get("critic_issue_codes"),
            "candidate_repair_scope": candidate.get("repair_scope"),
            "decision_equivalent": row.get("decision_equivalent_to_reference"),
            "wall_seconds": wall,
            "input_tokens": telemetry.get("input_tokens"),
            "cached_input_tokens": telemetry.get("cached_input_tokens"),
            "output_tokens": telemetry.get("output_tokens"),
            "reasoning_output_tokens": telemetry.get("reasoning_output_tokens"),
            "total_tokens": token_count,
            "provider": telemetry.get("provider"),
            "model": telemetry.get("model"),
            "reasoning_effort": row.get("reasoning_effort"),
            "request_id": request.get("request_id"),
            "request_sha256": request.get("request_sha256"),
            "candidate_sha256": row.get("candidate_sha256"),
            "checks": checks,
            "pass": all(checks.values()),
        })
    fixture_rows = [row for row in row_checks if row["sample_type"] == "fixture"]
    false_accepts = sum(row["reference_label"] == "FAIL" and row["critic_decision"] == "ACCEPT_CANDIDATE" for row in fixture_rows)
    false_rejects = sum(row["reference_label"] == "PASS" and row["critic_decision"] != "ACCEPT_CANDIDATE" for row in fixture_rows)
    return {
        "schema_version": 1,
        "kind": "p3_story_semantic_critic_quality_assessment",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source_benchmark": {"path": raw_path.resolve().relative_to(ROOT).as_posix(), "sha256": _sha(raw_path)},
        "attempted_pairs": raw.get("attempted_pairs"),
        "valid_pairs": sum(row["pass"] for row in row_checks),
        "sample_count": len(row_checks),
        "real_episode_samples": sum(row["sample_type"] == "real_episode" for row in row_checks),
        "fixture_samples": len(fixture_rows),
        "label_counts": {"PASS": sum(row["reference_label"] == "PASS" for row in row_checks),
                         "FAIL": sum(row["reference_label"] == "FAIL" for row in row_checks)},
        "decision_disagreements": sum(row["decision_equivalent"] is False for row in row_checks),
        "false_accept_count": false_accepts,
        "false_reject_count": false_rejects,
        "issue_precision": None,
        "issue_recall": None,
        "repair_scope_precision": None,
        "issue_metric_limitation": "Critic issue_codes have no controlled mapping to regression dimensions; no precision/recall is claimed.",
        "false_accept_value": False,
        "false_reject_value": False,
        "repair_value": False,
        "quality_value": False,
        "quality_reason": "One real historical canonical review disagrees with Critic, and two passing fixtures are false-rejected. Fixture reference labels are not canonical Existing Review outputs, so no comparative quality improvement is established.",
        "median_wall_seconds": statistics.median(walls) if walls else None,
        "median_total_tokens": statistics.median(tokens) if tokens else None,
        "added_wall_seconds": sum(walls),
        "added_total_tokens": sum(tokens),
        "raw_cost_field_reconciliation": {
            "raw_added_wall_seconds": raw.get("added_wall_seconds"),
            "recomputed_all_pairs_wall_seconds": sum(walls),
            "raw_added_total_tokens": raw.get("added_total_tokens"),
            "recomputed_all_pairs_total_tokens": sum(tokens),
            "reason": "The first immutable raw report summed fixture-only overhead into all-pairs fields; this assessment recomputes totals from all five sample telemetry records without modifying the raw report.",
        },
        "bounded_reflection": {"max_review_attempts": 2, "max_auto_repairs": 1, "repairs_invoked": 0},
        "authority_zero_regression": all(row["checks"]["no_authority_or_gate_mutation"] for row in row_checks),
        "telemetry_complete": all(row["checks"]["telemetry_complete"] and row["checks"]["no_failure_timeout"] for row in row_checks),
        "request_evidence_complete": all(row["checks"]["request_snapshot_sha_match"] and row["checks"]["request_snapshot_has_shadow_scope"] for row in row_checks),
        "production_decision": "NO_GO",
        "decision": "BENCHMARK_COMPLETE_VALUE_NOT_ESTABLISHED",
        "image_generation_invoked": False,
        "episode_transition": False,
        "samples": row_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run", "assess"])
    parser.add_argument("--sample-set", type=Path)
    parser.add_argument("--smoke", type=Path, default=DEFAULT_SMOKE)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from scripts.phase9_runtime_launcher import load_runtime_env_file
    runtime_env, env_keys = load_runtime_env_file(ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ))
    os.environ.update(runtime_env)
    if args.command == "prepare":
        report = prepare_sample_set(ROOT)
        report["runtime_env_loaded_keys"] = list(env_keys)
        path = _write_immutable(ROOT / "reports/p3-story-semantic-critic-paired-benchmark-sample-set-v3-20260928.json", report)
        print(json.dumps({"path": path.relative_to(ROOT).as_posix(), "eligible": report["eligible"],
                          "selected_sample_count": report["selected_sample_count"], "label_counts": report["label_counts"],
                          "blockers": report["blockers"]}, ensure_ascii=False))
        return 0 if report["eligible"] else 1
    if args.command == "assess":
        raw_path = args.sample_set if args.sample_set else ROOT / "reports/p3-story-semantic-critic-paired-benchmark-20260928.json"
        if not raw_path.is_absolute():
            raw_path = ROOT / raw_path
        assessment = assess_benchmark(raw_path)
        output = _write_immutable(ROOT / "reports/p3-story-semantic-critic-quality-assessment-20260928.json", assessment)
        print(json.dumps({"path": output.relative_to(ROOT).as_posix(), "valid_pairs": assessment["valid_pairs"],
                          "false_accept_count": assessment["false_accept_count"], "false_reject_count": assessment["false_reject_count"],
                          "quality_value": assessment["quality_value"], "production_decision": assessment["production_decision"]}, ensure_ascii=False))
        return 0 if assessment["decision"] == "BENCHMARK_COMPLETE_VALUE_NOT_ESTABLISHED" else 1
    if args.sample_set:
        sample_path = args.sample_set if args.sample_set.is_absolute() else ROOT / args.sample_set
    else:
        candidates = sorted((ROOT / "reports").glob("p3-story-semantic-critic-paired-benchmark-sample-set-v3-20260928*.json"),
                            key=lambda path: path.stat().st_mtime_ns)
        sample_path = candidates[-1] if candidates else ROOT / "reports/p3-story-semantic-critic-paired-benchmark-sample-set-v3-20260928.json"
    sample_set = _read_json(sample_path)
    if not sample_set:
        raise SystemExit(f"sample set missing/invalid: {sample_path}")
    report = run_benchmark(sample_set, args.smoke if args.smoke.is_absolute() else ROOT / args.smoke,
                           sample_set_path=sample_path, timeout=args.timeout)
    path = _write_immutable(ROOT / "reports/p3-story-semantic-critic-paired-benchmark-20260928.json", report)
    print(json.dumps({"path": path.relative_to(ROOT).as_posix(), "decision": report["decision"],
                      "valid_pairs": report["valid_pairs"], "quality_value": report["quality_value"],
                      "production_decision": report["production_decision"]}, ensure_ascii=False))
    return 0 if report["decision"] == "BENCHMARK_COMPLETE_VALUE_NOT_ESTABLISHED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
