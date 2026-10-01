#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic TEST_ONLY input preparation for Phase5A validation epochs.

This adapter intentionally does only preparation:
canonical fixture -> immutable Runtime Request -> frozen Model Policy ->
Frame Contract -> Prompt Package -> existing Production Queue admission.

It never reserves a Generation Attempt, calls a model/provider, reviews an
image, advances Episode stage, or grants release authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import frame_contract
import generation_attempt_authority
import image_scheduler
import logical_asset_identity
import model_policy
import phase5a_collaborative_canary as canary
import prompt_package_persistence
import runtime_request
import scheduler_core
import visual_profile_registry

FIXTURE_ID = "PHASE5A_SINGLE_FRAME_IMAGE_CHAIN_V1"
FIXTURE_SCHEMA_VERSION = 1
TOOL_VERSION = "2.1.0"
RUNTIME_REQUEST_TEXT = '"Phase5A Validation Fixture v1"\nimage_continue'
STORY_TEXT = """# Phase5A Validation Fixture v1

A quiet ordinary room in the afternoon. An old tabletop radio sits on a wooden table.
A powered-off television stands behind it. No people are present.
This fixture validates the single-frame image production chain and is never publishable.
"""
STORYBOARD_TEXT = """# Frame 01
Eye-level documentary observation of a quiet room. An old tabletop radio sits on a wooden
table, with its tuning pointer between station marks. A powered-off dark television stands
behind it. Soft overcast window daylight. No people, readable text, logos, captions,
watermarks, or cinematic staging.
"""
SCENE_PROMPT = """Frame 01: eye-level documentary still in a quiet overcast room. Old tabletop radio on wooden table; dark powered-off TV behind. Soft window daylight. No people, readable text, captions, logos, watermark, or cinematic staging."""


class ValidationInputError(RuntimeError):
    pass


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_text(text: str) -> str:
    return _sha_bytes(text.encode("utf-8"))


