#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StoryOS local-vision runtime health/readiness report."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import grounding_dino_provider
import isolated_ml_runtime
import local_vision_provision
import perceptual_similarity_provider
import pose_diagnostic_provider
import sam2_mask_provider
import storyos_config

ROOT = Path(__file__).resolve().parents[2]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sidecar_runtime() -> dict:
    return isolated_ml_runtime.runtime_probe()


def _provider_row(name: str, config: dict, available) -> dict:
    enabled = config.get("enabled") is True
    row = {"enabled": enabled}
    if not enabled:
        row.update({"ready": False, "reason": "DISABLED"})
        return row
    result = available(config)
    row.update({
        "ready": result.get("available") is True,
        "reason": result.get("reason"),
        "detail": result.get("detail"),
        "model_path": result.get("model_path") or config.get("model_path"),
    })
    return row


def snapshot() -> dict:
    cfg = storyos_config.load_config()
    triage = storyos_config.get_path(cfg, "production.local_visual_triage", {}) or {}
    dependencies = isolated_ml_runtime.dependency_status(
        ("torch", "transformers", "onnxruntime", "lpips", "cv2", "PIL")
    )
    providers = {
        "grounding_dino": _provider_row(
            "grounding_dino", triage.get("grounding_dino") or {}, grounding_dino_provider.available
        ),
        "sam2": _provider_row("sam2", triage.get("sam2") or {}, sam2_mask_provider.available),
        "pose": _provider_row("pose", triage.get("pose") or {}, pose_diagnostic_provider.available),
        "lpips": _provider_row("lpips", triage.get("lpips") or {}, perceptual_similarity_provider.available),
    }
    enabled = [name for name, row in providers.items() if row["enabled"]]
    ready = [name for name, row in providers.items() if row["enabled"] and row["ready"]]
    return {
        "schema_version": 1,
        "generated_at": now(),
        "sidecar_runtime": sidecar_runtime(),
        "sidecar_dependencies": dependencies,
        "model_cache": local_vision_provision.status()["models"],
        "providers": providers,
        "summary": {
            "enabled_heavy_provider_count": len(enabled),
            "ready_enabled_heavy_provider_count": len(ready),
            "enabled_heavy_providers": enabled,
            "ready_enabled_heavy_providers": ready,
            "production_heavy_models_active": bool(enabled and len(enabled) == len(ready)),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    report = snapshot()
    print(json.dumps(report, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
