from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"


def _function(filename: str, name: str) -> ast.FunctionDef:
    module = ast.parse((SYSTEM / filename).read_text(encoding="utf-8-sig"))
    matches = [node for node in module.body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1, f"function missing or ambiguous: {filename}:{name}"
    return matches[0]


def test_generation_gateway_provider_is_always_native_codex():
    function = _function("codex_subscription_image.py", "invoke_codex")
    calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)
             and node.func.attr == "provider_generate"]
    assert calls, "image generation must pass through authority gateway"
    for call in calls:
        assert len(call.args) > 3
        provider_arg = call.args[3]
        assert isinstance(provider_arg, ast.Constant)
        assert provider_arg.value == "codex_subscription", (
            "image gateway may not select OpenCodex or another proxy dynamically")


def test_image_worker_capability_exception_requires_phase5a_grant():
    function = _function("image_worker_pool.py", "execute")
    assignments = [node for node in ast.walk(function) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and
                           target.id == "payload_gate_pass" for target in node.targets)]
    assert len(assignments) == 1
    expression = ast.unparse(assignments[0].value).lower()
    assert "phase5a_grant_evidence" in expression
    assert "opencodex" not in expression, (
        "OpenCodex capability proof must never bypass native-only image policy")


def test_transport_diagnostic_is_text_only_not_proxy_image_probe():
    function = _function("codex_subscription_image.py", "_probe_transport_model_diagnostic")
    matches = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "task_type":
                matches.append(kw.value)
    assert matches
    assert all(isinstance(node, ast.Constant) and node.value == "smoke"
               for node in matches), "diagnostic may not change into a proxy image task"

def test_legacy_image_provider_selection_cannot_bypass_native_codex():
    import sys
    from unittest.mock import patch
    if str(SYSTEM) not in sys.path:
        sys.path.insert(0, str(SYSTEM))
    import image_payload_transport

    for provider in ("openai_images_api", "product_runtime_image", "third_party_proxy"):
        with (patch.object(image_payload_transport, "selected_route",
                           return_value={"provider": provider}),
              patch.object(image_payload_transport.codex_subscription_image,
                           "payload_capability_preflight") as native_probe,
              patch.dict(__import__("os").environ, {"STORY_OS_IMAGE_PROVIDER_ROUTE": "native_codex"})):
            result = image_payload_transport.payload_capability_preflight(
                model="image-policy-contract", quality="high")
        assert result["status"] == "BLOCKED"
        assert result["failure_class"] == "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
        assert result["failure_stage"] == "provider_policy"
        assert result["image_attempt_authority_called"] is False
        assert result["image_generation_called"] is False
        native_probe.assert_not_called()
