#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What was actually in force for this run, and who decided it.

W-96: `STORY_OS_RUNTIME` / `STORY_OS_IMAGE_RUNTIME` / `STORY_OS_VISION_RUNTIME`
let an operator override the runtime, and `runtime_router` already computes both
the value *and* its provenance. But that provenance only ever reached stdout. A
run that took an override and a run that did not produced identical on-disk
evidence, so "the config says CODEX" and "this run used CODEX" were
indistinguishable after the fact.

This writes the resolved value together with the thing that resolved it, so the
question is answerable from evidence:

    {"value": "PRODUCT_RUNTIME", "source": "env:STORY_OS_IMAGE_RUNTIME"}

Two rules the snapshot keeps:

- **No secrets.** Credential-bearing variables are recorded as presence
  (`{"present": true}`), never as values.
- **Derived, never authoritative.** Nothing reads this file back to decide how
  to run. It is a record of a decision already made elsewhere; if it ever
  disagrees with `runtime_router`, the router is right and this file is stale.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import runtime_portability
import runtime_workspace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "episodes/_system") not in sys.path:
    sys.path.insert(0, str(ROOT / "episodes/_system"))

import runtime_router  # noqa: E402
import storyos_config  # noqa: E402
import storage_config  # noqa: E402
import hot_state_bridge  # noqa: E402

REL = Path("meta/runtime/effective-config.json")
SCHEMA_VERSION = 1

YAML = "config/storyos.yaml"

# (snapshot key, config key, env var). The env var is the one runtime_router
# itself honours -- the contract test proves that by flipping it and watching
# both the router and this snapshot move together.
ROUTED = (
    ("runtime", "runtime.preferred_runtime", "STORY_OS_RUNTIME"),
    ("image_execution_runtime", "runtime.image_execution_runtime", "STORY_OS_IMAGE_RUNTIME"),
    ("vision_review_runtime", "runtime.review.vision.runtime", "STORY_OS_VISION_RUNTIME"),
)

# Read straight from the unified entry. Each of these has a real production
# consumer (see tests/system/test_config_consumer_contract.py).
DIRECT = (
    ("local_codex_preimage_workers", "runtime.workers.local_codex_preimage"),
    ("workers_derived", "runtime.workers.derived"),
    ("preimage_parallel_enabled", "runtime.preimage_parallel_enabled"),
    ("max_inflight_images", "production.max_inflight_images"),
)

# W-97: only product rules belong in YAML. They retain env as a one-run override.
CONFIGURABLE_ENV = (
    ("group_reference_proxy", "provider.group_reference_proxy", "STORY_OS_GROUP_REFERENCE_PROXY"),
    ("provider_ratio_crop_exception", "normalize.provider_ratio_crop_exception_enabled", "STORY_OS_PROVIDER_RATIO_CROP_EXCEPTION"),
)

# Deliberate env-only controls: operator transport, recovery/debug, security and
# capability attestation. These are not ordinary product configuration.
ENV_ONLY = (
    ("image_provider_route", "STORY_OS_IMAGE_PROVIDER_ROUTE", "operator_transport_override"),
    ("manual_raw_dir", "STORY_OS_MANUAL_RAW_DIR", "recovery_debug_override"),
    ("allow_codex_full_access", "STORY_OS_ALLOW_CODEX_FULL_ACCESS", "security_opt_in"),
    ("rolling_vision_verified", "STORY_OS_ROLLING_VISION_VERIFIED", "capability_attestation"),
)

