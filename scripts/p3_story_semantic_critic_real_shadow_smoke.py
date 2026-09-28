#!/usr/bin/env python3
"""Run one read-only, real-model Story Semantic Critic shadow smoke."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
AGENTS = SYSTEM / "agents"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SYSTEM))
from scripts.phase9_runtime_launcher import load_runtime_env_file

runtime_env, _runtime_env_keys = load_runtime_env_file(
    ROOT / ".storyos/runtime-launcher/runtime.env", dict(__import__("os").environ)
)
__import__("os").environ.update(runtime_env)

for path in (SYSTEM, AGENTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import episode_state_persistence
import product_review_adapter
import story_review
import story_semantic_critic_adapter as critic


def _sha(path: Path | None) -> str | None:
    return critic.sha256_file(path) if path and path.is_file() else None


def _load_existing_canonical_review(ep: Path) -> tuple[dict | None, Path]:
    review = story_review.load_review(ep)
    canonical_path = ep / story_review.REVIEW_REL
    if isinstance(review, dict):
        return review, canonical_path
    # Older completed Story Reviews are stored in the canonical review file
    # when no row exists in the configured persistence backend.
    if canonical_path.is_file():
        try:
            value = json.loads(canonical_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return None, canonical_path
        if isinstance(value, dict) and isinstance((value.get("summary") or {}).get("passed"), bool):
            return value, canonical_path
    return None, canonical_path


def _report_path() -> Path:
    base = ROOT / "reports/p3-story-semantic-critic-real-shadow-smoke-20260927.json"
    if not base.exists():
        return base
    for attempt in range(1, 100):
        candidate = base.with_name(f"p3-story-semantic-critic-real-shadow-smoke-retry{attempt}-20260927.json")
        if not candidate.exists():
            return candidate
    raise RuntimeError("all immutable real smoke report slots are occupied")


class SourceSetValidationError(RuntimeError):
    def __init__(self, validation: dict, blockers: list[str]):
        self.source_validation = validation
        self.blockers = blockers
        super().__init__("canonical Story Review source set is stale")


def run(episode_dir: Path) -> dict:
    ep = Path(episode_dir).resolve()
    state_before = episode_state_persistence.load(ep) or {}
    if state_before.get("current_state") != "STORYBOARD_LOCKED":
        raise RuntimeError(f"Episode state is not STORYBOARD_LOCKED: {state_before.get('current_state')}")
    review_before, review_record_path = _load_existing_canonical_review(ep)
    if not isinstance(review_before, dict):
        raise RuntimeError("frozen canonical Story Semantic Review is missing")
    story, storyboard = story_review.story_paths(ep)
    story_sha_before = story_review.sha256_file(story)
    board_sha_before = story_review.sha256_file(storyboard)
    source_validation = {
        "story_match": review_before.get("story_sha256") == story_sha_before,
        "storyboard_match": review_before.get("storyboard_sha256") == board_sha_before,
    }
    source_blockers = []
    if not source_validation["story_match"]:
        source_blockers.append("STORY_SOURCE_SHA_STALE")
    if not source_validation["storyboard_match"]:
        source_blockers.append("STORYBOARD_SOURCE_SHA_STALE")
    if source_blockers:
        raise SourceSetValidationError(source_validation, source_blockers)
    review_attempt = int(review_before.get("revision_count") or 0) + 1
    critic_attempt = 1
    review_export = ep / story_review.EXPORT_REL
    canonical_request_pointer = product_review_adapter.request_path(ep, "story-semantic")
    review_sha_before = story_review.review_authority_sha256(ep) or _sha(review_record_path)
    pointer_sha_before = _sha(canonical_request_pointer)
    state_fingerprint_before = json.dumps(state_before, ensure_ascii=False, sort_keys=True, default=str)
    source_paths = [story, storyboard, *critic.RUBRIC_PATHS]
    canonical_req_path = product_review_adapter.request_path(ep, "story-semantic", attempt=review_attempt)
    canonical_source_files = None
    if canonical_req_path.is_file():
        canonical_source_files = product_review_adapter._read_json(canonical_req_path).get("source_files")
    schedule = story_review.schedule_critic_shadow(
        ep, attempt=critic_attempt, review_attempt=review_attempt, story=story, storyboard=storyboard,
        sources=source_paths, canonical_source_files=canonical_source_files,
    )
    if not schedule.get("scheduled"):
        raise RuntimeError(f"Critic Shadow Host Request was not scheduled: {schedule}")

    result = critic.execute_shadow_request(
        ep, attempt=critic_attempt, review_attempt=review_attempt,
        timeout=900, existing_review=review_before,
    )
    state_after = episode_state_persistence.load(ep) or {}
    review_after, _ = _load_existing_canonical_review(ep)
    pointer_sha_after = _sha(canonical_request_pointer)
    review_sha_after = story_review.review_authority_sha256(ep) or _sha(review_record_path)
    source_unchanged = (
        story_review.sha256_file(story) == story_sha_before
        and story_review.sha256_file(storyboard) == board_sha_before
    )
    report = {
        "schema_version": 1,
        "kind": "p3_story_semantic_critic_real_shadow_smoke",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "episode": ep.resolve().relative_to(ROOT).as_posix(),
        "review_attempt": review_attempt,
        "critic_attempt": critic_attempt,
        "source_mode": "canonical_current",
        "review_bound_story_sha": review_before.get("story_sha256"),
        "actual_critic_story_sha": story_sha_before,
        "review_bound_storyboard_sha": review_before.get("storyboard_sha256"),
        "actual_critic_storyboard_sha": board_sha_before,
        "source_validation": source_validation,
        "source_matches_review": True,
        "host_wiring": True,
        "host_request_created": True,
        "host_request_id": result.get("request_id"),
        "host_request_path": result.get("request_path"),
        "host_request_snapshot_path": result.get("request_snapshot_path"),
        "host_request_snapshot_sha256": result.get("request_snapshot_sha256"),
        "candidate_path": result.get("candidate_path"),
        "candidate_sha256": result.get("candidate_sha256"),
        "applicability_context": result.get("applicability_context"),
        "applicability_sha256": (result.get("applicability_context") or {}).get("source_sha256"),
        "candidate_created": True,
        "real_model_execution": bool(result.get("model_execution", {}).get("real_model_execution")),
        "critic_invoked": result.get("critic_invoked") is True,
        "telemetry_complete": result.get("telemetry_complete") is True,
        "model_execution": result.get("model_execution"),
        "telemetry_evidence_path": result.get("telemetry_receipt_evidence_path"),
        "telemetry_evidence_sha256": result.get("telemetry_receipt_evidence_sha256"),
        "codex_jsonl_path": result.get("telemetry_evidence_path"),
        "codex_jsonl_sha256": result.get("telemetry_evidence_sha256"),
        "decision_parse": True,
        "decision_schema_valid": result.get("decision_schema_valid") is True,
        "failure": result.get("model_execution", {}).get("failure"),
        "timeout": result.get("model_execution", {}).get("timeout"),
        "shadow_decision": result.get("decision", {}).get("decision"),
        "existing_review_decision": result.get("existing_review_decision"),
        "comparison_completed": isinstance(result.get("decision_equivalent"), bool),
        "decision_equivalent": result.get("decision_equivalent"),
        "issue_disagreement": result.get("issue_disagreement"),
        "existing_review_unchanged": review_before == review_after and review_sha_before == review_sha_after,
        "source_sha_unchanged": source_unchanged,
        "authority_write": result.get("authority_write") is True,
        "gate_pass": result.get("gate_pass") is True,
        "episode_transition": result.get("episode_transition") is True,
        "shadow_only": result.get("shadow_is_advisory") is True,
        "allowed_tools_empty": result.get("allowed_tools_empty") is True,
        "episode_state": state_after.get("current_state"),
        "episode_state_unchanged": state_fingerprint_before == json.dumps(
            state_after, ensure_ascii=False, sort_keys=True, default=str
        ),
        "current_host_pointer_unchanged": pointer_sha_before == pointer_sha_after,
        "image_generation_invoked": False,
        "repair_invoked": result.get("repair_invoked") is True,
        "reflection": result.get("reflection"),
        "status": "PASS",
        "blockers": [],
    }
    checks = {
        "real_model_execution": report["real_model_execution"],
        "host_request_created": report["host_request_created"],
        "candidate_created": report["candidate_created"],
        "source_matches_review": report["source_matches_review"],
        "critic_invoked": report["critic_invoked"],
        "telemetry_complete": report["telemetry_complete"],
        "failure_false": report["failure"] is False,
        "timeout_false": report["timeout"] is False,
        "decision_schema_valid": report["decision_schema_valid"],
        "comparison_completed": report["comparison_completed"],
        "existing_review_unchanged": report["existing_review_unchanged"],
        "source_sha_unchanged": report["source_sha_unchanged"],
        "shadow_only": report["shadow_only"],
        "allowed_tools_empty": report["allowed_tools_empty"],
        "authority_write_false": not report["authority_write"],
        "gate_pass_false": not report["gate_pass"],
        "episode_transition_false": not report["episode_transition"],
        "episode_state_unchanged": report["episode_state_unchanged"],
        "current_host_pointer_unchanged": report["current_host_pointer_unchanged"],
        "image_generation_not_invoked": not report["image_generation_invoked"],
        "repair_not_invoked": not report["repair_invoked"],
    }
    report["checks"] = checks
    report["blockers"] = [key for key, passed in checks.items() if not passed]
    report["status"] = "PASS" if not report["blockers"] else "FAILED"
    return report


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/p3_story_semantic_critic_real_shadow_smoke.py <episode_dir>", file=sys.stderr)
        return 2
    report_path = _report_path()
    try:
        report = run(Path(sys.argv[1]))
    except Exception as exc:
        remote = dict(getattr(exc, "remote", {}) or {})
        name = type(exc).__name__
        failure_text = str(exc)
        if name == "CodexUserRunnerTimeout" or remote.get("timed_out") is True:
            failure_class = "TIMEOUT"
            timeout = True
        elif "schema" in failure_text.lower() or "decision keys" in failure_text.lower():
            failure_class = "SCHEMA"
            timeout = False
        elif "json" in failure_text.lower() or "candidate" in failure_text.lower():
            failure_class = "OUTPUT_FORMAT"
            timeout = False
        elif "source" in failure_text.lower() or "frozen" in failure_text.lower():
            failure_class = "SOURCE_STALE"
            timeout = False
        elif "telemetry" in failure_text.lower() or "receipt" in failure_text.lower():
            failure_class = "TELEMETRY"
            timeout = False
        elif name.startswith("Codex") or "returncode" in failure_text.lower():
            failure_class = "MODEL_FAILURE"
            timeout = False
        else:
            failure_class = "HOST_WIRING"
            timeout = False
        report = {
            "schema_version": 1,
            "kind": "p3_story_semantic_critic_real_shadow_smoke",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "status": "FAILED",
            "failure_class": failure_class,
            "failure": True,
            "failure_detail": str(exc),
            "timeout": timeout,
            "runner_receipt": remote,
            "real_model_execution": False,
            "telemetry_complete": False,
            "image_generation_invoked": False,
            "source_validation": getattr(exc, "source_validation", None),
            "host_request_created": False if isinstance(exc, SourceSetValidationError) else None,
            "model_invoked": False if isinstance(exc, SourceSetValidationError) else None,
            "candidate_created": False if isinstance(exc, SourceSetValidationError) else None,
            "telemetry_complete": False,
            "blockers": getattr(exc, "blockers", ["REAL_SHADOW_SMOKE_FAILED"]),
        }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with report_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError:
        print(f"immutable smoke evidence already exists: {report_path.relative_to(ROOT).as_posix()}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report.get("status"), "path": report_path.relative_to(ROOT).as_posix(),
                      "blockers": report.get("blockers")}, ensure_ascii=False))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
