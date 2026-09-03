#!/usr/bin/env python3
"""Load and validate the single human-editable Story OS YAML configuration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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
    workers = get_path(cfg, "production.max_inflight_images")
    if not isinstance(workers, int) or not 1 <= workers <= 3:
        errors.append("production.max_inflight_images must be 1..3")
    if get_path(cfg, "normalize.default_crop") != "forbidden":
        errors.append("normalize.default_crop must be forbidden")
    if get_path(cfg, "normalize.enabled") is not True or get_path(cfg, "normalize.preserve_raw") is not True:
        errors.append("normalize.enabled and normalize.preserve_raw must be true")
    if get_path(cfg, "normalize.technical_failure_triggers_generation") is not False:
        errors.append("normalize.technical_failure_triggers_generation must be false")
    if get_path(cfg, "production.continuous_first_completed") is not True or get_path(cfg, "production.wave_barrier") is not False:
        errors.append("production must use continuous_first_completed=true and wave_barrier=false")
    if get_path(cfg, "production.ledger_single_writer") is not True:
        errors.append("production.ledger_single_writer must be true")
    if get_path(cfg, "provider.exact_raw_canvas_required") is not False:
        errors.append("provider.exact_raw_canvas_required must be false for current desktop image transport")
    if get_path(cfg, "provider.measure_raw_dimensions_locally") is not True:
        errors.append("provider.measure_raw_dimensions_locally must be true")
    if get_path(cfg, "provider.provider_receipt_required") is not True:
        errors.append("provider.provider_receipt_required must be true")
    if get_path(cfg, "agent_runtime.trace.enabled") is not True:
        errors.append("agent_runtime.trace.enabled must be true")
    if get_path(cfg, "agent_runtime.intent.enabled") is not True:
        errors.append("agent_runtime.intent.enabled must be true")
    if get_path(cfg, "agent_runtime.router.enabled") is not True:
        errors.append("agent_runtime.router.enabled must be true")
    if get_path(cfg, "agent_runtime.batch.enabled") is not True:
        errors.append("agent_runtime.batch.enabled must be true")
    for key in (
        "provider.registry",
        "provider.runtime",
        "agent_runtime.trace.config",
        "agent_runtime.intent.config",
        "agent_runtime.router.config",
        "agent_runtime.batch.config",
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
    if not isinstance(stages, dict) or set(stages) != {"CREATIVE_STORY", "PREIMAGE_COMPILE", "VISUAL_LOCK", "PRODUCTION", "RELEASE"}:
        errors.append("stage_read_sets must declare the five bounded workflow steps")
    else:
        for step, paths in stages.items():
            if not isinstance(paths, list) or not paths or paths[0] != "config/storyos.yaml":
                errors.append(f"stage_read_sets.{step} must start with config/storyos.yaml")
    return errors


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
