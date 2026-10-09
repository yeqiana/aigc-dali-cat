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


def _native_success(argv, *, output=b'{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n{"type":"turn.completed"}\n'):
    result = subprocess.CompletedProcess(argv, 0, stdout=output, stderr=b'')
    result.remote = {"transport_route": "native_codex",
                     "transport_base_url": adapters.NATIVE_CODEX_BASE,
                     "timed_out": False}
    return result

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
        return _native_success(argv)
    with mock.patch.dict(os.environ, {"OPENAI_BASE_URL": "http://127.0.0.1:10100/v1"}):
        result = adapters.dispatch_codex_text(plan, prompt="hello", authorized=True, runner=stub)
    argv, kw = called[0]
    assert any(adapters.NATIVE_CODEX_BASE in part for part in argv)
    assert 'model_provider="openai"' in argv
    assert "OPENAI_BASE_URL" not in kw["env"]
    assert kw["env"]["STORY_OS_MODEL_TRANSPORT_POLICY"] == "DUAL_ONLY"
    assert kw["task_type"] == "generic_codex"
    assert result["status"] == "REQUIRES_VALIDATION"
    assert result["actual_model"] is None
    assert result["output_text"] == "ok"

def test_no_calls_before_authorization():
    plan = _plan(B)
    with pytest.raises(adapters.TransportDispatchBlocked, match="NOT_AUTHORIZED"):
        adapters.dispatch_codex_text(plan, prompt="hello", runner=lambda *a, **k: pytest.fail("called"))
    with pytest.raises(adapters.TransportDispatchBlocked, match="NOT_AUTHORIZED"):
        adapters.dispatch_openai_text(_plan({**B, "transport": "API_KEY_DIRECT"}), prompt="hello",
                                     api_key="secret", sender=lambda *a, **k: pytest.fail("called"))

