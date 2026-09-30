#!/usr/bin/env python3
"""Load and validate the single human-editable Story OS YAML configuration."""
from __future__ import annotations

import argparse
import contextvars
from contextlib import contextmanager
from functools import wraps
import json
import re
from pathlib import Path
from typing import Any

import workspace_provider

try:
    import yaml
except ImportError as exc:  # pragma: no cover - installation failure path
    raise SystemExit("PyYAML is required. Run: python -m pip install -r episodes/_system/requirements.txt") from exc

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config/storyos.yaml"
INDEX_PATH = ROOT / "config/index.yaml"
_CACHE: dict[Path, tuple[int, dict]] = {}
_operation_cache = contextvars.ContextVar("storyos_config_operation_cache", default=None)


@contextmanager
def operation_scope():
    """Keep one validated config snapshot for a single logical operation."""
    existing = _operation_cache.get()
    if existing is not None:
        yield existing
        return
    cache = {}
    token = _operation_cache.set(cache)
    try:
        yield cache
    finally:
        _operation_cache.reset(token)


def operation_cached(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with operation_scope():
            return function(*args, **kwargs)
    return wrapped


def _load(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"CONFIG_MISSING: {path.relative_to(ROOT).as_posix()}")
    stamp = path.stat().st_mtime_ns
    cached = _CACHE.get(path)
    if cached and cached[0] == stamp:
        return cached[1]
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"CONFIG_ROOT_INVALID: {path.relative_to(ROOT).as_posix()} must be a mapping")
    _CACHE[path] = (stamp, data)
    return data


def get_path(data: dict, dotted: str, default: Any = None) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


_REQUIRED_MODEL_PROFILES = {
    "orchestration", "authoring", "structured_text", "semantic_critic",
    "final_semantic", "vision_fast", "vision_final", "image_controller",
    "image_payload",
}
_REQUIRED_ROLE_ALIASES = {
    "orchestration": "orchestration",
    "story.authoring": "authoring",
    "preimage.character_finalize": "structured_text",
    "preimage.world_prepare": "structured_text",
    "preimage.frame_contract": "structured_text",
    "preimage.visual_narrative": "authoring",
    "prompt.production": "structured_text",
    "prompt.repair": "structured_text",
    "release": "structured_text",
    "critic.story": "semantic_critic",
    "critic.preimage": "semantic_critic",
    "critic.final": "final_semantic",
    "vision.fast": "vision_fast",
    "guardian": "vision_fast",
    "vision.visual_lock": "vision_final",
    "vision.final": "vision_final",
    "image.controller": "image_controller",
    "image.payload": "image_payload",
}


def _validate_model_policy(cfg: dict) -> list[str]:
    errors: list[str] = []
    policy = get_path(cfg, "models")
    if not isinstance(policy, dict):
        return ["models must be a mapping"]
    if not isinstance(policy.get("policy_version"), str) or not policy["policy_version"].strip():
        errors.append("models.policy_version must be a non-empty string")
    profiles = policy.get("profiles")
    if not isinstance(profiles, dict):
        return errors + ["models.profiles must be a mapping"]
    missing = _REQUIRED_MODEL_PROFILES - profiles.keys()
    if missing:
        errors.append("models.profiles missing required profiles: " + ", ".join(sorted(missing)))
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            errors.append(f"models.profiles.{name} must be a mapping")
            continue
        model = profile.get("model")
        if not isinstance(model, str) or not model.strip():
            errors.append(f"models.profiles.{name}.model must be a non-empty model id")
        if name == "image_payload":
            if profile.get("quality") != "high":
                errors.append("models.profiles.image_payload.quality must be high")
            fallback = profile.get("fallback_models")
            if not isinstance(fallback, list) or any(not isinstance(item, str) or not item.strip() for item in fallback):
                errors.append("models.profiles.image_payload.fallback_models must be a list of non-empty model ids")
            elif len(fallback) != len(set(fallback)) or model in fallback:
                errors.append("models.profiles.image_payload.fallback_models must be unique and exclude the primary model")
        else:
            if profile.get("reasoning_effort") not in {"low", "medium", "high"}:
                errors.append(f"models.profiles.{name}.reasoning_effort must be low, medium or high")
    aliases = policy.get("role_aliases")
    if not isinstance(aliases, dict):
        errors.append("models.role_aliases must be a mapping")
        return errors
    for role, expected in _REQUIRED_ROLE_ALIASES.items():
        if aliases.get(role) != expected:
            errors.append(f"models.role_aliases.{role} must map to {expected}")
    for role, profile in aliases.items():
        if not isinstance(role, str) or not role.strip() or not isinstance(profile, str) or profile not in profiles:
            errors.append(f"models.role_aliases.{role} must reference a configured profile")
    missing_value = object()
    for path in (
        "image.model", "image.quality", "image.fallback_models",
        "runtime.codex_image_controller_model", "runtime.codex_image_reasoning_effort",
        "runtime.review.text.model", "runtime.review.vision.model",
        "runtime.review.vision.reasoning_effort_default",
        "runtime.review.vision.reasoning_effort_fast",
        "runtime.review.vision.reasoning_effort_final",
    ):
        if get_path(cfg, path, missing_value) is not missing_value:
            errors.append(f"{path} is a legacy business model selector; use models.profiles and models.role_aliases")
    return errors


