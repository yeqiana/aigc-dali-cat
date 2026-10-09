#!/usr/bin/env python3
"""Configured image-payload transport adapter.

Provider selection remains authoritative in image_provider_runtime. This module
only delegates capability preflight to the selected transport so workers and
canaries cannot drift into provider-specific hard-coding.
"""
from __future__ import annotations

import os

import codex_subscription_image
import image_provider_runtime
import openai_images_provider


def selected_route(requested_count: int = 1) -> dict:
    return dict(image_provider_runtime.select_batch_provider(int(requested_count)))


def payload_capability_preflight(*, model: str, quality: str,
                                 codex_raw: str | None = None,
                                 proof_transport_model: str | None = None,
                                 proof_transport_effort: str | None = None) -> dict:
    route = selected_route(1)
    provider = str(route.get("provider") or "")
    explicit_route = str(os.environ.get("STORY_OS_IMAGE_PROVIDER_ROUTE") or "").strip().lower()
    if explicit_route and explicit_route not in {"native_codex", "codex_subscription"}:
        # Hard user contract: native Codex only; no proxy probe or image Attempt.
        return {**route, "provider": provider or None, "status": "BLOCKED",
                "failure_class": "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED",
                "failure_stage": "transport_policy", "transport_route": "opencodex_denied",
                "image_attempt_authority_called": False, "image_generation_called": False}
    if provider == "openai_images_api":
        result = openai_images_provider.payload_capability_preflight(
            model=str(model), quality=str(quality))
    elif provider == "codex_subscription":
        result = codex_subscription_image.payload_capability_preflight(
            model=str(model), quality=str(quality), codex_raw=codex_raw,
            allow_unknown_capability_proof=False)
    elif provider == "product_runtime_image":
        result = {
            "status": "BLOCKED",
            "failure_class": "HOST_ACTION_REQUIRED",
            "provider": provider,
            "host_action_required": True,
        }
    else:
        result = {
            "status": "BLOCKED",
            "failure_class": "NO_AUTOMATABLE_IMAGE_PAYLOAD_PROVIDER",
            "provider": provider or None,
        }
    return {
        **route,
        **result,
        "provider": provider or result.get("provider"),
        **({"transport_route": "native_codex"} if provider == "codex_subscription" and result.get("status") == "PASS" else {}),
    }