def test_direct_api_fixed_official_url_and_no_key_in_result():
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    captured = []
    def sender(req, timeout):
        captured.append((req, timeout))
        return json.dumps({"id": "resp_123", "status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}], "model": "provider-reported"}).encode()
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

def test_forged_plan_cannot_dispatch_to_native_or_api():
    fake = {"transport": "CODEX_NATIVE", "modality": "text_generation",
            "verified_capability": True, "requested_model": "requested"}
    with pytest.raises(adapters.TransportDispatchBlocked, match="PLAN_UNTRUSTED"):
        adapters.dispatch_codex_text(fake, prompt="hello", authorized=True,
                                     runner=lambda *a, **kw: pytest.fail("ran"))
    with pytest.raises(adapters.TransportDispatchBlocked, match="PLAN_UNTRUSTED"):
        adapters.dispatch_openai_text({**fake, "transport": "API_KEY_DIRECT"},
                                     prompt="hello", authorized=True, api_key="fake",
                                     sender=lambda *a, **kw: pytest.fail("ran"))

def test_issued_plan_is_immutable_and_cannot_be_elevated_by_editing():
    plan = _plan(B)
    with pytest.raises(TypeError):
        plan["transport"] = "API_KEY_DIRECT"
    with pytest.raises(AttributeError, match="PLAN_IMMUTABLE"):
        plan._fields = {"transport": "API_KEY_DIRECT"}

def test_native_uses_input_for_both_direct_and_bridge_modes():
    plan = _plan(B)
    seen = []
    def stub(argv, **kw):
        seen.append(kw)
        return _native_success(argv)
    adapters.dispatch_codex_text(plan, prompt="你好，世界", authorized=True, runner=stub)
    assert seen[0]["input"] == "你好，世界"
    assert seen[0]["text"] is True
    assert seen[0]["encoding"] == "utf-8"
    assert "stdin_text" not in seen[0]

def test_codex_empty_output_must_not_claim_success():
    plan = _plan(B)
    with pytest.raises(adapters.TransportDispatchBlocked, match="NATIVE_EMPTY_OUTPUT"):
        adapters.dispatch_codex_text(plan, prompt="hello", authorized=True,
            runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b""))

def test_api_http_unauthorized_is_sanitized_definite_refusal():
    from urllib.error import HTTPError
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    def sender(req, timeout):
        raise HTTPError(req.full_url, 401, "forbidden-secret", {}, None)
    with pytest.raises(adapters.TransportDispatchBlocked, match="^API_DIRECT_REQUEST_REJECTED$") as caught:
        adapters.dispatch_openai_text(plan, prompt="test", authorized=True, sender=sender,
                                     api_key="secret")
    assert "forbidden-secret" not in str(caught.value)

def test_api_incomplete_response_cannot_claim_success():
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    def sender(req, timeout):
        return json.dumps({"id": "resp_123", "status": "incomplete", "model": "requested"}).encode()
    with pytest.raises(adapters.TransportDispatchBlocked, match="RESPONSE_NOT_COMPLETE"):
        adapters.dispatch_openai_text(plan, prompt="test", authorized=True, sender=sender,
                                     api_key="secret")

def test_api_completed_response_requires_output_text():
    plan = _plan({**B,"transport":"API_KEY_DIRECT"})
    def sender(req, timeout):
        return json.dumps({"id":"resp_123","status":"completed","output":[]}).encode()
    with pytest.raises(adapters.TransportDispatchBlocked,match="OUTPUT_NOT_VERIFIED"):
        adapters.dispatch_openai_text(plan,prompt="hi",authorized=True,api_key="fake",sender=sender)

def test_api_pending_is_not_success_and_preserves_reconciliation_id():
    plan = _plan({**B,"transport":"API_KEY_DIRECT"})
    def sender(req, timeout):
        return json.dumps({"id":"resp_123","status":"in_progress"}).encode()
    row=adapters.dispatch_openai_text(plan,prompt="hi",authorized=True,api_key="fake",sender=sender)
    assert row["status"]=="PENDING_RECONCILIATION"
    assert row["provider_response_id"]=="resp_123"
    assert row["actual_model"] is None

def test_api_missing_status_never_claims_completion():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    with pytest.raises(adapters.TransportDispatchBlocked,match="RESPONSE_NOT_COMPLETE"):
        adapters.dispatch_openai_text(plan,prompt="hi",authorized=True,api_key="fake",
            sender=lambda req,timeout:json.dumps({"id":"resp_123"}).encode())

def test_codex_native_rejects_proven_wrong_upstream_route():
    plan = _plan(B)
    def stub(argv, **kw):
        result=subprocess.CompletedProcess(argv, 0, stdout=b'{"type":"turn.completed"}\n', stderr=b'')
        result.remote={"transport_route":"opencodex", "transport_base_url":"http://127.0.0.1:10100/v1", "timed_out":False}
        return result
    with pytest.raises(adapters.TransportDispatchBlocked,match="NATIVE_ROUTE_UNVERIFIED"):
        adapters.dispatch_codex_text(plan,prompt="hello",authorized=True,runner=stub)

def test_codex_remote_completion_is_only_observed_not_model_attested():
    plan = _plan(B)
    def stub(argv, **kw):
        result=_native_success(argv)
        return result
    row=adapters.dispatch_codex_text(plan,prompt="hello",authorized=True,runner=stub)
    assert row["native_runtime_evidence"]["status"]=="OBSERVED"
    assert row["actual_model"] is None
    assert row["native_runtime_evidence"]["tool_session_attested"] is False

def test_direct_api_redirect_is_blocked_without_leaking_credentials():
    from urllib.error import HTTPError
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    def redirect(req, timeout):
        raise HTTPError(req.full_url, 307, "temporary redirect", {"Location": "https://evil.example"}, None)
    with pytest.raises(adapters.TransportDispatchBlocked, match="API_DIRECT_REDIRECT_FORBIDDEN"):
        adapters.dispatch_openai_text(plan, prompt="hello", authorized=True,
                                     api_key="private-credential", sender=redirect)

def test_direct_api_rejects_oversized_and_empty_identity_responses():
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    with pytest.raises(adapters.TransportDispatchBlocked, match="API_DIRECT_OUTCOME_UNKNOWN"):
        adapters.dispatch_openai_text(plan, prompt="hello", authorized=True, api_key="private",
                                     sender=lambda req, timeout: b"X"*(adapters.MAX_API_RESPONSE_BYTES+1))
    with pytest.raises(adapters.TransportDispatchBlocked, match="API_DIRECT_OUTCOME_UNKNOWN"):
        adapters.dispatch_openai_text(plan, prompt="hello", authorized=True, api_key="private",
                                     sender=lambda req, timeout: b'{"id":"","status":"completed"}')

def test_default_sender_does_not_inherit_environment_proxy_or_follow_redirect():
    from contextlib import contextmanager
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    created = []
    class Opener:
        @contextmanager
        def open(self, req, timeout=None):
            created.append(("request", req.full_url))
            class Reply:
                def read(self, size):
                    return json.dumps({"id":"resp_xyz","status":"completed",
                        "output":[{"type":"message","content":[{"type":"output_text","text":"ok"}]}]}).encode()
            yield Reply()
    def build(*handlers):
        created.extend(handlers)
        return Opener()
    with (mock.patch.dict(os.environ, {"STORY_OS_MODEL_RUNTIME_V1_REAL_DISPATCH": "1"}),
          mock.patch.object(adapters.request, "build_opener", side_effect=build)):
        result = adapters.dispatch_openai_text(plan,prompt="ok",authorized=True,api_key="fake")
    assert result["provider_response_id"] == "resp_xyz"
    assert any(isinstance(x, adapters.request.ProxyHandler) and x.proxies == {} for x in created)
    assert any(isinstance(x, adapters._RejectRedirect) for x in created)
    assert ("request", adapters.OPENAI_RESPONSES_URL) in created

def test_native_missing_runner_provenance_fails_closed():
    plan = _plan(B)
    def missing_provenance(argv, **kw):
        return subprocess.CompletedProcess(argv, 0,
                                          stdout=b'{"type":"turn.completed"}\n', stderr=b'')
    with pytest.raises(adapters.TransportDispatchBlocked, match="CODEX_NATIVE_PROVENANCE_UNVERIFIED"):
        adapters.dispatch_codex_text(plan, prompt="hello", authorized=True,
                                     runner=missing_provenance)

def test_api_response_reconciliation_get_does_not_repeat_post():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    observed=[]
    def sender(req,timeout):
        observed.append((req.get_method(),req.full_url))
        return json.dumps({"id":"resp_ABC-1","status":"completed",
            "output":[{"type":"message","content":[{"type":"output_text","text":"ok"}]}]}).encode()
    row=adapters.reconcile_openai_text(plan,response_id="resp_ABC-1",
                                     authorized=True,api_key="fake",sender=sender)
    assert observed==[("GET","https://api.openai.com/v1/responses/resp_ABC-1")]
    assert row["status"]=="REQUIRES_VALIDATION"
    assert row["actual_model"] is None

def test_api_reconciliation_pending_is_safe_and_never_dispatches_new_model():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    row=adapters.reconcile_openai_text(plan,response_id="resp_ABC",
        authorized=True,api_key="fake",
        sender=lambda req,timeout:json.dumps({"id":"resp_ABC","status":"in_progress"}).encode())
    assert row["status"]=="PENDING_RECONCILIATION"

def test_api_reconciliation_cannot_use_injected_url_or_wrong_id():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    for bad in ("../../secret","https://evil.invalid","resp_ABC/../other"):
        with pytest.raises(adapters.TransportDispatchBlocked,match="ID_INVALID"):
            adapters.reconcile_openai_text(plan,response_id=bad,authorized=True,
                api_key="fake",sender=lambda *args:pytest.fail("network"))
    with pytest.raises(adapters.TransportDispatchBlocked,match="LOOKUP_OUTCOME_UNKNOWN"):
        adapters.reconcile_openai_text(plan,response_id="resp_ABC",authorized=True,api_key="fake",
            sender=lambda *args:json.dumps({"id":"resp_WRONG","status":"completed"}).encode())

def test_api_reconciliation_requires_authorization():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    with pytest.raises(adapters.TransportDispatchBlocked,match="NOT_AUTHORIZED"):
        adapters.reconcile_openai_text(plan,response_id="resp_ABC",api_key="fake",
            sender=lambda *args:pytest.fail("network"))

def test_native_terminal_event_without_text_cannot_complete_text_contract():
    plan=_plan(B)
    with pytest.raises(adapters.TransportDispatchBlocked,match="CODEX_NATIVE_TEXT_OUTPUT_MISSING"):
        adapters.dispatch_codex_text(plan,prompt="hello",authorized=True,
            runner=lambda argv,**kw:_native_success(argv,output=b'{"type":"turn.completed"}\n'))

def test_api_text_output_is_returned_for_downstream_validation():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    payload={"id":"resp_test","status":"completed","output":[
       {"type":"message","content":[{"type":"output_text","text":"第一段"},
                                    {"type":"output_text","text":"第二段"}]}]}
    row=adapters.dispatch_openai_text(plan,prompt="hello",authorized=True,api_key="fake",
        sender=lambda req,timeout:json.dumps(payload,ensure_ascii=False).encode())
    assert row["output_text"]=="第一段\n第二段"
    assert row["status"]=="REQUIRES_VALIDATION"

def test_api_get_reconciliation_returns_original_text_not_new_inference():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    row=adapters.reconcile_openai_text(plan,response_id="resp_abc",
        authorized=True,api_key="fake",
        sender=lambda req,timeout:json.dumps({"id":"resp_abc","status":"completed",
           "output":[{"type":"message","content":[{"type":"output_text","text":"already done"}]}]}).encode())
    assert row["output_text"]=="already done"

def test_api_post_rejects_ids_that_cannot_be_reconciled():
    plan = _plan({**B, "transport": "API_KEY_DIRECT"})
    for bad in ("resp-other", "http://example.test/x", "resp_x/../y", "  "):
        with pytest.raises(adapters.TransportDispatchBlocked, match="API_DIRECT_OUTCOME_UNKNOWN"):
            adapters.dispatch_openai_text(plan, prompt="hi", authorized=True, api_key="fake",
                sender=lambda req, timeout: json.dumps({"id":bad,"status":"completed",
                    "output":[{"type":"message","content":[{"type":"output_text","text":"ok"}]}]}).encode())


def test_real_model_transports_remain_disabled_until_explicit_cutover():
    native = _plan(B)
    api = _plan({**B, "transport": "API_KEY_DIRECT"})
    with mock.patch.dict(os.environ, {"STORY_OS_MODEL_RUNTIME_V1_REAL_DISPATCH":""}):
        with pytest.raises(adapters.TransportDispatchBlocked,match="REAL_DISPATCH_DISABLED"):
            adapters.dispatch_codex_text(native,prompt="hello",authorized=True,runner=None)
        with pytest.raises(adapters.TransportDispatchBlocked,match="REAL_DISPATCH_DISABLED"):
            adapters.dispatch_openai_text(api,prompt="hello",authorized=True,
                                          api_key="not-a-real-key",sender=None)
        with pytest.raises(adapters.TransportDispatchBlocked,match="REAL_DISPATCH_DISABLED"):
            adapters.reconcile_openai_text(api,response_id="resp_demo",authorized=True,
                                            api_key="not-a-real-key",sender=None)

def test_post_error_is_not_pending_even_if_status_queued():
    plan = _plan({**B,"transport":"API_KEY_DIRECT"})
    with pytest.raises(adapters.TransportDispatchBlocked, match="RESPONSE_NOT_COMPLETE"):
        adapters.dispatch_openai_text(plan, prompt="hello", authorized=True, api_key="fake",
            sender=lambda req,timeout:json.dumps({"id":"resp_abc","status":"queued",
                "error":{"code":"provider_rejected"}}).encode())

def test_get_error_is_non_success_even_if_status_pending():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    result=adapters.reconcile_openai_text(plan,response_id="resp_abc",authorized=True,
        api_key="fake",sender=lambda req,timeout:json.dumps({"id":"resp_abc",
            "status":"in_progress","error":{"code":"provider_failed"}}).encode())
    assert result["status"]=="RECONCILED_NON_SUCCESS"
    assert result["actual_model"] is None

def test_api_provider_model_identity_mismatch_is_not_marked_attested():
    plan=_plan({**B,"transport":"API_KEY_DIRECT"})
    result=adapters.dispatch_openai_text(plan,prompt="hello",authorized=True,api_key="fake",
        sender=lambda req,timeout:json.dumps({"id":"resp_abc","status":"completed",
            "model":"unexpected-model",
            "output":[{"type":"message","content":[{"type":"output_text","text":"ok"}]}]}).encode())
    assert result["actual_model"] is None
    assert result["reported_model_matches_request"] is False
    assert result["status"]=="REQUIRES_VALIDATION"
