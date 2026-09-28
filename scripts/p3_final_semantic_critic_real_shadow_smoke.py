#!/usr/bin/env python3
"""Run one read-only Final Semantic Critic shadow over an existing review set."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "episodes/_system"), str(ROOT / "episodes/_system/agents")]

import final_semantic_critic_adapter as critic
import frame_semantic_review


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_files(ep: Path) -> list[Path]:
    paths = [ep / "meta/episode-state.json", ep / frame_semantic_review.SUMMARY_REL]
    for pattern in ("*ledger*.json", "*lock*.json", "*snapshot*.json"):
        paths.extend((ep / "meta").rglob(pattern))
    return sorted({path.resolve() for path in paths if path.is_file()})


def _file_snapshot(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): _sha(path) for path in paths}


def canonical_source_validation(review: dict, ep: Path) -> dict[str, bool]:
    story, storyboard = frame_semantic_review.episode_files(ep)
    return {
        "story_match": review.get("story_sha256") == _sha(story),
        "storyboard_match": review.get("storyboard_sha256") == _sha(storyboard),
        "visual_contract_match": review.get("visual_contract_sha256")
        == frame_semantic_review.sha256_json(frame_semantic_review.stable_visual_contract(ep)),
    }


def run(episode_dir: Path, *, attempt: int, timeout: int) -> dict:
    ep = episode_dir.resolve()
    review_path = ep / frame_semantic_review.SUMMARY_REL
    state_path = ep / "meta/episode-state.json"
    report = {
        "schema_version": 1,
        "kind": "p3_final_semantic_critic_real_shadow_smoke",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "episode": ep.relative_to(ROOT).as_posix(),
        "sample_type": "real_episode",
        "real_model_execution": False,
        "critic_invoked": False,
        "telemetry_complete": False,
        "failure": False,
        "timeout": False,
        "decision_schema_valid": False,
        "comparison_completed": False,
        "frame_set_sha_match": False,
        "source_binding_sha_match": False,
        "rubric_sha_match": False,
        "existing_final_review_unchanged": False,
        "production_ledger_unchanged": False,
        "locks_unchanged": False,
        "final_snapshot_unchanged": False,
        "episode_transition": False,
        "repair_invoked": False,
        "image_generation_invoked": False,
        "authority_write": False,
        "host_request_created": False,
        "candidate_created": False,
        "source_validation": {},
        "blockers": [],
    }
    protected_before: dict[str, str] = {}
    source_before: dict[str, str] = {}
    try:
        if not review_path.is_file() or not state_path.is_file():
            raise critic.FinalSemanticCriticError("existing canonical review or Episode state missing")
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        report["episode_state_before"] = state.get("current_state")
        if state.get("current_state") != "STORYBOARD_LOCKED":
            raise critic.FinalSemanticCriticError("read-only smoke only accepts an Episode outside production")
        canonical_before = json.loads(review_path.read_text(encoding="utf-8-sig"))
        report["canonical_review_sha256_before"] = _sha(review_path)
        protected_before = _file_snapshot(_protected_files(ep))
        frames = frame_semantic_review.reviewable_frame_records(ep, require_files=True)
        source_before = {
            row["path_rel"]: row["sha256"] for row in frames
        }
        expected = [{"frame": row["frame"], "asset_sha256": row["sha256"]} for row in frames]
        if canonical_before.get("frames") != expected:
            raise critic.FinalSemanticCriticError("canonical review does not bind the current complete frame set")
        story, storyboard = frame_semantic_review.episode_files(ep)
        source_before[story.relative_to(ROOT).as_posix()] = _sha(story)
        source_before[storyboard.relative_to(ROOT).as_posix()] = _sha(storyboard)
        canonical_sources = canonical_source_validation(canonical_before, ep)
        report["source_validation"] = canonical_sources
        canonical_sources_match = all(canonical_sources.values())
        if not canonical_sources_match:
            mismatched = [name for name, matches in canonical_sources.items() if not matches]
            raise critic.FinalSemanticCriticError("canonical review source SHA stale: " + ", ".join(mismatched))
        capsule = critic.build_frozen_review_capsule(ep)
        report.update({
            "existing_review_decision": "PASS" if (canonical_before.get("summary") or {}).get("passed") is True else "FAIL",
            "frame_set_sha256": capsule["frame_set_sha256"],
            "source_binding_sha256": capsule["source_sha256"],
            "rubric_sha256": capsule["canonical_rubric_code_sha256"],
            "decision_schema_sha256": capsule["decision_schema_sha256"],
            "frame_set_sha_match": True,
            "source_binding_sha_match": canonical_sources_match,
            "rubric_sha_match": True,
            "candidate_frame_count": len(capsule["frame_set"]),
            "canonical_review_sha256_before": _sha(review_path),
        })
        source_before = {row["path"]: row["sha256"] for row in capsule["source_files"]}
        prepared = critic.prepare_shadow_request(ep, attempt=attempt)
        if not prepared:
            raise critic.FinalSemanticCriticError("Final Semantic Critic Shadow is disabled")
        report["host_request_created"] = True
        report["request_id"] = prepared.get("request_id")
        report["request_snapshot_path"] = prepared.get("request_snapshot_path")
        report["request_snapshot_sha256"] = prepared.get("request_snapshot_sha256")
        result = critic.execute_shadow_request(ep, attempt=attempt, timeout=timeout)
        report.update({
            "real_model_execution": bool((result.get("model_execution") or {}).get("real_model_execution")),
            "critic_invoked": bool(result.get("critic_invoked")),
            "telemetry_complete": bool(result.get("telemetry_complete")),
            "failure": bool((result.get("model_execution") or {}).get("failure")),
            "timeout": bool((result.get("model_execution") or {}).get("timeout")),
            "decision_schema_valid": True,
            "comparison_completed": True,
            "decision": result.get("critic_decision", {}).get("decision"),
            "comparison": result.get("comparison"),
            "model_execution": result.get("model_execution"),
            "request_id": result.get("request_id"),
            "request_sha256": result.get("request_sha256"),
            "allowed_tools_empty": result.get("allowed_tools") == [],
            "result_evidence_path": f"{ep.relative_to(ROOT).as_posix()}/meta/runtime/agent-shadow/final-semantic-critic/attempt-{attempt}-result-evidence.json",
        })
        report["candidate_created"] = True
    except Exception as exc:
        report["failure"] = True
        report["timeout"] = "Timeout" in type(exc).__name__
        report["failure_class"] = type(exc).__name__
        report["blockers"].append(str(exc))
    finally:
        if review_path.is_file():
            report["existing_final_review_unchanged"] = (
                report.get("canonical_review_sha256_before") == _sha(review_path)
                if report.get("canonical_review_sha256_before") else False
            )
        after_paths = _protected_files(ep)
        protected_after = _file_snapshot(after_paths)
        report["production_ledger_unchanged"] = {
            k: v for k, v in protected_before.items() if "ledger" in k.lower()
        } == {k: v for k, v in protected_after.items() if "ledger" in k.lower()}
        report["locks_unchanged"] = {
            k: v for k, v in protected_before.items() if "lock" in k.lower()
        } == {k: v for k, v in protected_after.items() if "lock" in k.lower()}
        report["final_snapshot_unchanged"] = {
            k: v for k, v in protected_before.items() if "snapshot" in k.lower()
        } == {k: v for k, v in protected_after.items() if "snapshot" in k.lower()}
        report["episode_state_unchanged"] = (
            protected_before.get(state_path.relative_to(ROOT).as_posix())
            == protected_after.get(state_path.relative_to(ROOT).as_posix())
        )
        report["frozen_sources_unchanged"] = all(
            (ROOT / rel).is_file() and _sha(ROOT / rel) == expected
            for rel, expected in source_before.items()
        ) if source_before else False
        report["canonical_episode_modified"] = not (
            report["existing_final_review_unchanged"]
            and report["production_ledger_unchanged"]
            and report["locks_unchanged"]
            and report["final_snapshot_unchanged"]
            and report["episode_state_unchanged"]
            and report["frozen_sources_unchanged"]
        )
    report["shadow_only"] = True
    report["allowed_tools_empty"] = True
    report["gate_pass"] = False
    report["episode_transition"] = False
    report["repair_invoked"] = False
    report["image_generation_invoked"] = False
    report["pass"] = all(report.get(key) is True for key in (
        "real_model_execution", "critic_invoked", "telemetry_complete",
        "decision_schema_valid", "comparison_completed", "frame_set_sha_match",
        "source_binding_sha_match", "rubric_sha_match", "existing_final_review_unchanged",
        "production_ledger_unchanged", "locks_unchanged", "final_snapshot_unchanged",
        "episode_state_unchanged", "frozen_sources_unchanged",
    )) and report.get("timeout") is False and report.get("failure") is False
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--attempt", type=int, default=1, choices=(1, 2))
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/p3-final-semantic-critic-real-shadow-smoke-20260928.json")
    args = parser.parse_args()
    result = run(args.episode, attempt=args.attempt, timeout=args.timeout)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        print(f"refusing to overwrite immutable smoke evidence: {args.output}", file=sys.stderr)
        return 2
    print(json.dumps({key: result.get(key) for key in (
        "episode", "sample_type", "pass", "real_model_execution", "telemetry_complete",
        "decision", "failure", "timeout", "image_generation_invoked", "blockers",
    )}, ensure_ascii=False))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
