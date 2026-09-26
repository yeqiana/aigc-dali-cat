#!/usr/bin/env python3
"""Load and validate the single human-editable Story OS YAML configuration."""
from __future__ import annotations

import argparse
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


def validate(data: dict | None = None) -> list[str]:
    cfg = data or _load(CONFIG_PATH)
    errors: list[str] = []
    if cfg.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(get_path(cfg, "image.model"), str) or not get_path(cfg, "image.model").strip():
        errors.append("image.model must be a non-empty model id")
    fallback_models = get_path(cfg, "image.fallback_models", [])
    if not isinstance(fallback_models, list) or any(
            not isinstance(row, str) or not row.strip() for row in fallback_models):
        errors.append("image.fallback_models must be a list of non-empty model ids")
    else:
        normalized = [row.strip() for row in fallback_models]
        if len(normalized) != len(set(normalized)):
            errors.append("image.fallback_models must not contain duplicates")
        if str(get_path(cfg, "image.model") or "").strip() in normalized:
            errors.append("image.fallback_models must not repeat image.model")
    if get_path(cfg, "image.quality") != "high":
        errors.append("image.quality must be high")
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
    preferred_runtime = str(get_path(cfg, "runtime.preferred_runtime", "")).upper()
    if preferred_runtime not in {"WORK", "WEB", "CODEX"}:
        errors.append("runtime.preferred_runtime must be WORK, WEB or CODEX")
    image_execution_runtime = str(get_path(cfg, "runtime.image_execution_runtime", "")).upper()
    if image_execution_runtime not in {"CODEX", "PRODUCT_RUNTIME", "AUTO"}:
        errors.append("runtime.image_execution_runtime must be CODEX, PRODUCT_RUNTIME or AUTO")
    if get_path(cfg, "runtime.codex_image_controller_model") != "gpt-5.6-luna":
        errors.append("runtime.codex_image_controller_model must be gpt-5.6-luna")
    if get_path(cfg, "runtime.codex_image_reasoning_effort") != "medium":
        errors.append("runtime.codex_image_reasoning_effort must be medium")
    if get_path(cfg, "runtime.local_codex_fallback") != "explicit_only":
        errors.append("runtime.local_codex_fallback must be explicit_only")
    if not isinstance(get_path(cfg, "runtime.codex_fallback_when_webcodex_unavailable"), bool):
        errors.append("runtime.codex_fallback_when_webcodex_unavailable must be a bool")
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
    if str(get_path(cfg, "runtime.review.vision.model", "")) != "gpt-5.6-terra":
        errors.append("runtime.review.vision.model must be gpt-5.6-terra")
    if get_path(cfg, "runtime.review.vision.isolated_required") is not True:
        errors.append("runtime.review.vision.isolated_required must be true")
    if get_path(cfg, "runtime.review.vision.ephemeral") is not True:
        errors.append("runtime.review.vision.ephemeral must be true")
    if get_path(cfg, "runtime.review.vision.generation_session_reuse") is not False:
        errors.append("runtime.review.vision.generation_session_reuse must be false")
    for key in ("reasoning_effort_default", "reasoning_effort_fast", "reasoning_effort_final"):
        if str(get_path(cfg, f"runtime.review.vision.{key}", "")) not in {"low", "medium", "high"}:
            errors.append(f"runtime.review.vision.{key} must be low, medium or high")
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
    data = _load(CONFIG_PATH)
    errors = validate(data)
    if errors:
        raise ValueError("CONFIG_INVALID: " + "; ".join(errors))
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
