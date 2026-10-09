from __future__ import annotations
import sys
from pathlib import Path
from unittest import mock
import pytest
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
from model_runtime_v1 import registry

def test_existing_policy_is_reused():
    row = registry.resolve_role("story.authoring")
    assert row["profile"] == "authoring"
    assert len(row["policy_sha256"]) == 64
    assert row["capability_status"] == "DECLARED"
    assert row["actual_model"] is None

def test_roles_declare_distinct_capabilities():
    assert registry.resolve_role("image.payload")["declared_capabilities"] == ["image_generation"]
    assert registry.resolve_role("vision.final")["declared_capabilities"] == ["vision_understanding"]

@pytest.mark.parametrize("bad", ["opencodex", "webcodex", "AUTO", "product_runtime_image", ""])
def test_forbidden_transport_rejected_before_policy_lookup(bad):
    with mock.patch.object(registry.model_policy, "resolve", side_effect=AssertionError("policy called")):
        with pytest.raises(ValueError, match="MODEL_TRANSPORT_FORBIDDEN"):
            registry.resolve_role("image.payload", transport=bad)

def test_frozen_episode_policy_is_respected():
    with mock.patch.object(registry.model_policy, "resolve", return_value={
        "profile": "authoring", "model": "frozen", "model_policy_sha256": "a"*64}) as fn:
        row = registry.resolve_role("story.authoring", episode="/episode")
    fn.assert_called_once_with("story.authoring", "/episode")
    assert row["requested_model"] == "frozen"

def test_explicit_api_binding_never_auto_fallback():
    with mock.patch.object(registry.model_policy, "resolve", return_value={
        "profile": "authoring", "model": "requested", "model_policy_sha256": "a"*64}):
        row = registry.resolve_role("story.authoring", transport="API_KEY_DIRECT")
    assert row["transport"] == "API_KEY_DIRECT"
    assert row["fallback_automatic"] is False
