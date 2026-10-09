"""Shadow capability resolver. Configuration alone never proves tool availability."""
from __future__ import annotations
from datetime import datetime, timezone

def resolve(binding: dict, *, required=None, proof=None, trusted_verify=None,
            now: datetime | None = None) -> dict:
    declared = frozenset(binding.get("declared_capabilities") or ())
    required = frozenset(required if required is not None else declared)
    if not required or not required.issubset(declared):
        return {"status": "BLOCKED", "reason": "MODEL_CAPABILITY_UNDECLARED", "available": False}
    if proof is None or trusted_verify is None:
        return {"status": "DECLARED", "reason": "MODEL_CAPABILITY_NOT_ATTESTED", "available": False}
    # A previous execution receipt is NOT fresh tool availability proof.
    if (not isinstance(proof, dict)
        or proof.get("policy_sha256") != binding.get("policy_sha256")
        or proof.get("requested_model") != binding.get("requested_model")
        or proof.get("transport") != binding.get("transport")
        or proof.get("role") != binding.get("role")
        or not required.issubset(frozenset(proof.get("capabilities") or ()))
        or proof.get("attestation_kind") != "SESSION_TOOL_REGISTRY"):
        return {"status": "BLOCKED", "reason": "MODEL_CAPABILITY_PROOF_SCOPE_MISMATCH", "available": False}
    expiry = proof.get("expires_at")
    if not isinstance(expiry, str) or not expiry:
        return {"status": "BLOCKED", "reason": "MODEL_CAPABILITY_PROOF_EXPIRY_MISSING", "available": False}
    try:
        end = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        current = now or datetime.now(timezone.utc)
        if end.tzinfo is None or current.tzinfo is None or current >= end:
            raise ValueError("expired")
    except (ValueError, TypeError):
        return {"status": "BLOCKED", "reason": "MODEL_CAPABILITY_PROOF_EXPIRED", "available": False}
    # Verification must come from a privileged runtime verifier, not a self
    # asserted passed=true flag inside an ordinary request.
    try:
        verified = trusted_verify(proof) is True
    except Exception:
        verified = False
    if not verified:
        return {"status": "BLOCKED", "reason": "MODEL_CAPABILITY_PROOF_UNVERIFIED", "available": False}
    return {"status": "AVAILABLE", "reason": "TRUSTED_RUNTIME_PROOF", "available": True}
