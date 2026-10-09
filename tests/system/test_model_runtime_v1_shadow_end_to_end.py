from __future__ import annotations
import hashlib
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
from model_runtime_v1 import registry, capability, adapters, ledger_view

def _attestation(binding):
    return {"role":binding["role"],"requested_model":binding["requested_model"],
            "transport":binding["transport"],"policy_sha256":binding["policy_sha256"],
            "capabilities":["text_generation"],"attestation_kind":"SESSION_TOOL_REGISTRY",
            "expires_at":(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat()}

def test_shadow_request_cannot_dispatch_without_trusted_proof_or_operator_authorization():
    binding=registry.resolve_role("story.authoring")
    assert capability.resolve(binding)["available"] is False
    with pytest.raises(adapters.TransportDispatchBlocked,match="NOT_ATTESTED"):
        adapters.plan_text(binding)
    plan=adapters.plan_text(binding,proof=_attestation(binding),
                            trusted_verify=lambda _:True)
    with pytest.raises(adapters.TransportDispatchBlocked,match="NOT_AUTHORIZED"):
        adapters.dispatch_codex_text(plan,prompt="no model invocation")
    envelope=ledger_view.new_execution(binding,input_sha256=hashlib.sha256(b"prompt").hexdigest())
    assert envelope["status"]=="PLANNED"
    assert envelope["actual_model"] is None
    assert envelope["review_authority_granted"] is False

def test_api_key_cannot_be_reached_with_default_codex_transport():
    binding=registry.resolve_role("story.authoring")
    plan=adapters.plan_text(binding,proof=_attestation(binding),trusted_verify=lambda _:True)
    with pytest.raises(adapters.TransportDispatchBlocked,match="TRANSPORT_MISMATCH"):
        adapters.dispatch_openai_text(plan,prompt="test",authorized=True,api_key="fake")

def test_unspecified_image_runtime_is_not_silently_routed_via_text():
    binding=registry.resolve_role("image.payload")
    with pytest.raises(adapters.TransportDispatchBlocked,match="MODALITY_UNSUPPORTED"):
        adapters.plan_text(binding,proof=None)
