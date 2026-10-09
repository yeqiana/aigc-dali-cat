"""Non-authoritative registry facade over the existing episode-frozen model_policy.

Requested model names are not actual model identity; no implicit provider fallback.
"""
from __future__ import annotations

import model_policy

CODEX_NATIVE = "CODEX_NATIVE"
API_KEY_DIRECT = "API_KEY_DIRECT"
ALLOWED_TRANSPORTS = frozenset({CODEX_NATIVE, API_KEY_DIRECT})
ROLE_CAPABILITIES = {
    "image.payload": ("image_generation",),
    "vision.fast": ("vision_understanding",),
    "vision.visual_lock": ("vision_understanding",),
    "vision.final": ("vision_understanding",),
    "guardian": ("vision_understanding",),
    "critic.final": ("text_generation", "reasoning"),
    "critic.story": ("text_generation", "reasoning"),
    "critic.preimage": ("text_generation", "reasoning"),
}

def resolve_role(role: str, *, transport: str = CODEX_NATIVE, episode=None) -> dict:
    if not isinstance(role, str) or not role.strip():
        raise ValueError("MODEL_ROLE_REQUIRED")
    if transport not in ALLOWED_TRANSPORTS:
        raise ValueError("MODEL_TRANSPORT_FORBIDDEN")
    bound = model_policy.resolve(role, episode)
    model = str(bound.get("model") or "").strip()
    digest = str(bound.get("model_policy_sha256") or "").strip()
    if not model or not digest:
        raise ValueError("MODEL_BINDING_INCOMPLETE")
    capabilities = ROLE_CAPABILITIES.get(role, ("text_generation",))
    return {
        "role": role,
        "profile": bound["profile"],
        "requested_model": model,
        "policy_sha256": digest,
        "transport": transport,
        "declared_capabilities": list(capabilities),
        "capability_status": "DECLARED",
        "actual_model": None,
        "fallback_automatic": False,
    }
