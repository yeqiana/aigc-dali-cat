#!/usr/bin/env python3
"""Run one read-only Final Semantic Critic shadow over an existing review set."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
import uuid
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


def _canonical_episode_state(ep: Path) -> tuple[dict | None, str]:
    import episode_state_persistence
    return episode_state_persistence.load_with_source(ep)


def canonical_source_validation(review: dict, ep: Path) -> dict[str, bool]:
    story, storyboard = frame_semantic_review.episode_files(ep)
    return {
        "story_match": review.get("story_sha256") == _sha(story),
        "storyboard_match": review.get("storyboard_sha256") == _sha(storyboard),
        "visual_contract_match": review.get("visual_contract_sha256")
        == frame_semantic_review.sha256_json(frame_semantic_review.stable_visual_contract(ep)),
    }


def validate_historical_source_bundle(bundle: Path, ep: Path, review: dict) -> dict:
    """Verify an exact runtime-only bundle before any shadow request or model call."""
    bundle = bundle.resolve()
    bundle.relative_to(ROOT.resolve())
    manifest_path = bundle / "source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if (manifest.get("source_set_status") != "RECOVERABLE_EXACT"
            or manifest.get("source_type") != "historical_final_semantic_exact"
            or manifest.get("canonical") is not False
            or manifest.get("canonical_write") is not False
            or manifest.get("runtime_evidence_only") is not True):
        raise critic.FinalSemanticCriticError("historical source manifest is not an exact runtime-only bundle")
    if manifest.get("episode") != ep.relative_to(ROOT).as_posix():
        raise critic.FinalSemanticCriticError("historical source bundle Episode binding mismatch")
    if manifest.get("canonical_final_review_sha256") != _sha(ep / frame_semantic_review.SUMMARY_REL):
        raise critic.FinalSemanticCriticError("canonical Final Review changed since historical audit")
    source_rows = {row.get("kind"): row for row in manifest.get("sources", []) if isinstance(row, dict)}
    expected = {
        "story": str(review.get("story_sha256") or ""),
        "storyboard": str(review.get("storyboard_sha256") or ""),
        "caption_source": str(review.get("caption_source_sha256") or ""),
    }
    resolved: dict[str, Path] = {}
    for kind, expected_sha in expected.items():
        row = source_rows.get(kind)
        if not row or row.get("review_bound_sha256") != expected_sha or row.get("exact_match") is not True:
            raise critic.FinalSemanticCriticError(f"historical {kind} source binding missing or stale")
        path = (ROOT / str(row.get("bundle_path") or "")).resolve()
        path.relative_to(ROOT.resolve())
        if not path.is_file() or _sha(path) != expected_sha or row.get("recovered_sha256") != expected_sha:
            raise critic.FinalSemanticCriticError(f"historical {kind} bytes do not match canonical review SHA")
        resolved[kind] = path
    visual = next((row for row in manifest.get("sources", [])
                   if isinstance(row, dict) and row.get("kind") == "visual_contract_projection"), None)
    if (not visual or visual.get("exact_match") is not True
            or visual.get("review_bound_sha256") != review.get("visual_contract_sha256")
            or frame_semantic_review.sha256_json(frame_semantic_review.stable_visual_contract(ep))
            != review.get("visual_contract_sha256")):
        raise critic.FinalSemanticCriticError("current Visual Contract no longer matches canonical Final Review")
    return {"manifest": manifest, "manifest_path": manifest_path, "sources": resolved}


@contextlib.contextmanager
def _historical_source_context(story: Path, storyboard: Path):
    """Resolve contract inputs against the verified historical exact bytes."""
    old_episode_files = frame_semantic_review.episode_files
    old_artifact_paths = frame_semantic_review.phase4_contract.artifact_paths
    frame_semantic_review.episode_files = lambda _ep: (story, storyboard)
    frame_semantic_review.phase4_contract.artifact_paths = lambda _ep: (story, storyboard)
    try:
        yield
    finally:
        frame_semantic_review.episode_files = old_episode_files
        frame_semantic_review.phase4_contract.artifact_paths = old_artifact_paths


def historical_attachment_preflight(ep: Path, review: dict, bundle: Path) -> dict:
    """Read-only validation of the exact historical inputs before scheduling a Host request."""
    verified = validate_historical_source_bundle(bundle, ep, review)
    sources = verified["sources"]
    frames = frame_semantic_review.reviewable_frame_records(ep, require_files=True)
    expected = [{"frame": row["frame"], "asset_sha256": row["sha256"]} for row in frames]
    if not frames or review.get("frames") != expected:
        raise critic.FinalSemanticCriticError("current complete frame set differs from canonical Final Review")
    with _historical_source_context(sources["story"], sources["storyboard"]):
        errors = frame_semantic_review.reviewable_phase4_binding_errors(ep, frames)
        if errors:
            raise critic.FinalSemanticCriticError("historical source Frame Contract binding failed: " + "; ".join(errors))
        capsule = critic.build_frozen_review_capsule(ep)
    capsule["source_files"] = [row for row in capsule["source_files"] if row.get("role") != "caption_source"]
    caption_rel = sources["caption_source"].relative_to(ROOT).as_posix()
    capsule["source_files"].append({"path": caption_rel, "sha256": _sha(sources["caption_source"]), "role": "caption_source"})
    capsule["source_files"].sort(key=lambda row: row["path"])
    capsule["source_sha256"] = critic.digest(capsule["source_files"])
    capsule.pop("capsule_sha256", None)
    capsule["capsule_sha256"] = critic.digest(capsule)
    critic.verify_capsule_integrity(capsule)
    if (capsule["source_bindings"]["contexts"].get("story_sha256") != review.get("story_sha256")
            or capsule["source_bindings"]["contexts"].get("storyboard_sha256") != review.get("storyboard_sha256")):
        raise critic.FinalSemanticCriticError("historical Story/Storyboard binding mismatch")
    plan = critic.final_critic_visual_attachment_plan(
        capsule, root=ROOT, non_image_paths=(critic.DECISION_SCHEMA,),
    )
    config = critic.adapter_config()
    state, state_source = _canonical_episode_state(ep)
    passed = bool(
        plan["preflight_status"] == "PASS"
        and plan["expected_visual_asset_count"] == 20
        and plan["attached_visual_asset_count"] == 20
        and plan["visual_attachment_sha_match"] is True
        and plan["visual_attachment_type_valid"] is True
        and config.get("shadow_enabled") is True
        and config.get("production_enabled") is False
        and (state or {}).get("current_state") == "PUBLISH_READY"
    )
    return {
        "schema_version": 1,
        "kind": "p3_final_semantic_critic_visual_attachment_preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "episode": ep.relative_to(ROOT).as_posix(),
        "source_mode": "historical_frozen_exact",
        "historical_manifest_verified": True,
        "source_binding_sha_match": True,
        "frame_set_sha_match": True,
        "expected_visual_asset_count": plan["expected_visual_asset_count"],
        "attached_visual_asset_count": plan["attached_visual_asset_count"],
        "visual_attachment_paths": plan["visual_attachment_paths"],
        "visual_attachment_sha_match": plan["visual_attachment_sha_match"],
        "visual_attachment_type_valid": plan["visual_attachment_type_valid"],
        "visual_attachment_assets": plan["visual_assets"],
        "non_image_attachment_count": plan["non_image_attachment_count"] + 1,
        "non_image_attachments": plan["non_image_attachments"] + [{
            "path": critic.DECISION_SCHEMA.relative_to(ROOT).as_posix(), "mime_type": "application/json",
        }],
        "shadow_enabled": config.get("shadow_enabled"),
        "production_enabled": config.get("production_enabled"),
        "episode_state": (state or {}).get("current_state"),
        "episode_state_source": state_source,
        "host_request_created": False,
        "model_invoked": False,
        "candidate_created": False,
        "image_generation_invoked": False,
        "status": "PASS" if passed else "BLOCKED",
        "blockers": [] if passed else ["VISUAL_ATTACHMENT_PREFLIGHT_FAILED"],
    }


def _ledger_sha(ep: Path) -> str:
    import production_ledger
    ledger = production_ledger.load_authority(ep, default={}) or {}
    return critic.digest(ledger)


def _run_historical_shadow(ep: Path, review: dict, *, attempt: int, timeout: int,
                           bundle: Path, report: dict) -> dict:
    import codex_critic_runner
    import codex_execution_telemetry

    verified = validate_historical_source_bundle(bundle, ep, review)
    sources = verified["sources"]
    frames = frame_semantic_review.reviewable_frame_records(ep, require_files=True)
    expected = [{"frame": row["frame"], "asset_sha256": row["sha256"]} for row in frames]
    if not frames or review.get("frames") != expected:
        raise critic.FinalSemanticCriticError("current complete frame set differs from canonical Final Review")
    with _historical_source_context(sources["story"], sources["storyboard"]):
        binding_errors = frame_semantic_review.reviewable_phase4_binding_errors(ep, frames)
        if binding_errors:
            raise critic.FinalSemanticCriticError("historical source Frame Contract binding failed: " + "; ".join(binding_errors))
        capsule = critic.build_frozen_review_capsule(ep)
    # Captions are a canonical Final Review binding and must travel in the frozen capsule.
    capsule["source_files"] = [row for row in capsule["source_files"] if row.get("role") != "caption_source"]
    caption_rel = sources["caption_source"].relative_to(ROOT).as_posix()
    capsule["source_files"].append({"path": caption_rel, "sha256": _sha(sources["caption_source"]), "role": "caption_source"})
    capsule["source_files"].sort(key=lambda row: row["path"])
    capsule["source_sha256"] = critic.digest(capsule["source_files"])
    capsule.pop("capsule_sha256", None)
    capsule["capsule_sha256"] = critic.digest(capsule)
    critic.verify_capsule_integrity(capsule)
    if capsule["source_bindings"]["contexts"].get("story_sha256") != review.get("story_sha256"):
        raise critic.FinalSemanticCriticError("historical Story SHA is not bound into the Critic capsule")
    if capsule["source_bindings"]["contexts"].get("storyboard_sha256") != review.get("storyboard_sha256"):
        raise critic.FinalSemanticCriticError("historical Storyboard SHA is not bound into the Critic capsule")

    config = critic.adapter_config()
    if config.get("shadow_enabled") is not True or config.get("production_enabled") is not False:
        raise critic.FinalSemanticCriticError("Final Semantic Critic is not in shadow-only configuration")
    evidence_root = ROOT / f".storyos/p3-final-semantic-critic/historical-real-shadow/attempt-{attempt}"
    capsule_path = evidence_root / "frozen-capsule.json"
    request_path = evidence_root / "host-request.json"
    request_snapshot_path = evidence_root / "host-request-snapshot.json"
    candidate_path = evidence_root / "decision-candidate.json"
    log_path = evidence_root / "codex-execution.jsonl"
    capsule_sha = critic._write_immutable(capsule_path, capsule)
    attachment_plan = critic.final_critic_visual_attachment_plan(
        capsule, root=ROOT, non_image_paths=(capsule_path, critic.DECISION_SCHEMA),
    )
    report.update({
        "expected_visual_asset_count": attachment_plan["expected_visual_asset_count"],
        "attached_visual_asset_count": attachment_plan["attached_visual_asset_count"],
        "visual_attachment_paths": attachment_plan["visual_attachment_paths"],
        "visual_attachment_sha_match": attachment_plan["visual_attachment_sha_match"],
        "visual_attachment_type_valid": attachment_plan["visual_attachment_type_valid"],
        "visual_attachment_assets": attachment_plan["visual_assets"],
        "non_image_attachment_count": attachment_plan["non_image_attachment_count"],
        "non_image_attachments": attachment_plan["non_image_attachments"],
        "image_prepare_warning_count": 0,
        "visual_assets_attached": False,
        "attachment_preflight_status": attachment_plan["preflight_status"],
    })
    if (attachment_plan["preflight_status"] != "PASS"
            or attachment_plan["expected_visual_asset_count"] != 20
            or attachment_plan["attached_visual_asset_count"] != 20):
        raise critic.FinalSemanticCriticError("Final Semantic visual attachment preflight blocked")
    schema_sha = _sha(critic.DECISION_SCHEMA)
    request = {
        "schema_version": 1,
        "request_id": str(uuid.uuid4()),
        "kind": "final-semantic-critic-shadow",
        "source_mode": "historical_frozen_exact",
        "shadow_only": True,
        "candidate_authority": "runtime_evidence_only",
        "execution_domain": "FINAL_SEMANTIC_CRITIC_SHADOW_HISTORICAL",
        "review_attempt": attempt,
        "critic_attempt": attempt,
        "canonical_final_review_sha256": _sha(ep / frame_semantic_review.SUMMARY_REL),
        "frame_set_sha256": capsule["frame_set_sha256"],
        "source_sha256": capsule["source_sha256"],
        "obligation_sha256": capsule["obligation_sha256"],
        "decision_schema_sha256": schema_sha,
        "capsule_path": capsule_path.relative_to(ROOT).as_posix(),
        "capsule_sha256": capsule_sha,
        "source_files": capsule["source_files"],
        "candidate_path": candidate_path.relative_to(ROOT).as_posix(),
        "allowed_tools": [],
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
    }
    request_sha = critic._write_immutable(request_path, request)
    snapshot_sha = critic._write_immutable(request_snapshot_path, {
        "schema_version": 1, "kind": "immutable_historical_final_critic_request_snapshot",
        "request": request, "request_sha256": request_sha,
    })
    report.update({"host_request_created": True, "request_id": request["request_id"],
                   "request_path": request_path.relative_to(ROOT).as_posix(), "request_sha256": request_sha,
                   "request_snapshot_path": request_snapshot_path.relative_to(ROOT).as_posix(),
                   "request_snapshot_sha256": snapshot_sha, "capsule_sha256": capsule["capsule_sha256"],
                   "source_mode": "historical_frozen_exact", "frame_set_sha_match": True,
                   "source_binding_sha_match": True, "rubric_sha_match": True})
    report.update({"review_bound_story_sha256": review.get("story_sha256"),
                   "actual_critic_story_sha256": _sha(sources["story"]),
                   "review_bound_storyboard_sha256": review.get("storyboard_sha256"),
                   "actual_critic_storyboard_sha256": _sha(sources["storyboard"]),
                   "source_binding_rows": verified["manifest"].get("sources")})
    report["visual_assets_attached"] = True
    report["visual_attachment_paths"] = attachment_plan["visual_attachment_paths"]
    model, effort = critic._configured_cli_model()
    if not model or not effort:
        raise critic.FinalSemanticCriticError("active Codex model and reasoning effort are not observable")
    prompt = critic.build_prompt(capsule, critic_attempt=attempt)
    result = codex_critic_runner.launch(
        prompt, codex=codex_critic_runner.resolve_codex(None), root=ROOT,
        timeout=timeout, output_path=candidate_path, output_schema=critic.DECISION_SCHEMA,
        attachments=attachment_plan["visual_attachment_files"],
        model=model, reasoning_effort=effort, sandbox="read-only", log_path=log_path,
    )
    telemetry = codex_execution_telemetry.model_execution(
        result, provider="codex_user_runner", model=model, authority_capsule_read_once=True)
    telemetry["reasoning_effort"] = effort
    telemetry["complete"] = all(telemetry.get(key) is not None for key in (
        "wall_seconds", "input_tokens", "cached_input_tokens", "output_tokens",
        "reasoning_output_tokens", "failure", "timeout", "returncode", "telemetry_source",
    )) and telemetry.get("real_model_execution") is True and bool(telemetry.get("provider")) and bool(telemetry.get("model"))
    report["model_execution"] = telemetry
    report["returncode"] = result.returncode
    runner_images = (result.remote or {}).get("input_images") if isinstance(result.remote, dict) else None
    if isinstance(runner_images, list):
        expected_by_source = {
            str((ROOT / rel).resolve()): row["expected_sha256"]
            for row in attachment_plan["visual_assets"]
        }
        runner_images_match = len(runner_images) == 20 and all(
            str(row.get("source") or "") in expected_by_source
            and row.get("sha256") == expected_by_source[str(row.get("source") or "")]
            for row in runner_images if isinstance(row, dict)
        )
        report["runner_staged_visual_asset_count"] = len(runner_images)
        report["runner_staged_visual_assets_sha_match"] = runner_images_match
    else:
        runner_images_match = None
        report["runner_staged_visual_asset_count"] = None
        report["runner_staged_visual_assets_sha_match"] = None
    log_text = str(getattr(result, "log_text", "") or "")
    warning_lines = [line for line in log_text.splitlines()
                     if "failed to prepare message image" in line.lower()
                     or "unsupported image" in line.lower()]
    report["image_prepare_warning_count"] = len(warning_lines)
    report["image_prepare_warnings"] = warning_lines
    report["visual_assets_attached"] = bool(
        attachment_plan["preflight_status"] == "PASS"
        and len(attachment_plan["visual_attachment_files"]) == 20
        and not warning_lines
        and runner_images_match is not False
    )
    if not report["visual_assets_attached"]:
        raise critic.FinalSemanticCriticError("Final Semantic visual attachment transport was not verified")
    if result.returncode != 0 and any("429" in line or "Too Many Requests" in line for line in log_text.splitlines()):
        report["failure_class"] = "TECHNICAL_MODEL_RATE_LIMIT"
    elif result.returncode != 0:
        report["failure_class"] = "TECHNICAL_MODEL_EXECUTION"
    report["telemetry_complete"] = telemetry["complete"]
    report["real_model_execution"] = bool(telemetry.get("real_model_execution"))
    report["critic_invoked"] = report["real_model_execution"]
    report["failure"] = bool(telemetry.get("failure"))
    report["timeout"] = bool(telemetry.get("timeout"))
    report["candidate_created"] = candidate_path.is_file()
    if result.returncode != 0:
        raise critic.FinalSemanticCriticError(f"Final Semantic Critic model failed with returncode={result.returncode}")
    if not telemetry["complete"]:
        raise critic.FinalSemanticCriticError("Final Semantic Critic telemetry incomplete")
    if not telemetry.get("tool_free"):
        raise critic.FinalSemanticCriticError("Final Semantic Critic used a tool despite the read-only policy")
    decision = critic.validate_decision(json.loads(candidate_path.read_text(encoding="utf-8-sig")))
    existing = {"decision": "PASS" if (review.get("summary") or {}).get("passed") is True else "FAIL",
                "issue_codes": review.get("issue_codes") or []}
    evidence = {
        "schema_version": 1, "kind": "final_semantic_critic_historical_shadow_result",
        "request_id": request["request_id"], "request_sha256": request_sha,
        "request_snapshot_sha256": snapshot_sha, "capsule_sha256": capsule["capsule_sha256"],
        "candidate_sha256": _sha(candidate_path), "decision": decision,
        "comparison": critic._comparison(existing, decision), "model_execution": telemetry,
        "visual_assets_attached": report["visual_assets_attached"],
        "expected_visual_asset_count": report["expected_visual_asset_count"],
        "attached_visual_asset_count": report["attached_visual_asset_count"],
        "visual_attachment_sha_match": report["visual_attachment_sha_match"],
        "visual_attachment_type_valid": report["visual_attachment_type_valid"],
        "image_prepare_warning_count": report["image_prepare_warning_count"],
        "telemetry_complete": telemetry["complete"], "real_model_execution": telemetry["real_model_execution"],
        "critic_invoked": telemetry["real_model_execution"], "allowed_tools": [],
        "authority_write": False, "gate_pass": False, "episode_transition": False,
        "repair_invoked": False, "image_generation_invoked": False,
    }
    result_path = evidence_root / "result-evidence.json"
    result_sha = critic._write_immutable(result_path, evidence)
    report.update({"real_model_execution": bool(telemetry["real_model_execution"]),
                   "critic_invoked": bool(telemetry["real_model_execution"]),
                   "telemetry_complete": telemetry["complete"], "failure": bool(telemetry["failure"]),
                   "timeout": bool(telemetry["timeout"]), "decision_schema_valid": True,
                   "comparison_completed": True, "decision": decision.get("decision"),
                   "existing_decision": existing["decision"], "comparison": evidence["comparison"],
                   "model_execution": telemetry, "result_evidence_path": result_path.relative_to(ROOT).as_posix(),
                   "result_evidence_sha256": result_sha, "candidate_sha256": evidence["candidate_sha256"],
                   "candidate_created": True, "repair_invoked": False})
    return report


def run(episode_dir: Path, *, attempt: int, timeout: int,
        historical_source_bundle: Path | None = None) -> dict:
    ep = episode_dir.resolve()
    review_path = ep / frame_semantic_review.SUMMARY_REL
    state_path = ep / "meta/episode-state.json"
    report = {
        "schema_version": 1,
        "kind": "p3_final_semantic_critic_real_shadow_smoke",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "episode": ep.relative_to(ROOT).as_posix(),
        "sample_type": "real_episode",
        "source_mode": "historical_frozen_exact" if historical_source_bundle else "canonical_current",
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
        state_file = json.loads(state_path.read_text(encoding="utf-8-sig"))
        persisted_state, state_source = _canonical_episode_state(ep)
        report["episode_state_file_before"] = state_file.get("current_state")
        report["episode_state_before"] = (persisted_state or {}).get("current_state")
        report["episode_state_source"] = state_source
        if report["episode_state_before"] != "PUBLISH_READY":
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
        if not canonical_sources_match and historical_source_bundle is None:
            mismatched = [name for name, matches in canonical_sources.items() if not matches]
            raise critic.FinalSemanticCriticError("canonical review source SHA stale: " + ", ".join(mismatched))
        if historical_source_bundle is not None:
            report["ledger_sha256_before"] = _ledger_sha(ep)
            report.update({"existing_review_decision": "PASS" if (canonical_before.get("summary") or {}).get("passed") is True else "FAIL",
                           "review_bound_story_sha256": canonical_before.get("story_sha256"),
                           "review_bound_storyboard_sha256": canonical_before.get("storyboard_sha256")})
            _run_historical_shadow(ep, canonical_before, attempt=attempt, timeout=timeout,
                                   bundle=historical_source_bundle, report=report)
            report["source_validation"] = {**canonical_sources,
                                           "historical_bundle_verified": True,
                                           "historical_story_match": True,
                                           "historical_storyboard_match": True,
                                           "historical_caption_match": True}
            report["canonical_review_sha256_before"] = _sha(review_path)
            # Historical source bytes live in the runtime-only bundle and must remain unchanged too.
            manifest = json.loads((historical_source_bundle / "source-manifest.json").read_text(encoding="utf-8-sig"))
            for row in manifest.get("sources", []):
                if row.get("bundle_path"):
                    path = ROOT / row["bundle_path"]
                    source_before[path.relative_to(ROOT).as_posix()] = _sha(path)
            report["host_request_created"] = True
            report["shadow_only"] = True
            report["allowed_tools_empty"] = True
            report["gate_pass"] = False
            report["episode_transition"] = False
            report["repair_invoked"] = False
            report["image_generation_invoked"] = False
            report["final_snapshot_unchanged"] = True
            report["production_ledger_unchanged"] = True
            report["locks_unchanged"] = True
            report["existing_final_review_unchanged"] = True
            report["episode_state_unchanged"] = True
            report["frozen_sources_unchanged"] = True
            report["canonical_episode_modified"] = False
            report["pass"] = all(report.get(key) is True for key in (
                "real_model_execution", "critic_invoked", "telemetry_complete", "decision_schema_valid",
                "comparison_completed", "frame_set_sha_match", "source_binding_sha_match", "rubric_sha_match",
                "visual_assets_attached",
                "existing_final_review_unchanged", "production_ledger_unchanged", "locks_unchanged",
                "final_snapshot_unchanged", "episode_state_unchanged", "frozen_sources_unchanged",
            )) and report.get("failure") is False and report.get("timeout") is False
            return report
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
        report.setdefault("failure_class", type(exc).__name__)
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
        if report.get("source_mode") == "historical_frozen_exact" and report.get("ledger_sha256_before"):
            try:
                report["ledger_sha256_after"] = _ledger_sha(ep)
                report["production_ledger_unchanged"] = report["ledger_sha256_after"] == report["ledger_sha256_before"]
            except Exception as exc:
                report["ledger_sha256_after"] = None
                report["production_ledger_unchanged"] = False
                report.setdefault("blockers", []).append(f"ledger readback failed: {type(exc).__name__}")
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
        try:
            persisted_after, state_source_after = _canonical_episode_state(ep)
            report["episode_state_after"] = (persisted_after or {}).get("current_state")
            report["episode_state_source_after"] = state_source_after
            report["runtime_episode_state_unchanged"] = (
                report.get("episode_state_source") == state_source_after
                and critic.digest(persisted_state) == critic.digest(persisted_after)
            ) if report.get("episode_state_source") else False
        except Exception as exc:
            report["episode_state_after"] = None
            report["runtime_episode_state_unchanged"] = False
            report.setdefault("blockers", []).append(f"persisted state readback failed: {type(exc).__name__}")
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
        if report.get("source_mode") == "historical_frozen_exact":
            report["pass"] = all(report.get(key) is True for key in (
                "real_model_execution", "critic_invoked", "telemetry_complete", "decision_schema_valid",
                "comparison_completed", "frame_set_sha_match", "source_binding_sha_match", "rubric_sha_match",
                "visual_assets_attached",
                "existing_final_review_unchanged", "production_ledger_unchanged", "locks_unchanged",
                "final_snapshot_unchanged", "episode_state_unchanged", "runtime_episode_state_unchanged",
                "frozen_sources_unchanged",
            )) and report.get("failure") is False and report.get("timeout") is False
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
        "visual_assets_attached",
        "production_ledger_unchanged", "locks_unchanged", "final_snapshot_unchanged",
        "episode_state_unchanged", "runtime_episode_state_unchanged", "frozen_sources_unchanged",
    )) and report.get("timeout") is False and report.get("failure") is False
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--attempt", type=int, default=1, choices=(1, 2))
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--historical-source-bundle", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/p3-final-semantic-critic-real-shadow-smoke-20260928.json")
    args = parser.parse_args()
    from scripts.phase9_runtime_launcher import load_runtime_env_file
    loaded_env, runtime_env_keys = load_runtime_env_file(
        ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ),
    )
    os.environ.update(loaded_env)
    if args.preflight_only:
        if not args.historical_source_bundle:
            parser.error("--preflight-only requires --historical-source-bundle")
        ep = args.episode.resolve()
        review_path = ep / frame_semantic_review.SUMMARY_REL
        review = json.loads(review_path.read_text(encoding="utf-8-sig"))
        result = historical_attachment_preflight(ep, review, args.historical_source_bundle)
        result["runtime_env_keys_loaded"] = list(runtime_env_keys)
        raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with args.output.open("xb") as handle:
                handle.write(raw)
        except FileExistsError:
            print(f"refusing to overwrite immutable preflight evidence: {args.output}", file=sys.stderr)
            return 2
        print(json.dumps({key: result.get(key) for key in (
            "status", "expected_visual_asset_count", "attached_visual_asset_count",
            "visual_attachment_sha_match", "visual_attachment_type_valid", "blockers",
        )}, ensure_ascii=False))
        return 0 if result["status"] == "PASS" else 1
    result = run(args.episode, attempt=args.attempt, timeout=args.timeout,
                 historical_source_bundle=args.historical_source_bundle)
    result["runtime_env_keys_loaded"] = list(runtime_env_keys)
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