def validate(data: dict | None = None) -> list[str]:
    cfg = data or _load(CONFIG_PATH)
    errors: list[str] = []
    if cfg.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    errors.extend(_validate_model_policy(cfg))
    default_ratio = str(get_path(cfg, "image.default_aspect_ratio", ""))
    canvases = get_path(cfg, "image.canvases", {})
    if default_ratio not in {"4:5", "9:16"} or default_ratio not in canvases:
        errors.append("image.default_aspect_ratio must reference 4:5 or 9:16 canvas")
    for ratio, expected in {"4:5": (1080, 1350), "9:16": (1080, 1920)}.items():
        row = canvases.get(ratio) if isinstance(canvases, dict) else None
        if not isinstance(row, dict) or (row.get("width"), row.get("height")) != expected:
            errors.append(f"image.canvases.{ratio} must be {expected[0]}x{expected[1]}")
    auto = get_path(cfg, "normalize.automatic_ratio_delta_max")
    review = get_path(cfg, "normalize.review_ratio_delta_max")
    if not isinstance(auto, (int, float)) or not isinstance(review, (int, float)) or not 0 <= auto < review <= 0.05:
        errors.append("normalize ratio thresholds must satisfy 0 <= automatic < review <= 0.05")
    raw_min_dimension = get_path(cfg, "normalize.provider_raw_min_dimension")
    if not isinstance(raw_min_dimension, int) or not 64 <= raw_min_dimension <= 512:
        errors.append("normalize.provider_raw_min_dimension must be an int between 64 and 512")
    workers = get_path(cfg, "production.max_inflight_images")
    if not isinstance(workers, int) or not 1 <= workers <= 5:
        errors.append("production.max_inflight_images must be 1..5")
    if get_path(cfg, "normalize.default_crop") != "forbidden":
        errors.append("normalize.default_crop must be forbidden")
    if get_path(cfg, "normalize.enabled") is not True or get_path(cfg, "normalize.preserve_raw") is not True:
        errors.append("normalize.enabled and normalize.preserve_raw must be true")
    if get_path(cfg, "normalize.technical_failure_triggers_generation") is not False:
        errors.append("normalize.technical_failure_triggers_generation must be false")
    if not isinstance(get_path(cfg, "normalize.provider_ratio_crop_exception_enabled"), bool):
        errors.append("normalize.provider_ratio_crop_exception_enabled must be a bool")
    if get_path(cfg, "production.continuous_first_completed") is not True or get_path(cfg, "production.wave_barrier") is not False:
        errors.append("production must use continuous_first_completed=true and wave_barrier=false")
    if get_path(cfg, "production.ledger_single_writer") is not True:
        errors.append("production.ledger_single_writer must be true")
    triage = get_path(cfg, "production.local_visual_triage")
    if not isinstance(triage, dict):
        errors.append("production.local_visual_triage must be a mapping")
    else:
        for key in ("enabled", "hard_failures_block_commit"):
            if not isinstance(triage.get(key), bool):
                errors.append(f"production.local_visual_triage.{key} must be a bool")
        for key in ("near_duplicate_phash_max_distance", "near_duplicate_dhash_max_distance"):
            value = triage.get(key)
            if type(value) is not int or not 0 <= value <= 16:
                errors.append(f"production.local_visual_triage.{key} must be an int between 0 and 16")
        ranges = {
            "low_entropy_warn_below": (0.0, 8.0),
            "dark_luma_warn_below": (0.0, 64.0),
            "bright_luma_warn_above": (191.0, 255.0),
            "low_edge_mean_warn_below": (0.0, 64.0),
            "repair_noop_rms_max": (0.0, 0.05),
            "repair_ssim_warn_below": (0.0, 1.0),
        }
        for key, (lo, hi) in ranges.items():
            value = triage.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not lo <= float(value) <= hi:
                errors.append(f"production.local_visual_triage.{key} must be between {lo} and {hi}")
        embedding = triage.get("embedding")
        if not isinstance(embedding, dict):
            errors.append("production.local_visual_triage.embedding must be a mapping")
        else:
            if not isinstance(embedding.get("enabled"), bool):
                errors.append("production.local_visual_triage.embedding.enabled must be a bool")
            if embedding.get("provider") != "onnx":
                errors.append("production.local_visual_triage.embedding.provider must be onnx")
            if not isinstance(embedding.get("model_path"), str):
                errors.append("production.local_visual_triage.embedding.model_path must be a string")
            if embedding.get("enabled") is True and not str(embedding.get("model_path") or "").strip():
                errors.append("production.local_visual_triage.embedding.model_path required when enabled")
            if type(embedding.get("input_size")) is not int or not 64 <= embedding.get("input_size") <= 1024:
                errors.append("production.local_visual_triage.embedding.input_size must be an int between 64 and 1024")
        sface = triage.get("sface")
        if not isinstance(sface, dict):
            errors.append("production.local_visual_triage.sface must be a mapping")
        else:
            if not isinstance(sface.get("enabled"), bool):
                errors.append("production.local_visual_triage.sface.enabled must be a bool")
            if type(sface.get("max_references")) is not int or not 1 <= sface.get("max_references") <= 8:
                errors.append("production.local_visual_triage.sface.max_references must be an int between 1 and 8")
        grounding = triage.get("grounding_dino")
        if not isinstance(grounding, dict):
            errors.append("production.local_visual_triage.grounding_dino must be a mapping")
        else:
            if not isinstance(grounding.get("enabled"), bool):
                errors.append("production.local_visual_triage.grounding_dino.enabled must be a bool")
            if not isinstance(grounding.get("model_path"), str):
                errors.append("production.local_visual_triage.grounding_dino.model_path must be a string")
            if grounding.get("enabled") is True and not str(grounding.get("model_path") or "").strip():
                errors.append("production.local_visual_triage.grounding_dino.model_path required when enabled")
            if type(grounding.get("max_queries")) is not int or not 1 <= grounding.get("max_queries") <= 32:
                errors.append("production.local_visual_triage.grounding_dino.max_queries must be an int between 1 and 32")
            for key in ("box_threshold", "text_threshold"):
                value = grounding.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 1.0:
                    errors.append(f"production.local_visual_triage.grounding_dino.{key} must be between 0 and 1")
            if not isinstance(grounding.get("flag_missing_queries"), bool):
                errors.append("production.local_visual_triage.grounding_dino.flag_missing_queries must be a bool")
        sam2 = triage.get("sam2")
        if not isinstance(sam2, dict):
            errors.append("production.local_visual_triage.sam2 must be a mapping")
        else:
            if not isinstance(sam2.get("enabled"), bool):
                errors.append("production.local_visual_triage.sam2.enabled must be a bool")
            if not isinstance(sam2.get("model_path"), str):
                errors.append("production.local_visual_triage.sam2.model_path must be a string")
            if sam2.get("enabled") is True and not str(sam2.get("model_path") or "").strip():
                errors.append("production.local_visual_triage.sam2.model_path required when enabled")
            value = sam2.get("broad_mask_warn_above")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 1.0:
                errors.append("production.local_visual_triage.sam2.broad_mask_warn_above must be between 0 and 1")
        pose = triage.get("pose")
        if not isinstance(pose, dict):
            errors.append("production.local_visual_triage.pose must be a mapping")
        else:
            if not isinstance(pose.get("enabled"), bool):
                errors.append("production.local_visual_triage.pose.enabled must be a bool")
            if not isinstance(pose.get("model_path"), str):
                errors.append("production.local_visual_triage.pose.model_path must be a string")
            if pose.get("enabled") is True and not str(pose.get("model_path") or "").strip():
                errors.append("production.local_visual_triage.pose.model_path required when enabled")
            for key in ("input_width", "input_height"):
                value = pose.get(key)
                if type(value) is not int or not 64 <= value <= 2048:
                    errors.append(f"production.local_visual_triage.pose.{key} must be an int between 64 and 2048")
            value = pose.get("mean_confidence_warn_below")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 1.0:
                errors.append("production.local_visual_triage.pose.mean_confidence_warn_below must be between 0 and 1")
        lpips = triage.get("lpips")
        if not isinstance(lpips, dict):
            errors.append("production.local_visual_triage.lpips must be a mapping")
        else:
            if not isinstance(lpips.get("enabled"), bool):
                errors.append("production.local_visual_triage.lpips.enabled must be a bool")
            if lpips.get("net") not in {"alex", "vgg", "squeeze"}:
                errors.append("production.local_visual_triage.lpips.net must be alex, vgg or squeeze")
            if type(lpips.get("max_side")) is not int or not 64 <= lpips.get("max_side") <= 2048:
                errors.append("production.local_visual_triage.lpips.max_side must be an int between 64 and 2048")
            value = lpips.get("warn_above")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 2.0:
                errors.append("production.local_visual_triage.lpips.warn_above must be between 0 and 2")
    if get_path(cfg, "provider.exact_raw_canvas_required") is not False:
        errors.append("provider.exact_raw_canvas_required must be false for current desktop image transport")
    if get_path(cfg, "provider.measure_raw_dimensions_locally") is not True:
        errors.append("provider.measure_raw_dimensions_locally must be true")
    if get_path(cfg, "provider.provider_receipt_required") is not True:
        errors.append("provider.provider_receipt_required must be true")
    if not isinstance(get_path(cfg, "provider.group_reference_proxy"), bool):
        errors.append("provider.group_reference_proxy must be a bool")
    if get_path(cfg, "agent_runtime.trace.enabled") is not True:
        errors.append("agent_runtime.trace.enabled must be true")
    if get_path(cfg, "agent_runtime.intent.enabled") is not True:
        errors.append("agent_runtime.intent.enabled must be true")
    if get_path(cfg, "agent_runtime.router.enabled") is not True:
        errors.append("agent_runtime.router.enabled must be true")
    if get_path(cfg, "agent_runtime.batch.enabled") is not True:
        errors.append("agent_runtime.batch.enabled must be true")
    if get_path(cfg, "agent_runtime.codex_subscription_batch.enabled") is not True:
        errors.append("agent_runtime.codex_subscription_batch.enabled must be true")
    if not isinstance(get_path(cfg, "agent_runtime.adapters.character_finalize.shadow_enabled"), bool):
        errors.append("agent_runtime.adapters.character_finalize.shadow_enabled must be a bool")
    if not isinstance(get_path(cfg, "agent_runtime.adapters.character_finalize.production_enabled"), bool):
        errors.append("agent_runtime.adapters.character_finalize.production_enabled must be a bool")
    if not isinstance(get_path(cfg, "agent_runtime.adapters.character_finalize.legacy_fallback_on_technical"), bool):
        errors.append("agent_runtime.adapters.character_finalize.legacy_fallback_on_technical must be a bool")
    if not isinstance(get_path(cfg, "agent_runtime.adapters.world_prepare.shadow_enabled"), bool):
        errors.append("agent_runtime.adapters.world_prepare.shadow_enabled must be a bool")
    if not isinstance(get_path(cfg, "agent_runtime.adapters.world_prepare.production_enabled"), bool):
        errors.append("agent_runtime.adapters.world_prepare.production_enabled must be a bool")
    story_critic = get_path(cfg, "agent_runtime.adapters.story_semantic_critic")
    if story_critic is not None:
        for key in ("shadow_enabled", "production_enabled", "legacy_fallback_on_technical"):
            if not isinstance(story_critic.get(key) if isinstance(story_critic, dict) else None, bool):
                errors.append(f"agent_runtime.adapters.story_semantic_critic.{key} must be a bool")
        if story_critic.get("shadow_enabled") is True and story_critic.get("production_enabled") is True:
            errors.append("agent_runtime.adapters.story_semantic_critic shadow and production cannot both be enabled")
        reflection = story_critic.get("bounded_reflection") if isinstance(story_critic, dict) else None
        if not isinstance(reflection, dict):
            errors.append("agent_runtime.adapters.story_semantic_critic.bounded_reflection must be a mapping")
        else:
            if reflection.get("max_review_attempts") != 2:
                errors.append("agent_runtime.adapters.story_semantic_critic.bounded_reflection.max_review_attempts must be 2")
            if reflection.get("max_auto_repairs") != 1:
                errors.append("agent_runtime.adapters.story_semantic_critic.bounded_reflection.max_auto_repairs must be 1")
    preimage_critic = get_path(cfg, "agent_runtime.adapters.preimage_semantic_critic")
    if preimage_critic is not None:
        for key in ("shadow_enabled", "production_enabled", "legacy_fallback_on_technical"):
            if not isinstance(preimage_critic.get(key) if isinstance(preimage_critic, dict) else None, bool):
                errors.append(f"agent_runtime.adapters.preimage_semantic_critic.{key} must be a bool")
        if isinstance(preimage_critic, dict) and preimage_critic.get("shadow_enabled") is True and preimage_critic.get("production_enabled") is True:
            errors.append("agent_runtime.adapters.preimage_semantic_critic shadow and production cannot both be enabled")
        reflection = preimage_critic.get("bounded_reflection") if isinstance(preimage_critic, dict) else None
        if not isinstance(reflection, dict):
            errors.append("agent_runtime.adapters.preimage_semantic_critic.bounded_reflection must be a mapping")
        else:
            if reflection.get("max_review_attempts") != 2:
                errors.append("agent_runtime.adapters.preimage_semantic_critic.bounded_reflection.max_review_attempts must be 2")
            if reflection.get("max_auto_repairs") != 1:
                errors.append("agent_runtime.adapters.preimage_semantic_critic.bounded_reflection.max_auto_repairs must be 1")
    final_critic = get_path(cfg, "agent_runtime.adapters.final_semantic_critic")
    if final_critic is not None:
        for key in ("shadow_enabled", "production_enabled", "legacy_fallback_on_technical"):
            if not isinstance(final_critic.get(key) if isinstance(final_critic, dict) else None, bool):
                errors.append(f"agent_runtime.adapters.final_semantic_critic.{key} must be a bool")
        if isinstance(final_critic, dict) and final_critic.get("shadow_enabled") is True and final_critic.get("production_enabled") is True:
            errors.append("agent_runtime.adapters.final_semantic_critic shadow and production cannot both be enabled")
        reflection = final_critic.get("bounded_reflection") if isinstance(final_critic, dict) else None
        if not isinstance(reflection, dict):
            errors.append("agent_runtime.adapters.final_semantic_critic.bounded_reflection must be a mapping")
        else:
            if reflection.get("max_review_attempts") != 2:
                errors.append("agent_runtime.adapters.final_semantic_critic.bounded_reflection.max_review_attempts must be 2")
            if reflection.get("max_auto_repairs") != 1:
                errors.append("agent_runtime.adapters.final_semantic_critic.bounded_reflection.max_auto_repairs must be 1")
    router = get_path(cfg, "agent_runtime.task_capability_router")
    if not isinstance(router, dict):
        errors.append("agent_runtime.task_capability_router must be a mapping")
    else:
        for key in ("shadow_enabled", "production_enabled"):
            if not isinstance(router.get(key), bool):
                errors.append(f"agent_runtime.task_capability_router.{key} must be a bool")
        ttl = router.get("health_ttl_seconds")
        if type(ttl) is not int or ttl <= 0:
            errors.append("agent_runtime.task_capability_router.health_ttl_seconds must be a positive int")
        depth = router.get("max_fallback_depth")
        if type(depth) is not int or depth < 0:
            errors.append("agent_runtime.task_capability_router.max_fallback_depth must be a non-negative int")
        if router.get("policy_mode") != "LEGACY_PREFERRED_CAPABILITY_GUARDED":
            errors.append("agent_runtime.task_capability_router.policy_mode is not supported")
        allowed_tasks = {"story_semantic_critic", "preimage_semantic_critic", "final_semantic_critic"}
        supported = router.get("supported_task_types")
        if (not isinstance(supported, list) or not supported
                or any(not isinstance(task, str) or task not in allowed_tasks for task in supported)
                or len(supported) != len(set(supported))):
            errors.append("agent_runtime.task_capability_router.supported_task_types must be a non-empty unique allowlist of registered Critic task types")
    guardian = get_path(cfg, "agent_runtime.guardian_facade")
    if not isinstance(guardian, dict):
        errors.append("agent_runtime.guardian_facade must be a mapping")
    else:
        for key in ("shadow_enabled", "production_enabled"):
            if not isinstance(guardian.get(key), bool):
                errors.append(f"agent_runtime.guardian_facade.{key} must be a bool")
    preferred_runtime = str(get_path(cfg, "runtime.preferred_runtime", "")).upper()
    if preferred_runtime not in {"WORK", "WEB", "CODEX"}:
        errors.append("runtime.preferred_runtime must be WORK, WEB or CODEX")
    production_mode = str(get_path(cfg, "production.mode", "")).strip().upper()
    if production_mode not in {"COLLABORATIVE", "CODEX_MANAGED"}:
        errors.append("production.mode must be COLLABORATIVE or CODEX_MANAGED")
    image_executor = str(get_path(cfg, "execution.image.executor", "")).strip().upper()
    if image_executor not in {"CODEX", "PRODUCT_RUNTIME", "AUTO"}:
        errors.append("execution.image.executor must be CODEX, PRODUCT_RUNTIME or AUTO")
    vision_executor = str(get_path(cfg, "execution.vision_review.executor", "")).strip().upper()
    if vision_executor not in {"CODEX", "WORK", "AUTO"}:
        errors.append("execution.vision_review.executor must be CODEX, WORK or AUTO")
    workspace_executor = str(get_path(cfg, "execution.workspace.provider", "")).strip().lower()
    if workspace_executor != "webcodex":
        errors.append("execution.workspace.provider must be webcodex")
    legacy_workspace_executor = str(get_path(cfg, "runtime.workspace.provider", "")).strip().lower()
    if legacy_workspace_executor and legacy_workspace_executor != workspace_executor:
        errors.append("runtime.workspace.provider compatibility alias must match execution.workspace.provider")
    image_execution_runtime = str(get_path(cfg, "runtime.image_execution_runtime", "")).upper()
    if image_execution_runtime not in {"CODEX", "PRODUCT_RUNTIME", "AUTO"}:
        errors.append("runtime.image_execution_runtime must be CODEX, PRODUCT_RUNTIME or AUTO")
    if get_path(cfg, "runtime.local_codex_fallback") != "explicit_only":
        errors.append("runtime.local_codex_fallback must be explicit_only")
    if not isinstance(get_path(cfg, "runtime.codex_fallback_when_webcodex_unavailable"), bool):
        errors.append("runtime.codex_fallback_when_webcodex_unavailable must be a bool")
    elif get_path(cfg, "runtime.codex_fallback_when_webcodex_unavailable") is not False:
        errors.append("runtime.codex_fallback_when_webcodex_unavailable must remain false; mode switching is explicit")
    if image_execution_runtime and image_execution_runtime != image_executor:
        errors.append("runtime.image_execution_runtime compatibility alias must match execution.image.executor")
    errors.extend(workspace_provider.validate_config(cfg))
    # Review capability routing. WORK remains text/governance authority; actual-pixel
    # review is a separate isolated Codex capability and does not switch the whole Runtime.
    if str(get_path(cfg, "runtime.review.text.runtime", "")).upper() != "WORK":
        errors.append("runtime.review.text.runtime must be WORK")
    if get_path(cfg, "runtime.review.text.isolated_required") is not True:
        errors.append("runtime.review.text.isolated_required must be true")
    if get_path(cfg, "runtime.review.text.fresh_turn_required") is not True:
        errors.append("runtime.review.text.fresh_turn_required must be true")
    if str(get_path(cfg, "runtime.review.vision.runtime", "")).upper() != "CODEX":
        errors.append("runtime.review.vision.runtime must be CODEX")
    if str(get_path(cfg, "runtime.review.vision.runtime", "")).upper() != vision_executor:
        errors.append("runtime.review.vision.runtime compatibility alias must match execution.vision_review.executor")
    if get_path(cfg, "runtime.review.vision.isolated_required") is not True:
        errors.append("runtime.review.vision.isolated_required must be true")
    if get_path(cfg, "runtime.review.vision.ephemeral") is not True:
        errors.append("runtime.review.vision.ephemeral must be true")
    if get_path(cfg, "runtime.review.vision.generation_session_reuse") is not False:
        errors.append("runtime.review.vision.generation_session_reuse must be false")
    final_review_cap = get_path(cfg, "runtime.review.vision.max_inflight_final")
    if type(final_review_cap) is not int or not 1 <= final_review_cap <= 6:
        errors.append("runtime.review.vision.max_inflight_final must be an int between 1 and 6")
    if str(get_path(cfg, "runtime.review.governance.runtime", "")).upper() != "WORK":
        errors.append("runtime.review.governance.runtime must be WORK")
    if get_path(cfg, "runtime.review.allow_web_runtime") is not False:
        errors.append("runtime.review.allow_web_runtime must be false")
    for key in ("enabled", "gate_hint", "local_gate_enabled"):
        if not isinstance(get_path(cfg, f"runtime.review.local_vision_shadow.{key}"), bool):
            errors.append(f"runtime.review.local_vision_shadow.{key} must be a bool")
    host_loop_cap = get_path(cfg, "runtime.host_loop_max_cycles")
    if type(host_loop_cap) is not int or not 8 <= host_loop_cap <= 256:
        errors.append("runtime.host_loop_max_cycles must be an int between 8 and 256")

    # Legacy runtime aliases stay validated during migration. Workspace provider
    # identity is canonical only under runtime.workspace.
    if str(get_path(cfg, "runtime.review.runtime", "")).upper() != "WORK":
        errors.append("runtime.review.runtime legacy alias must be WORK")
    if get_path(cfg, "runtime.review.isolated_critic_required") is not True:
        errors.append("runtime.review.isolated_critic_required legacy alias must be true")
    if get_path(cfg, "runtime.review.fresh_product_review_turn_required") is not True:
        errors.append("runtime.review.fresh_product_review_turn_required legacy alias must be true")
    if get_path(cfg, "runtime.review.allow_local_codex_review") is not False:
        errors.append("runtime.review.allow_local_codex_review legacy text/governance alias must be false")
    for key, expected in (("runtime.workers.local_codex_preimage",4),("runtime.workers.derived",6)):
        if get_path(cfg,key) != expected: errors.append(f"{key} must be {expected}")
    # W-91: runtime.parallel.authority_enabled / derived_enabled were removed rather
    # than pinned here. A key whose only reader is this type check is exactly the
    # "declared but never consumed" state the config-reality contract forbids.
    if not isinstance(get_path(cfg,"runtime.preimage_parallel_enabled"), bool):
        errors.append("runtime.preimage_parallel_enabled must be a bool")
    for key in (
        "provider.registry",
        "provider.runtime",
        "agent_runtime.trace.config",
        "agent_runtime.intent.config",
        "agent_runtime.router.config",
        "agent_runtime.batch.config",
        "agent_runtime.codex_subscription_batch.config",
        "creative.account_profile_path",
        "directing.grammar_path",
        "visual.default_profile_path",
        "visual.capture_profile_registry",
        "visual.capture_grammar_path",
        "visual.sequence_grammar_path",
    ):
        raw = get_path(cfg, key)
        if not isinstance(raw, str) or not (ROOT / raw).is_file():
            errors.append(f"{key} points to a missing file: {raw}")
    for key in ("paths.index", "paths.product_manifest", "paths.creative_authority", "paths.authority_index"):
        raw = get_path(cfg, key)
        if not isinstance(raw, str) or not (ROOT / raw).exists():
            errors.append(f"{key} points to a missing path: {raw}")
    repair_limit=get_path(cfg,"production.max_content_repairs_per_frame")
    if type(repair_limit) is not int or repair_limit not in {0,1}:
        errors.append("production.max_content_repairs_per_frame must be 0 or 1")
    baseline_pool_enabled=get_path(cfg,"production.visual_lock_baseline_pool.enabled")
    baseline_pool_max=get_path(cfg,"production.visual_lock_baseline_pool.max_additional_candidates")
    if baseline_pool_enabled is not True:
        errors.append("production.visual_lock_baseline_pool.enabled must be true")
    if type(baseline_pool_max) is not int or not 0 <= baseline_pool_max <= 3:
        errors.append("production.visual_lock_baseline_pool.max_additional_candidates must be 0..3")
    admission_pool_enabled=get_path(cfg,"production.visual_lock_admission_pool.enabled")
    admission_pool_max=get_path(cfg,"production.visual_lock_admission_pool.max_additional_candidates_per_frame")
    if admission_pool_enabled is not True:
        errors.append("production.visual_lock_admission_pool.enabled must be true")
    if type(admission_pool_max) is not int or not 0 <= admission_pool_max <= 3:
        errors.append("production.visual_lock_admission_pool.max_additional_candidates_per_frame must be 0..3")
    tech_retry_max=get_path(cfg,"production.technical_retry.max_attempts_per_item")
    tech_retry_backoff=get_path(cfg,"production.technical_retry.backoff_seconds")
    if type(tech_retry_max) is not int or not 1 <= tech_retry_max <= 5:
        errors.append("production.technical_retry.max_attempts_per_item must be 1..5")
    if not isinstance(tech_retry_backoff,list) or len(tech_retry_backoff) != max(0, int(tech_retry_max or 0)-1) or any(type(x) is not int or x < 0 or x > 300 for x in tech_retry_backoff):
        errors.append("production.technical_retry.backoff_seconds must contain max_attempts_per_item-1 integer delays in 0..300")
    policy = get_path(cfg, "timeout_policy")
    try:
        from runtime_timeout_policy import REQUIRED_ROLES, VALID_RANGE
    except ImportError:
        REQUIRED_ROLES = ()
        VALID_RANGE = {}
    if not isinstance(policy, dict):
        errors.append("timeout_policy must be a mapping")
    else:
        for role in REQUIRED_ROLES:
            if role not in policy:
                errors.append(f"timeout_policy missing required key: {role}")
        for role, value in policy.items():
            if role not in REQUIRED_ROLES:
                errors.append(f"timeout_policy has unknown key: {role}")
            elif not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"timeout_policy.{role} must be a positive int")
            else:
                rng = VALID_RANGE.get(role)
                if rng is not None and not rng[0] <= value <= rng[1]:
                    errors.append(f"timeout_policy.{role} must be within {rng[0]}..{rng[1]}")
    # B9 契约位：compatibility 三开关只允许布尔；false 表示禁止对应历史兼容行为。
    compat = get_path(cfg, "compatibility")
    if not isinstance(compat, dict):
        errors.append("compatibility must be a mapping")
    else:
        for key in ("read_legacy_json", "rewrite_bound_runtime_request", "migrate_historical_episode_meta"):
            value = compat.get(key)
            if not isinstance(value, bool):
                errors.append(f"compatibility.{key} must be a bool")
    # storage 契约位：只放非敏感部署拓扑，凭据一律只以环境变量「名字」出现。
    # password_env 的格式校验是「禁止把密码写进仓库」的机器化防线：任何看起来
    # 像密码字面量的值都匹配不上 STORYOS_* 变量名，会在这里 fail-fast。
    storage = get_path(cfg, "storage")
    if not isinstance(storage, dict):
        errors.append("storage must be a mapping")
    else:
        for name, required in (
            ("mysql", ("host", "port", "user", "database", "password_env")),
            ("redis", ("host", "port", "db", "timeout_seconds", "password_env")),
        ):
            section = storage.get(name)
            if not isinstance(section, dict):
                errors.append(f"storage.{name} must be a mapping")
                continue
            for key in required:
                if key not in section:
                    errors.append(f"storage.{name}.{key} is required")
            if not isinstance(section.get("host"), str) or not str(section.get("host") or "").strip():
                errors.append(f"storage.{name}.host must be a non-empty string")
            port = section.get("port")
            if type(port) is not int or not 1 <= port <= 65535:
                errors.append(f"storage.{name}.port must be an int in 1..65535")
            password_env = section.get("password_env")
            if not isinstance(password_env, str) or not re.fullmatch(r"STORYOS_[A-Z0-9_]+", password_env):
                errors.append(
                    f"storage.{name}.password_env must name a STORYOS_* environment variable; "
                    "credential literals must never be written into this file"
                )
        mysql = storage.get("mysql") if isinstance(storage.get("mysql"), dict) else {}
        redis = storage.get("redis") if isinstance(storage.get("redis"), dict) else {}
        if not isinstance(mysql.get("user"), str) or not str(mysql.get("user") or "").strip():
            errors.append("storage.mysql.user must be a non-empty string")
        if not isinstance(mysql.get("database"), str) or not str(mysql.get("database") or "").strip():
            errors.append("storage.mysql.database must be a non-empty string")
        redis_db = redis.get("db")
        if type(redis_db) is not int or redis_db < 0:
            errors.append("storage.redis.db must be a non-negative int")
        redis_timeout = redis.get("timeout_seconds")
        if type(redis_timeout) not in (int, float) or isinstance(redis_timeout, bool) or redis_timeout <= 0:
            errors.append("storage.redis.timeout_seconds must be a positive number")
        runtime_store = storage.get("runtime_store")
        if not isinstance(runtime_store, dict):
            errors.append("storage.runtime_store must be a mapping")
        else:
            if str(runtime_store.get("mode") or "").lower() not in {"jsonl", "mysql", "dual"}:
                errors.append("storage.runtime_store.mode must be jsonl, mysql or dual")
            jsonl_root = runtime_store.get("jsonl_root")
            if not isinstance(jsonl_root, str) or not jsonl_root.strip():
                errors.append("storage.runtime_store.jsonl_root must be a non-empty string")
        episode_meta_store = storage.get("episode_meta_store")
        if not isinstance(episode_meta_store, dict):
            errors.append("storage.episode_meta_store must be a mapping")
        elif str(episode_meta_store.get("mode") or "").lower() not in {"json", "dual", "mysql"}:
            errors.append("storage.episode_meta_store.mode must be json, dual or mysql")
        hot_state = storage.get("hot_state")
        if not isinstance(hot_state, dict):
            errors.append("storage.hot_state must be a mapping")
        elif str(hot_state.get("mode") or "").lower() not in {"file", "dual", "redis"}:
            errors.append("storage.hot_state.mode must be file, dual or redis")
    return errors


