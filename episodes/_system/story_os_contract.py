#!/usr/bin/env python3
"""Story OS immutable product-contract helpers.

The product version is read from story_os_manifest.json. Episode stage truth remains
<episode>/meta/episode-state.json; this module does not store mutable episode state.
"""
from __future__ import annotations

import json
from pathlib import Path
import storyos_config

ROOT = Path(__file__).resolve().parents[2]
_CONFIG = storyos_config.load_config()
MANIFEST_REL = Path(str(storyos_config.get_path(_CONFIG, "paths.product_manifest")))
MANIFEST = ROOT / MANIFEST_REL
CANONICAL_STAGES = (
    "IDEA_LOCKED",
    "STORYBOARD_LOCKED",
    "VISUAL_CALIBRATED",
    "PRODUCTION_PASSED",
    "PUBLISH_READY",
    "PUBLISHED",
    "DATA_REVIEWED",
)


def load_contract(root: Path | None = None) -> dict:
    path = (root or ROOT) / MANIFEST_REL
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Story OS manifest missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Story OS manifest invalid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Story OS manifest root must be an object: {path}")
    return data


def story_os_version(root: Path | None = None) -> str:
    value = load_contract(root).get("story_os_version")
    if not isinstance(value, str) or not re_version(value):
        raise RuntimeError(f"story_os_manifest.json has invalid story_os_version: {value!r}")
    return value


def re_version(value: str) -> bool:
    parts = value.split(".")
    return len(parts) >= 3 and all(p.isdigit() for p in parts)


def canonical_stages(root: Path | None = None) -> list[str]:
    data = load_contract(root)
    stages = data.get("stages")
    if list(CANONICAL_STAGES) != stages:
        raise RuntimeError(
            "story_os_manifest.json stages drifted from the immutable seven-stage contract"
        )
    return list(CANONICAL_STAGES)
