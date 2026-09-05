#!/usr/bin/env python3
from __future__ import annotations
import json, os
from pathlib import Path
import storyos_config
import runtime_router

ROOT = Path(__file__).resolve().parents[2]
_CFG = storyos_config.load_config()

def load() -> dict:
    rel = storyos_config.get_path(_CFG, "provider.runtime")
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError("provider.runtime missing")
    data = json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("image provider runtime config root must be object")
    return data

def api_key_present() -> bool:
    env = str((load().get("selection") or {}).get("api_key_env") or "OPENAI_API_KEY")
    return bool(os.environ.get(env, "").strip())

def base_url() -> str:
    cfg = load().get("selection") or {}
    env = str(cfg.get("base_url_env") or "OPENAI_BASE_URL")
    raw = os.environ.get(env) or cfg.get("default_base_url") or "https://api.openai.com/v1"
    return str(raw).rstrip("/")

def select_batch_provider(requested_count: int) -> dict:
    cfg = load()
    api = cfg.get("openai_images_api") or {}
    if api.get("enabled") is True and api_key_present():
        maximum = int(api.get("native_n_max") or 10)
        if 1 <= int(requested_count) <= maximum:
            return {
                "provider": "openai_images_api",
                "execution_mode": str(api.get("story_batch_mode") or "native_n_first"),
                "native_multi_image": True,
                "max_images": maximum,
                "reason": "OPENAI_API_KEY present and requested count supported",
            }
    runtime, _ = runtime_router.detect()
    product = cfg.get("product_runtime_image") or {}
    if runtime in set(product.get("runtimes") or []) and product.get("enabled") is True:
        return {
            "provider": "product_runtime_image",
            "execution_mode": "host_action_required",
            "native_multi_image": False,
            "logical_batch": int(requested_count) > 1,
            "max_images": int(requested_count),
            "requested_logical_batch_size": int(requested_count),
            "api_key_required": False,
            "local_codex_fallback": False,
            "host_action_required": True,
            "reason": f"{runtime} selected; product image tool must execute without local Codex fallback",
        }
    codex = cfg.get("codex_subscription") or {}
    if runtime == "CODEX" and codex.get("enabled") is True:
        return {
            "provider": "codex_subscription",
            "execution_mode": "logical_parallel_fanout" if int(requested_count) > 1 else "legacy_bridge",
            "native_multi_image": False,
            "logical_batch": int(requested_count) > 1,
            "max_images": 1,
            "requested_logical_batch_size": int(requested_count),
            "api_key_required": False,
            "reason": "CODEX runtime explicitly selected; use Codex subscription logical batch fan-out",
        }
    raise RuntimeError("NO_IMAGE_PROVIDER_AVAILABLE_WITHOUT_LOCAL_CODEX_FALLBACK")

def capability_snapshot() -> dict:
    cfg = load()
    api = cfg.get("openai_images_api") or {}
    product = cfg.get("product_runtime_image") or {}
    codex = cfg.get("codex_subscription") or {}
    runtime, _ = runtime_router.detect()
    return {
        "schema_version": 1,
        "openai_images_api": {
            "configured": api.get("enabled") is True,
            "credential_available": api_key_present(),
            "native_n_supported": bool(api.get("native_n_supported")),
            "native_n_max": int(api.get("native_n_max") or 10),
            "base_url": base_url(),
        },
        "product_runtime_image": {
            "configured": product.get("enabled") is True,
            "runtime_eligible": runtime in set(product.get("runtimes") or []),
            "host_action_required": bool(product.get("host_action_required")),
            "local_codex_fallback": bool(product.get("local_codex_fallback")),
        },
        "codex_subscription": {
            "configured": codex.get("enabled") is True,
            "runtime_eligible": runtime == "CODEX",
            "native_multi_output_supported": bool(codex.get("native_multi_output_supported")),
            "logical_parallel_fallback": bool(codex.get("logical_parallel_fallback")),
            "logical_batch_api_key_required": False,
        },
        "secret_values_persisted": False,
    }

def self_test() -> None:
    cfg = load()
    assert int((cfg["openai_images_api"])["native_n_max"]) == 10
    assert cfg["security"]["never_persist_api_key"] is True
    print("IMAGE PROVIDER RUNTIME V2.4.1 SELF-TEST PASS")

if __name__ == "__main__":
    self_test()
