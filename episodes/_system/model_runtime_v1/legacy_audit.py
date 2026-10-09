"""Read-only scanner for legacy model routes; evidence is not safe-delete proof."""
from __future__ import annotations
from pathlib import Path

SOURCES = {
    "episodes/_system/codex_user_runner.py": ("_opencodex_health", "_opencodex_image_capability", "_opencodex_base_url", "\"transport_route\": \"opencodex\""),
    "episodes/_system/codex_subscription_image.py": ("_codex_http_only_provider_args", "model_providers.storyos_http"),
    "episodes/_system/image_payload_transport.py": ("product_runtime_image", "openai_images_api"),
    "config/providers/image-provider-runtime.json": ("product_runtime_image", "fallback_on_transport_failure"),
    "config/storyos.yaml": ("webcodex", "PRODUCT_RUNTIME"),
}

def scan(root: str | Path) -> dict:
    root = Path(root)
    findings = []
    for rel, patterns in SOURCES.items():
        file = root / rel
        if not file.is_file():
            findings.append({"path": rel, "status": "MISSING", "hit_count": 0})
            continue
        lines = file.read_text(encoding="utf-8-sig").splitlines()
        hits = [i for i, line in enumerate(lines, 1)
                if any(term.casefold() in line.casefold() for term in patterns)]
        findings.append({"path": rel,
                         "status": "REVIEW_REQUIRED" if hits else "NO_LEGACY_HIT",
                         "hit_count": len(hits), "line_numbers": hits[:40]})
    return {"mode": "READ_ONLY", "production_route_verified": False,
            "safe_to_remove_code": False, "findings": findings}
