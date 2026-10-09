from __future__ import annotations
import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
from unittest import mock
import pytest
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
from model_runtime_v1 import adapters

B = {"transport": "CODEX_NATIVE", "role": "story.authoring", "requested_model": "requested",
     "policy_sha256": "a"*64, "declared_capabilities": ["text_generation"]}
def _proof(binding):
    return {"role": binding["role"], "requested_model": binding["requested_model"],
            "transport": binding["transport"], "policy_sha256": binding["policy_sha256"],
            "capabilities": ["text_generation"], "attestation_kind": "SESSION_TOOL_REGISTRY",
            "expires_at": (datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()}

def _plan(binding):
    return adapters.plan_text(binding, proof=_proof(binding), trusted_verify=lambda _: True)

def test_text_plan_requires_proven_capability_and_two_allowed_transports():
    with pytest.raises(adapters.TransportDispatchBlocked, match="NOT_ATTESTED"):
        adapters.plan_text(B)
    with pytest.raises(adapters.TransportDispatchBlocked, match="FORBIDDEN"):
        _plan({**B, "transport": "opencodex"})
    assert _plan(B)["fallback_automatic"] is False

def test_codex_native_explicit_pinning_and_env_clearing():
    plan = _plan(B)
    called = []
    def stub(argv, **kw):
        called.append((argv, kw))
        return subprocess.CompletedProcess(argv, 0, stdout=b'{"type":"turn.completed"}\n', stderr=b'')
    with mock.patch.dict(os.environ, {"OPENAI_BASE_URL": "http://127.0.0.1:10100/v1"}):
        result = adapters.dispatch_codex_text(plan, prompt="hello", authorized=True, runner=stub)
    argv, kw = called[0]
    assert any(adapters.NATIVE_CODEX_BASE in part for part in argv)
    assert "OPENAI_BASE_URL" not in kw["env"]
    assert kw["task_type"] == "generic_codex"
    assert result["status"] == "REQUIRES_VALIDATION"
    assert result["actual_model"] is None

def test_no_calls_before_authorization():
    plan = _plan(B)
    with pytest.raises(adapters.TransportDispatchBlocked, match="NOT_AUTHORIZED"):
        adapters.dispatch_codex_text(plan, prompt="hello", runner=lambda *a, **k: pytest.fail("called"))
    with pytest.raises(adapters.TransportDispatchBlocked, match="NOT_AUTHORIZED"):
        adapters.dispatch_openai_text({**plan, "transport": "API_KEY_DIRECT"}, prompt="hello",
                                     api_key="secret", sender=lambda *a, **k: pytest.fail("called"))

def test_direct_api_fixed_official_url_and_no_key_in_result():
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    captured = []
    def sender(req, timeout):
        captured.append((req, timeout))
        return json.dumps({"id": "resp-123", "model": "provider-reported"}).encode()
    with mock.patch.dict(os.environ, {"OPENAI_BASE_URL": "http://127.0.0.1:10100/v1"}):
        result = adapters.dispatch_openai_text(plan, prompt="test", authorized=True,
                                               api_key="unit-test-secret", sender=sender)
    assert captured[0][0].full_url == "https://api.openai.com/v1/responses"
    assert captured[0][0].get_header("Authorization") == "Bearer unit-test-secret"
    assert "unit-test-secret" not in repr(result)
    assert result["reported_model"] == "provider-reported"
    assert result["actual_model"] is None

def test_api_transport_failure_is_unknown_not_retryable_success():
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    def sender(req, timeout):
        raise RuntimeError("secret-key-should-never-leak")
    with pytest.raises(adapters.TransportDispatchBlocked, match="^API_DIRECT_OUTCOME_UNKNOWN$") as caught:
        adapters.dispatch_openai_text(plan, prompt="test", authorized=True,
                                     api_key="secret-key-should-never-leak", sender=sender)
    assert "secret-key" not in str(caught.value)

def test_image_modality_must_use_existing_image_adapter_not_text():
    with pytest.raises(adapters.TransportDispatchBlocked, match="MODALITY_UNSUPPORTED"):
        _plan({**B, "declared_capabilities": ["image_generation"]})
