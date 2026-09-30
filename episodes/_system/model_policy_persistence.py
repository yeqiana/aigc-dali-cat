from __future__ import annotations

"""Episode-bound, immutable Model Policy payload persistence.

The canonical record is an Episode Contract in ``episode_meta_store``. The
Episode JSON file is a compatibility projection only and is never read as the
authority while ``episode_meta_store=mysql``.
"""
import hashlib
import json
from pathlib import Path

import episode_contract_persistence
import runtime_workspace
import story_json


CONTRACT_TYPE = "MODEL_POLICY"
REL = Path("meta/runtime/model-policy-snapshot.json")


def _policy_sha256(payload: dict) -> str:
    # Match model_policy.policy_sha256(): binding metadata such as bound_at and
    # fallback serialization must not change the identity of the selected policy.
    core = {key: payload[key] for key in ("policy_version", "profiles", "role_aliases")}
    raw = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load(ep: Path) -> dict | None:
    """Load the authoritative frozen policy, if one is bound to this Episode."""
    ep = Path(ep).resolve()
    policy = episode_contract_persistence.load_latest(
        ep, CONTRACT_TYPE, legacy_path=ep / REL
    )
    if not isinstance(policy, dict):
        return None
    expected = str(policy.get("policy_sha256") or "").lower()
    if not expected or expected != _policy_sha256(policy):
        raise ValueError("episode model policy payload SHA mismatch")
    return policy


def freeze(ep: Path, policy_payload: dict) -> dict:
    """Bind the first policy payload to the Episode; reject any later drift."""
    ep = Path(ep).resolve()
    if not isinstance(policy_payload, dict):
        raise ValueError("model policy payload must be an object")
    payload = dict(policy_payload)
    expected_sha = str(payload.get("policy_sha256") or "").lower()
    required = ("schema_version", "policy_version", "bound_at", "profiles", "role_aliases", "fallback_candidates")
    missing = [key for key in required if payload.get(key) in (None, "")]
    if missing:
        raise ValueError("model policy payload missing: " + ", ".join(missing))
    if not isinstance(payload.get("profiles"), dict) or not isinstance(payload.get("role_aliases"), dict):
        raise ValueError("model policy profiles and role_aliases must be objects")
    actual_sha = _policy_sha256(payload)
    if not expected_sha or expected_sha != actual_sha:
        raise ValueError("model policy payload policy_sha256 does not match policy content")
    payload["policy_sha256"] = actual_sha

    current = load(ep)
    if current is not None:
        if str(current.get("policy_sha256")) != payload["policy_sha256"]:
            raise ValueError("episode model policy is already frozen with a different SHA")
        return {"policy": current, "policy_sha256": payload["policy_sha256"], "created": False}

    episode_contract_persistence.save(
        ep,
        CONTRACT_TYPE,
        REL,
        payload,
        status="FROZEN",
        source_sha256=payload["policy_sha256"],
    )
    return {"policy": payload, "policy_sha256": payload["policy_sha256"], "created": True}


def validate_bound_policy(ep: Path, expected_sha256: str | None = None) -> list[str]:
    try:
        payload = load(Path(ep).resolve())
    except Exception as exc:
        return [f"episode model policy unreadable: {exc}"]
    if payload is None:
        return ["episode model policy is not frozen"]
    if expected_sha256 and str(payload.get("policy_sha256") or "").lower() != str(expected_sha256).lower():
        return ["episode model policy SHA differs from expected policy"]
    return []


def projection(ep: Path) -> dict | None:
    """Read the local diagnostics projection without treating it as authority."""
    value = story_json.read_json(runtime_workspace.workspace_path(Path(ep).resolve(), REL), default=None)
    return value if isinstance(value, dict) else None