# Presence only. These carry credentials or point at them.
SECRET_ENV = ("STORYOS_MYSQL_PWD", "OPENAI_API_KEY", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID")

# W-95: platform stays YAML-independent; application code resolves these and
# injects them. Evidence names either the app-level YAML authority or env override.
_STORAGE_CONFIG = (
    ("runtime_store_mode", "storage.runtime_store.mode", "STORYOS_RUNTIME_STORE_MODE"),
    ("runtime_jsonl_root", "storage.runtime_store.jsonl_root", "STORYOS_RUNTIME_JSONL_ROOT"),
)
_EPISODE_META_STORAGE_CONFIG = (
    ("episode_meta_store_mode", "storage.episode_meta_store.mode", "STORYOS_EPISODE_META_STORE_MODE"),
)
_HOT_STATE_CONFIG = (
    ("hot_state_mode", "storage.hot_state.mode", "STORYOS_HOT_STATE_MODE"),
)


def _truthy(raw: str) -> bool:
    return str(raw).strip().lower() in {"1", "true", "on", "yes"}


def snapshot() -> dict:
    """Resolve every steered value to (value, source). Pure; writes nothing."""
    cfg = storyos_config.load_config()
    out: dict = {"schema_version": SCHEMA_VERSION, "sources": {}}
    sources = out["sources"]

    for name, key, env_var in ROUTED:
        override = os.environ.get(env_var, "").strip()
        if override:
            sources[name] = {"value": override.upper(), "source": f"env:{env_var}"}
        else:
            declared = storyos_config.get_path(cfg, key)
            sources[name] = {
                "value": str(declared).upper() if isinstance(declared, str) else declared,
                "source": f"{YAML}#{key}",
            }

    for name, key in DIRECT:
        sources[name] = {"value": storyos_config.get_path(cfg, key), "source": f"{YAML}#{key}"}

    for name, key, env_var in CONFIGURABLE_ENV:
        raw = os.environ.get(env_var, "").strip()
        if raw:
            sources[name] = {"value": _truthy(raw), "source": f"env:{env_var}"}
        else:
            sources[name] = {"value": storyos_config.get_path(cfg, key), "source": f"{YAML}#{key}"}

    for name, env_var, classification in ENV_ONLY:
        raw = os.environ.get(env_var)
        if raw is None or not str(raw).strip():
            sources[name] = {"value": None, "source": f"env:{env_var} (unset)", "classification": classification}
        else:
            # STORY_OS_MANUAL_RAW_DIR holds a path, the rest are on/off switches.
            value: object = str(raw) if env_var.endswith("_DIR") else _truthy(raw)
            sources[name] = {"value": value, "source": f"env:{env_var}", "classification": classification}

    resolved_store = storage_config.runtime_store_config()
    for name, key, env_var in _STORAGE_CONFIG:
        raw = os.environ.get(env_var, "").strip()
        if raw:
            sources[name] = {"value": raw, "source": f"env:{env_var}"}
        else:
            value = resolved_store["mode" if name == "runtime_store_mode" else "jsonl_root"]
            sources[name] = {"value": value, "source": f"{YAML}#{key}"}

    resolved_episode_meta = storage_config.episode_meta_store_config()
    for name, key, env_var in _EPISODE_META_STORAGE_CONFIG:
        raw = os.environ.get(env_var, "").strip()
        sources[name] = {
            "value": raw if raw else resolved_episode_meta["mode"],
            "source": f"env:{env_var}" if raw else f"{YAML}#{key}",
        }

    resolved_hot_state = storage_config.hot_state_config()
    for name, key, env_var in _HOT_STATE_CONFIG:
        raw = os.environ.get(env_var, "").strip()
        sources[name] = {
            "value": raw if raw else resolved_hot_state["mode"],
            "source": f"env:{env_var}" if raw else f"{YAML}#{key}",
        }

    out["credential_presence"] = {
        name: {"present": bool(os.environ.get(name, "").strip())} for name in SECRET_ENV
    }
    # The headline question a reader has after the fact: did this run follow the
    # config file, or did something override it?
    out["overrides_in_force"] = sorted(
        row["source"].split(":", 1)[1] for _, row in sources.items()
        if str(row["source"]).startswith("env:") and not str(row["source"]).endswith("(unset)")
    )
    return out


def write(ep) -> dict:
    ep = Path(ep).resolve()
    runtime_portability.assert_episode_directory(ep)
    data = snapshot()
    runtime_workspace.write_json(ep, REL, data)
    hot_state_bridge.mirror(ep, "EFFECTIVE_CONFIG", data)
    return data


def load(ep) -> dict:
    """Read Redis projection first in dual mode, then compatibility file."""
    ep = Path(ep).resolve()
    hot = hot_state_bridge.read(ep, "EFFECTIVE_CONFIG")
    value = hot_state_bridge.value_or_fallback(
        hot,
        lambda: runtime_workspace.read_json(ep, REL, default={}),
        default={},
    )
    return value if isinstance(value, dict) else {}


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(write(sys.argv[1]), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