def load_config() -> dict:
    cache = _operation_cache.get()
    if cache is not None and "config" in cache:
        return cache["config"]
    data = _load(CONFIG_PATH)
    errors = validate(data)
    if errors:
        raise ValueError("CONFIG_INVALID: " + "; ".join(errors))
    if cache is not None:
        cache["config"] = data
        return data
    return data


def load_index() -> dict:
    data = _load(INDEX_PATH)
    errors = validate_index(data)
    if errors:
        raise ValueError("INDEX_INVALID: " + "; ".join(errors))
    return data


def validate_index(data: dict | None = None) -> list[str]:
    index = data or _load(INDEX_PATH)
    errors: list[str] = []
    if index.get("schema_version") != 1 or index.get("config") != "config/storyos.yaml":
        errors.append("schema_version/config")
    for section in ("entrypoints", "authority", "registries", "runtimes"):
        rows = index.get(section)
        if not isinstance(rows, dict):
            errors.append(f"{section} must be a mapping")
            continue
        for name, raw in rows.items():
            if not isinstance(raw, str) or "<episode>" in raw:
                continue
            if not (ROOT / raw).exists():
                errors.append(f"{section}.{name} points to missing path: {raw}")
    stages = index.get("stage_read_sets")
    required_steps={"CREATIVE_STORY", "PREIMAGE_COMPILE", "VISUAL_LOCK", "PRODUCTION", "RELEASE"}
    if not isinstance(stages, dict) or not required_steps.issubset(set(stages)):
        errors.append("stage_read_sets must declare the five bounded workflow steps")
    else:
        for step, paths in stages.items():
            if not isinstance(paths, list) or not paths or paths[0] != "config/storyos.yaml":
                errors.append(f"stage_read_sets.{step} must start with config/storyos.yaml")
    internal = index.get("internal")
    if not isinstance(internal, dict):
        errors.append("internal must be a mapping")
    else:
        legacy_index = internal.get("legacy_runtime_index")
        if not isinstance(legacy_index, str) or not legacy_index.strip():
            errors.append("internal.legacy_runtime_index must be a non-empty relative path string")
    layout = index.get("episode_layout")
    layout_groups = ("authority", "evidence", "derived", "local_derived", "media")
    if not isinstance(layout, dict) or any(not isinstance(layout.get(group), list) for group in layout_groups):
        errors.append("episode_layout must declare authority/evidence/derived/local_derived/media lists")
    return errors


