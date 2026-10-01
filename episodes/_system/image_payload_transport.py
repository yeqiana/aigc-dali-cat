#!/usr/bin/env python3
"""Configured image-payload transport adapter.

Provider selection remains authoritative in image_provider_runtime. This module
only delegates capability preflight to the selected transport so workers and
canaries cannot drift into provider-specific hard-coding.
"""
from __future__ import annotations

import codex_subscription_image
import image_provider_runtime
import openai_images_provider


def selected_route(requested_count: int = 1) -> dict:
    return dict(image_provider_runtime.select_batch_provider(int(requested_count)))


def payload_capability_preflight(*, model: str, quality: str,
                                 codex_raw: str | None = None) -> dict:
    route = selected_route(1)
    provider = str(route.get("provider") or "")
    if provider == "openai_images_api":
        result = openai_images_provider.payload_capability_preflight(
            model=str(model), quality=str(quality))
    elif provider == "codex_subscription":
        result = codex_subscription_image.payload_capability_preflight(
            model=str(model), quality=str(quality), codex_raw=codex_raw)
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
    return {**route, **result, "provider": provider or result.get("provider")}
