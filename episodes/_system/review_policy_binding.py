"""Attach only the authoritative, Episode-frozen Model Policy identity to review evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import model_policy_persistence


def attach_bound_policy_sha(ep: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Return a receipt payload carrying the frozen policy SHA, if one exists.

    This deliberately does not resolve the current global config. A review made
    before an Episode policy was frozen remains unbound and cannot be reused as
    current-policy evidence. Caller-supplied SHA values are never trusted.
    """
    result = dict(payload)
    provenance = result.get("critic_provenance")
    provenance = dict(provenance) if isinstance(provenance, dict) else {}
    frozen = model_policy_persistence.load(Path(ep).resolve())
    frozen_sha = str((frozen or {}).get("policy_sha256") or "").strip().lower()

    # Never preserve a caller supplied identity when no authoritative binding
    # exists; doing so would turn an unbound review into false reuse evidence.
    result.pop("model_policy_sha256", None)
    provenance.pop("model_policy_sha256", None)
    if frozen_sha:
        for existing in (
            payload.get("model_policy_sha256"),
            (payload.get("critic_provenance") or {}).get("model_policy_sha256")
            if isinstance(payload.get("critic_provenance"), dict) else None,
        ):
            if existing and str(existing).strip().lower() != frozen_sha:
                raise ValueError("MODEL_POLICY_SHA_MISMATCH: review evidence differs from Episode-frozen policy")
        result["model_policy_sha256"] = frozen_sha
        provenance["model_policy_sha256"] = frozen_sha
    if provenance or "critic_provenance" in result:
        result["critic_provenance"] = provenance
    return result
