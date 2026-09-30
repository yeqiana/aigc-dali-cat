"""Lean resolver for the single configured StoryOS business model policy."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import storyos_config

_FALLBACK_FAILURES = {"PROVIDER_CAPACITY", "MODEL_UNAVAILABLE"}


def _policy(config: dict | None = None) -> dict:
    cfg = config if config is not None else storyos_config.load_config()
    errors = storyos_config._validate_model_policy(cfg)
    if errors:
        raise ValueError("MODEL_POLICY_INVALID: " + "; ".join(errors))
    return cfg["models"]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def policy_sha256(config: dict | None = None) -> str:
    """Return a deterministic digest of version, profiles, and role aliases."""
    policy = _policy(config)
    payload = {key: policy[key] for key in ("policy_version", "profiles", "role_aliases")}
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _resolved(profile_name: str, config: dict | None = None) -> dict:
    policy = _policy(config)
    profile = policy["profiles"].get(profile_name)
    if profile is None:
        raise ValueError(f"MODEL_PROFILE_UNKNOWN: {profile_name}")
    result = copy.deepcopy(profile)
    result.update({
        "profile": profile_name,
        "policy_version": policy["policy_version"],
        "model_policy_sha256": policy_sha256(config),
    })
    return result


def resolve_profile(profile_name: str, episode: str | Path | None = None) -> dict:
    """Resolve a named profile; episode binding is enforced by persistence integration."""
    return _resolve_bound_profile(profile_name, episode)


def resolve(role: str, episode: str | Path | None = None) -> dict:
    if episode is not None:
        bound = _load_bound_policy(episode)
        if not isinstance(bound, dict):
            raise ValueError("MODEL_POLICY_NOT_BOUND: freeze_for_episode must run before model execution")
        profile = (bound.get("role_aliases") or {}).get(role)
        if profile is None:
            raise ValueError(f"MODEL_ROLE_UNKNOWN_IN_BOUND_POLICY: {role}")
        result = _resolve_bound_profile(profile, episode)
        result["role"] = role
        return result
    policy = _policy()
    profile = policy["role_aliases"].get(role)
    if profile is None:
        raise ValueError(f"MODEL_ROLE_UNKNOWN: {role}")
    result = _resolve_bound_profile(profile, episode)
    result["role"] = role
    return result


def resolve_candidate(role: str, candidate_index: int, episode: str | Path | None = None) -> dict:
    """Resolve candidate 0 as primary and 1..N as ordered fallbacks."""
    selected = resolve(role, episode)
    if type(candidate_index) is not int or candidate_index < 0:
        raise ValueError("MODEL_CANDIDATE_INDEX_INVALID: expected a non-negative integer")
    candidates = [selected["model"], *selected.get("fallback_models", [])]
    if candidate_index >= len(candidates):
        raise IndexError(f"MODEL_CANDIDATE_OUT_OF_RANGE: role={role} index={candidate_index}")
    selected["model"] = candidates[candidate_index]
    selected["candidate_index"] = candidate_index
    return selected


def next_fallback(role: str, failure_class: str, episode: str | Path | None = None) -> dict | None:
    """Return the first policy-owned fallback only for recognized availability failures."""
    if str(failure_class or "").strip().upper() not in _FALLBACK_FAILURES:
        return None
    resolved = resolve_candidate(role, 1, episode)
    return resolved


def _resolve_bound_profile(profile_name: str, episode: str | Path | None) -> dict:
    if episode is None:
        return _resolved(profile_name)
    bound = _load_bound_policy(episode)
    if bound is None:
        raise ValueError("MODEL_POLICY_NOT_BOUND: freeze_for_episode must run before model execution")
    bound = bound.get("policy") if isinstance(bound.get("policy"), dict) else bound
    profiles = bound.get("profiles") or {}
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"MODEL_PROFILE_UNKNOWN_IN_BOUND_POLICY: {profile_name}")
    return _resolved_from_bound(profile_name, profile, bound)


def _resolved_from_bound(profile_name: str, profile: dict, bound: dict) -> dict:
    result = copy.deepcopy(profile)
    result.update({
        "profile": profile_name,
        "policy_version": bound.get("policy_version"),
        "model_policy_sha256": bound.get("policy_sha256"),
    })
    return result


def _load_bound_policy(episode: str | Path) -> dict | None:
    """Read the authoritative episode_meta_store record through its persistence adapter."""
    try:
        import model_policy_persistence
    except ImportError as exc:
        raise RuntimeError("MODEL_POLICY_PERSISTENCE_UNAVAILABLE") from exc
    return model_policy_persistence.load(Path(episode))


def freeze_for_episode(episode: str | Path | None = None) -> dict:
    """Build the immutable payload, and bind it when an Episode is supplied."""
    policy = _policy()
    payload = {
        "schema_version": 1,
        "policy_version": policy["policy_version"],
        "policy_sha256": policy_sha256(),
        "bound_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profiles": copy.deepcopy(policy["profiles"]),
        "role_aliases": copy.deepcopy(policy["role_aliases"]),
        "fallback_candidates": {
            name: list(profile.get("fallback_models") or [])
            for name, profile in policy["profiles"].items()
        },
    }
    if episode is None:
        return payload
    try:
        import model_policy_persistence
    except ImportError as exc:
        raise RuntimeError("MODEL_POLICY_PERSISTENCE_UNAVAILABLE") from exc
    return model_policy_persistence.freeze(Path(episode), payload)


def validate_bound_policy(episode: str | Path | None = None) -> list[str]:
    """Validate configured profiles, or verify an existing persisted Episode binding."""
    errors = _policy_errors()
    if episode is None:
        return errors
    try:
        import model_policy_persistence
        return errors + model_policy_persistence.validate_bound_policy(Path(episode))
    except Exception as exc:
        return errors + [str(exc)]


def validate_capability_profiles() -> list[str]:
    """Validate the minimum profile separation required by the registered tool capabilities."""
    errors = _policy_errors()
    if errors:
        return errors
    policy = _policy()
    if policy["profiles"]["image_controller"]["model"] == policy["profiles"]["image_payload"]["model"]:
        errors.append("MODEL_CAPABILITY_PROFILE_COLLISION: controller and payload must remain separate")
    return errors


def _policy_errors() -> list[str]:
    try:
        cfg = storyos_config.load_config()
        return storyos_config._validate_model_policy(cfg)
    except Exception as exc:
        return [str(exc)]
