from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
from model_runtime_v1 import capability

B = {"role": "image.payload", "requested_model": "requested", "transport": "CODEX_NATIVE",
     "policy_sha256": "a"*64, "declared_capabilities": ["image_generation"]}

def proof():
    return {"role": "image.payload", "requested_model": "requested", "transport": "CODEX_NATIVE",
            "policy_sha256": "a"*64, "capabilities": ["image_generation"],
            "attestation_kind": "SESSION_TOOL_REGISTRY",
            "expires_at": (datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),
            "passed": True}

def test_declared_is_not_available():
    assert capability.resolve(B)["status"] == "DECLARED"
    assert capability.resolve(B, proof=proof())["available"] is False

def test_wrong_scope_cannot_be_promoted():
    p = proof()
    p["role"] = "vision.final"
    assert capability.resolve(B, proof=p, trusted_verify=lambda _: True)["status"] == "BLOCKED"

def test_expired_or_missing_expiry_blocked():
    p = proof()
    p["expires_at"] = (datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()
    assert capability.resolve(B, proof=p, trusted_verify=lambda _: True)["reason"] == "MODEL_CAPABILITY_PROOF_EXPIRED"
    del p["expires_at"]
    assert capability.resolve(B, proof=p, trusted_verify=lambda _: True)["reason"] == "MODEL_CAPABILITY_PROOF_EXPIRY_MISSING"

def test_requires_external_verifier_even_if_self_pass():
    assert capability.resolve(B, proof=proof(), trusted_verify=lambda _: False)["available"] is False
    assert capability.resolve(B, proof=proof(), trusted_verify=lambda _: True)["status"] == "AVAILABLE"

def test_undeclared_capability_blocked():
    assert capability.resolve(B, required={"tool_calling"}, proof=proof(), trusted_verify=lambda _: True)["reason"] == "MODEL_CAPABILITY_UNDECLARED"

def test_historical_execution_receipt_cannot_authorize_current_tool():
    old=proof()
    old["attestation_kind"]="EXECUTION_RECEIPT"
    r=capability.resolve(B,proof=old,trusted_verify=lambda _:True)
    assert r["status"]=="BLOCKED" and not r["available"]