def _canonical_json(data: Any) -> bytes:
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _repo_rel(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValidationInputError("PHASE5A_VALIDATION_INPUT_PATH_ESCAPE") from exc


def _write_exact(path: Path, text: str) -> None:
    expected = text if text.endswith("\n") else text + "\n"
    if path.is_file():
        actual = path.read_text(encoding="utf-8-sig")
        if actual != expected:
            raise ValidationInputError(
                f"PHASE5A_VALIDATION_INPUT_DRIFT:{_repo_rel(path)}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def _write_json_exact(path: Path, data: dict[str, Any]) -> None:
    expected = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path.is_file():
        try:
            actual = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            raise ValidationInputError(
                f"PHASE5A_VALIDATION_INPUT_INVALID_JSON:{_repo_rel(path)}"
            ) from exc
        if actual != data:
            raise ValidationInputError(
                f"PHASE5A_VALIDATION_INPUT_DRIFT:{_repo_rel(path)}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def _fixture_documents(ep: Path) -> dict[str, Any]:
    profile = visual_profile_registry.registry_entry("M00")
    if not isinstance(profile, dict):
        raise ValidationInputError("PHASE5A_VALIDATION_PROFILE_M00_MISSING")
    profile_path = str(profile.get("path") or profile.get("profile_path") or "")
    if not profile_path or not (ROOT / profile_path).is_file():
        raise ValidationInputError("PHASE5A_VALIDATION_PROFILE_M00_INVALID")

    story_path = ep / "story.md"
    storyboard_path = ep / "storyboard.md"
    prompt_path = ep / "prompts/production/01.txt"

    release_manifest = {
        "tool_version": TOOL_VERSION,
        "episode": {
            "id": FIXTURE_ID,
            "title": "Phase5A Validation Fixture",
            "aspect_ratio": "4:5",
        },
        "release": {"body_frame_count": 1},
        "artifacts": {
            "story": _repo_rel(story_path),
            "storyboard": _repo_rel(storyboard_path),
        },
    }
    story_gates = {
        "tool_version": TOOL_VERSION,
        "canary_fixture": {
            "class": "TEST_ONLY",
            "promotion_class": "NON_PROMOTABLE",
            "fixture_id": FIXTURE_ID,
        },
        "visual_profile": {
            "mode": "default",
            "profile_id": "M00",
            "profile_path": profile_path,
            "capture_profile": "auto",
            "override_reason": None,
        },
        "visual": {
            "authenticity_card": {
                "capture_medium": "ordinary digital camera observation",
                "lighting": "available overcast daylight",
                "no_promotional_staging": True,
            },
            "continuity": {},
            "environment_contract": {
                "schema_version": 1,
                "baseline": {
                    "condition": "overcast",
                    "time_of_day": "afternoon",
                    "ground_state": "dry",
                    "visibility": "clear",
                    "physical_cues": ["soft daylight from a window"],
                },
                "segments": [],
                "frame_overrides": {},
            },
            "fast_frame_scout": {
                "schema_version": 1,
                "enabled": True,
                "policy": "risk_based_v21",
                "final_critic_still_required": True,
                "decisions": ["PASS_FAST", "REPAIR_NOW", "DEFER_TO_FINAL"],
                "high_risk_required": True,
            },
            "frame_directives": {
                "01": {
                    "narrative_role": "setup",
                    "frame_mode": "normal_record",
                    "impact_level": 1,
                    "required_visual_cues": [
                        "old tabletop radio on wooden table",
                        "dark powered-off television in background",
                        "ordinary overcast window light",
                    ],
                    "scale_reference": None,
                    "escalation_from": None,
                }
            },
        },
    }
    visual_profile = {
        "profile_id": "M00",
        "profile_path": profile_path,
        "capture_profile": "auto",
    }
    return {
        "story_path": story_path,
        "storyboard_path": storyboard_path,
        "prompt_path": prompt_path,
        "release_manifest": release_manifest,
        "story_gates": story_gates,
        "visual_profile": visual_profile,
        "profile_path": profile_path,
    }


def fixture_source_descriptor(ep: str | Path) -> dict[str, Any]:
    episode = Path(ep).resolve()
    docs = _fixture_documents(episode)
    source = {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "fixture_id": FIXTURE_ID,
        "tool_version": TOOL_VERSION,
        "runtime_request_text_sha256": _sha_text(RUNTIME_REQUEST_TEXT),
        "story_sha256": _sha_text(STORY_TEXT + ("" if STORY_TEXT.endswith("\n") else "\n")),
        "storyboard_sha256": _sha_text(
            STORYBOARD_TEXT + ("" if STORYBOARD_TEXT.endswith("\n") else "\n")
        ),
        "scene_prompt_sha256": _sha_text(SCENE_PROMPT + "\n"),
        "visual_profile_id": "M00",
        "visual_profile_path": docs["profile_path"],
        "body_frame_count": 1,
        "aspect_ratio": "4:5",
        "promotable": False,
        "release_eligible": False,
        "stage_authority": False,
    }
    source["source_sha256"] = _sha_bytes(_canonical_json(source))
    return source


def _ensure_fixture_files(ep: Path) -> dict[str, Any]:
    docs = _fixture_documents(ep)
    _write_exact(docs["story_path"], STORY_TEXT)
    _write_exact(docs["storyboard_path"], STORYBOARD_TEXT)
    _write_exact(docs["prompt_path"], SCENE_PROMPT)
    _write_json_exact(ep / "meta/release-manifest.json", docs["release_manifest"])
    _write_json_exact(ep / "meta/story-gates.json", docs["story_gates"])
    _write_json_exact(ep / "meta/visual-profile.json", docs["visual_profile"])
    descriptor = fixture_source_descriptor(ep)
    _write_json_exact(ep / "meta/phase5a-validation-input.json", descriptor)
    return {**docs, "descriptor": descriptor}


def _ensure_runtime_request_and_policy(ep: Path) -> dict[str, Any]:
    existing = runtime_request.effective_for_episode(ep)
    if existing is None:
        request = runtime_request.compile_request(RUNTIME_REQUEST_TEXT)
    else:
        request = dict(existing)
        provenance = request.get("provenance") if isinstance(request.get("provenance"), dict) else {}
        if provenance.get("original_request") != RUNTIME_REQUEST_TEXT:
            raise ValidationInputError("PHASE5A_VALIDATION_RUNTIME_REQUEST_DRIFT")
        if request.get("mode") != "image_continue":
            raise ValidationInputError("PHASE5A_VALIDATION_RUNTIME_MODE_DRIFT")
        if (request.get("story_input") or {}).get("mode") != "locked_story":
            raise ValidationInputError("PHASE5A_VALIDATION_STORY_MODE_DRIFT")
    result = canary.bind_and_freeze(ep, request)
    payload = model_policy.resolve("image.payload", episode=ep)
    if str(payload.get("model") or "") != "gpt-image-2.5-flare":
        raise ValidationInputError("PHASE5A_VALIDATION_PAYLOAD_MODEL_DRIFT")
    if str(payload.get("quality") or "").lower() != "high":
        raise ValidationInputError("PHASE5A_VALIDATION_PAYLOAD_QUALITY_DRIFT")
    return {**result, "request": request, "payload": payload}


def prepare(ep: str | Path, *, canary_id: str) -> dict[str, Any]:
    episode, marker = canary.validate_workspace(ep, canary_id)
    claim = canary.claim_global_canary(
        episode, canary_id, allow_validation_epoch=True
    )
    if not claim.get("validation_epoch"):
        raise ValidationInputError("PHASE5A_VALIDATION_EPOCH_REQUIRED")

    docs = _ensure_fixture_files(episode)
    binding = _ensure_runtime_request_and_policy(episode)

    contract = frame_contract.compile_frame(episode, 1, write_cache=True)
    imported = image_scheduler.import_batch(episode, docs["prompt_path"].parent)
    queue = scheduler_core.load_queue(episode)
    active = [
        row for row in queue.get("items") or []
        if isinstance(row, dict)
        and int(row.get("frame") or 0) == 1
        and row.get("kind") == "original"
        and row.get("status") != "superseded"
    ]
    if len(active) != 1:
        raise ValidationInputError("PHASE5A_VALIDATION_QUEUE_CARDINALITY_INVALID")
    item = active[0]
    package = prompt_package_persistence.load_latest(episode, 1)
    if not isinstance(package, dict):
        raise ValidationInputError("PHASE5A_VALIDATION_PROMPT_PACKAGE_MISSING")
    if (item.get("prompt_package") or {}).get("package_sha256") != package.get("package_sha256"):
        raise ValidationInputError("PHASE5A_VALIDATION_PROMPT_PACKAGE_BINDING_INVALID")
    if (item.get("prompt_package") or {}).get("frame_contract_sha256") != contract.get("contract_sha256"):
        raise ValidationInputError("PHASE5A_VALIDATION_FRAME_CONTRACT_BINDING_INVALID")

    asset_key = logical_asset_identity.frame_asset_key(episode, 1)
    attempt = generation_attempt_authority.load_asset_state(episode, asset_key)
    consumed = int(attempt.get("attempts_consumed") or 0)
    active_attempt = attempt.get("active_attempt_index")
    if consumed != 0 or active_attempt is not None:
        raise ValidationInputError("PHASE5A_VALIDATION_PREPARATION_CONSUMED_ATTEMPT")

    preparation = {
        "schema_version": 1,
        "kind": "phase5a_validation_input_preparation",
        "canary_id": canary_id,
        "validation_epoch": int(claim.get("validation_epoch") or 0),
        "fixture_id": FIXTURE_ID,
        "source_sha256": docs["descriptor"]["source_sha256"],
        "runtime_request_id": binding["runtime_request_id"],
        "model_policy_sha256": binding["policy_sha256"],
        "frame_contract_sha256": contract["contract_sha256"],
        "prompt_package_sha256": package["package_sha256"],
        "scene_prompt_sha256": package["scene_prompt_sha256"],
        "queue_item_id": item["id"],
        "queue_status": item["status"],
        "logical_asset_key": asset_key,
        "attempts_consumed": consumed,
        "remaining_attempts": int(attempt.get("remaining_attempts") or 0),
        "active_attempt_index": active_attempt,
        "provider_calls": 0,
        "model_calls": 0,
        "promotable": False,
        "release_eligible": False,
        "stage_authority": False,
        "marker": marker,
    }
    receipt_path = episode / "meta/phase5a-validation-preparation.json"
    if receipt_path.is_file():
        current = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        # Queue/item timestamps can remain historical, but preparation identity
        # itself must be immutable across resume.
        identity_keys = (
            "canary_id", "validation_epoch", "fixture_id", "source_sha256",
            "runtime_request_id", "model_policy_sha256", "frame_contract_sha256",
            "prompt_package_sha256", "scene_prompt_sha256", "queue_item_id",
            "logical_asset_key",
        )
        for key in identity_keys:
            if current.get(key) != preparation.get(key):
                raise ValidationInputError(
                    f"PHASE5A_VALIDATION_PREPARATION_DRIFT:{key}"
                )
    else:
        _write_json_exact(receipt_path, preparation)
    return preparation


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir", type=Path)
    ap.add_argument("--canary-id", required=True)
    args = ap.parse_args()
    try:
        row = prepare(args.episode_dir, canary_id=args.canary_id)
    except Exception as exc:
        print(json.dumps(
            {"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"},
            ensure_ascii=False, indent=2
        ))
        return 2
    print(json.dumps({"status": "READY", **row}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
