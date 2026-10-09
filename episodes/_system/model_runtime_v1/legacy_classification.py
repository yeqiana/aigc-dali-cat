"""Classify known legacy routes for removal planning; no modification or dispatch."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LegacyRoute:
    source: str
    route_kind: str
    action: str
    production_route_retired: bool

ROUTES={
    "codex_user_runner": LegacyRoute("codex_user_runner.py", "NATIVE_ONLY_CODEX_CLI",
                                    "VALIDATE_ISOLATED_BRANCH_BEFORE_PRODUCTION_CUTOVER", False),
    "image_payload_transport": LegacyRoute("image_payload_transport.py", "IMAGE_PROVIDER_FANOUT",
                                           "MIGRATE_TO_APPROVED_TWO_TRANSPORTS", False),
    "image_provider_runtime": LegacyRoute("image_provider_runtime.py", "LEGACY_IMAGE_PROVIDER_POLICY",
                                          "HOLD_PENDING_IMAGE_CANARY", False),
    "webcodex_workspace": LegacyRoute("config/storyos.yaml", "WORKSPACE_PROVIDER",
                                      "KEEP_AS_DEVOPS_WORKSPACE_ONLY", False),
    "openai_images_provider": LegacyRoute("openai_images_provider.py", "OFFICIAL_API_DIRECT",
                                         "KEEP_AS_POTENTIAL_API_IMAGE_ADAPTER", False),
}
def classify(name: str) -> dict:
    if name not in ROUTES:
        return {"status":"UNKNOWN","can_delete":False,"reason":"UNCLASSIFIED_SOURCE"}
    route=ROUTES[name]
    return {"status":"REVIEW_REQUIRED","source":route.source,
            "route_kind":route.route_kind,"action":route.action,
            "can_delete":False,"production_route_retired":route.production_route_retired}
