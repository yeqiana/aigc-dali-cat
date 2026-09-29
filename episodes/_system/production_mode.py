"""Resolve the top-level StoryOS production mode and legacy runtime overrides."""
from __future__ import annotations

import os

import storyos_config

MODES = {"COLLABORATIVE", "CODEX_MANAGED"}
RUNTIMES = {"WORK", "WEB", "CODEX"}


def resolve(cfg: dict | None = None) -> dict:
    """Return configured/effective mode and runtime with explicit provenance.

    STORY_OS_PRODUCTION_MODE is the only normal production-mode override.
    STORY_OS_RUNTIME remains a temporary low-level compatibility/debug override.
    Neither host availability nor the presence of a Codex binary changes mode.
    """
    cfg = cfg or storyos_config.load_config()
    configured = str(storyos_config.get_path(cfg, "production.mode") or "").strip().upper()
    if configured not in MODES:
        raise ValueError(f"production.mode must be one of {', '.join(sorted(MODES))}")

    production_override = os.getenv("STORY_OS_PRODUCTION_MODE", "").strip().upper()
    if production_override:
        if production_override not in MODES:
            raise ValueError(f"invalid STORY_OS_PRODUCTION_MODE: {production_override!r}")
        effective_mode = production_override
        effective_runtime = "CODEX" if effective_mode == "CODEX_MANAGED" else "WORK"
        source = "env:STORY_OS_PRODUCTION_MODE"
    else:
        legacy_runtime = os.getenv("STORY_OS_RUNTIME", "").strip().upper()
        if legacy_runtime in RUNTIMES:
            effective_runtime = legacy_runtime
            effective_mode = "CODEX_MANAGED" if legacy_runtime == "CODEX" else "COLLABORATIVE"
            source = "env:STORY_OS_RUNTIME"
        else:
            effective_mode = configured
            effective_runtime = "CODEX" if configured == "CODEX_MANAGED" else "WORK"
            source = "config/storyos.yaml#production.mode"

    return {
        "configured_mode": configured,
        "effective_mode": effective_mode,
        "effective_runtime": effective_runtime,
        "source": source,
        "production_mode_override": production_override or None,
        "legacy_runtime_override": (
            os.getenv("STORY_OS_RUNTIME", "").strip().upper()
            if not production_override and os.getenv("STORY_OS_RUNTIME", "").strip().upper() in RUNTIMES
            else None
        ),
        "automatic_runtime_fallback": False,
    }