def legacy_json_read_allowed(cfg: dict | None = None) -> bool:
    """compatibility.read_legacy_json 当前是否允许读取 legacy JSON。"""
    data = cfg if cfg is not None else _load(CONFIG_PATH)
    return get_path(data, "compatibility.read_legacy_json") is True


def guard_legacy_json_read(path: str | Path, *, cfg: dict | None = None) -> None:
    """legacy JSON 读取闸口（B9 契约位）。

    仓库当前没有历史 legacy JSON 的 .py 消费者；未来任何代码若要读取
    .storyos/history/legacy/ 下的 runtime-index 或历史请求/证据 JSON，
    必须先经过本闸口：compatibility.read_legacy_json=false 时显式报错，
    禁止静默读旧格式。rewrite_bound_runtime_request 与
    migrate_historical_episode_meta 同样登记为契约位（当前无对应写路径），
    新增写路径的代码必须显式读取这两个开关。
    """
    if legacy_json_read_allowed(cfg):
        return
    raise ValueError(
        "LEGACY_JSON_READ_BLOCKED: compatibility.read_legacy_json=false; "
        f"refusing legacy JSON read: {path}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["validate", "show", "index"])
    args = ap.parse_args()
    try:
        if args.command == "validate":
            errors = validate()
            errors.extend(validate_index())
            if errors:
                for error in errors:
                    print("[FAIL]", error)
                return 2
            print("STORY OS CONFIG VALID")
            return 0
        data = load_index() if args.command == "index" else load_config()
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("STORY OS CONFIG ERROR:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
