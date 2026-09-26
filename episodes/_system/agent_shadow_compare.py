"""Deterministic-first comparison for legacy vs Agent shadow candidates."""
from __future__ import annotations

import hashlib
import json

import preimage_task_contract


def _sha(value) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _character_semantic_obligations(task: dict) -> dict:
    contract = (((task.get("input_contract") or {}).get("authority_inputs") or {}).get("meta/character-contract.json") or {})
    visual = (((task.get("input_contract") or {}).get("authority_inputs") or {}).get("meta/character-visual-contract.json") or {})
    members = ((contract.get("cast") or {}).get("members") or [])
    ids = [str(row.get("id") or "") for row in members if str(row.get("id") or "")]
    names = {str(row.get("id")): str(row.get("name") or "") for row in members if str(row.get("id") or "")}
    visual_members = visual.get("members") or {}
    anchors = {
        cid: str((visual_members.get(cid) or {}).get("story_identity_anchor") or "")
        for cid in ids
    }
    pov = contract.get("pov") or {}
    return {
        "cast_ids": ids,
        "names": names,
        "appearance_anchors": anchors,
        "pov_character_id": str(pov.get("character_id") or ""),
        "pov_person": "first_person" if pov.get("first_person") is True else None,
    }


def character_semantic_obligations(task: dict) -> dict:
    """Public frozen obligations contract used by Character Agent producers/tests."""
    return _character_semantic_obligations(task)


def compare_character_finalize_semantics(task: dict, candidate: dict) -> dict:
    """Strict deterministic Character Finalize semantic-obligation check.

    It proves preservation of frozen cast, POV and locked visual identity anchors.
    It deliberately does not infer free-form textual equivalence.
    """
    obligations = _character_semantic_obligations(task)
    payload = ((candidate.get("payload") or {}).get("character.finalize") or {}) if isinstance(candidate, dict) else {}
    character_raw = payload.get("character")
    identity_raw = payload.get("identity")
    appearance_raw = payload.get("appearance")
    pov_raw = payload.get("pov")
    character = character_raw if isinstance(character_raw, dict) else {}
    identity = identity_raw if isinstance(identity_raw, dict) else {}
    appearance = appearance_raw if isinstance(appearance_raw, dict) else {}
    pov = pov_raw if isinstance(pov_raw, dict) else {}
    errors = []
    expected_ids = set(obligations["cast_ids"])
    if not expected_ids:
        errors.append("frozen Character Contract cast obligations missing")
    if not isinstance(character_raw, dict):
        errors.append("character semantic object missing")
    if not isinstance(identity_raw, dict):
        errors.append("identity semantic object missing")
    if not isinstance(appearance_raw, dict):
        errors.append("appearance semantic object missing")
    if not isinstance(pov_raw, dict):
        errors.append("POV semantic object missing")
    visible = character.get("visible_cast") or []
    visible_ids = set()
    for raw in visible:
        text = str(raw)
        for cid in expected_ids:
            if cid in text:
                visible_ids.add(cid)
    if visible_ids != expected_ids:
        errors.append("visible cast does not cover frozen cast ids")
    if set(identity) != expected_ids:
        errors.append("identity keys do not exactly match frozen cast ids")
    if set(appearance) != expected_ids:
        errors.append("appearance keys do not exactly match frozen cast ids")
    for cid in sorted(expected_ids):
        name = obligations["names"].get(cid) or ""
        if name and name not in str(identity.get(cid) or ""):
            errors.append(f"identity missing frozen character name: {cid}")
        anchor = obligations["appearance_anchors"].get(cid) or ""
        if anchor and anchor not in str(appearance.get(cid) or ""):
            errors.append(f"appearance missing locked story identity anchor: {cid}")
    expected_pov = obligations.get("pov_character_id")
    if expected_pov and str(pov.get("character_id") or "") != expected_pov:
        errors.append("POV character differs from frozen Character Contract")
    expected_person = obligations.get("pov_person")
    if expected_person and str(pov.get("person") or "") != expected_person:
        errors.append("POV person differs from frozen Character Contract")
    if not str(character.get("relationship") or "").strip():
        errors.append("character relationship missing")
    if not str(character.get("continuity_rule") or "").strip():
        errors.append("character continuity rule missing")
    if not str(pov.get("capture_rule") or "").strip():
        errors.append("POV capture rule missing")
    return {
        "pass": not errors,
        "errors": errors,
        "obligations": obligations,
        "mode": "deterministic_frozen_character_obligations",
    }


def character_semantic_equivalence(task: dict, legacy: dict, shadow: dict) -> dict:
    legacy_result = compare_character_finalize_semantics(task, legacy)
    shadow_result = compare_character_finalize_semantics(task, shadow)
    return {
        "semantic_equivalent": bool(legacy_result["pass"] and shadow_result["pass"]),
        "legacy": legacy_result,
        "shadow": shadow_result,
        "mode": "both_candidates_satisfy_same_frozen_character_obligations",
    }


WORLD_SCOPES = (
    "visual.world_identity",
    "visual.world_state",
    "visual.temporal_continuity",
    "visual.wardrobe",
)


def _world_semantic_obligations(task: dict) -> dict:
    contract = task.get("input_contract") or {}
    capsule = contract.get("world_prepare_capsule") or {}
    obligations = capsule.get("obligations") or {}
    return {
        "snapshot_id": task.get("snapshot_id"),
        "capsule_sha256": capsule.get("capsule_sha256"),
        "required_scope": list(task.get("authority_scope") or ()),
        "scopes": obligations.get("scopes") or {},
        "story_lock_sha256": obligations.get("story_lock_sha256"),
        "source_sha256": capsule.get("source_sha256") or {},
    }


def world_semantic_obligations(task: dict) -> dict:
    """Return the machine-readable World contract frozen by the Host capsule."""
    return _world_semantic_obligations(task)


def _preserves_frozen(expected, actual, path: str) -> list[str]:
    """Require every frozen leaf at its original structural path; permit additions."""
    errors: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path} must remain an object"]
        for key, value in expected.items():
            if key not in actual:
                errors.append(f"{path}.{key} missing from candidate")
            else:
                errors.extend(_preserves_frozen(value, actual[key], f"{path}.{key}"))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list) or actual != expected:
            return [f"{path} differs from frozen ordered values"]
        return []
    if actual != expected:
        return [f"{path} differs from frozen value"]
    return []


def compare_world_prepare_semantics(task: dict, candidate: dict) -> dict:
    """Deterministic World obligations check; does not call an LLM critic."""
    obligations = _world_semantic_obligations(task)
    errors: list[str] = []
    required = list(task.get("authority_scope") or ())
    if required != list(WORLD_SCOPES):
        errors.append("WORLD_PREPARE authority scope differs from the canonical task contract")
    if set(obligations["scopes"]) != set(required):
        errors.append("frozen World obligations do not cover every required scope")
    payload = candidate.get("payload") if isinstance(candidate, dict) else None
    payload = payload if isinstance(payload, dict) else {}
    for scope in required:
        expected = obligations["scopes"].get(scope)
        actual = payload.get(scope)
        if not isinstance(expected, dict):
            errors.append(f"frozen obligation must be an object: {scope}")
            continue
        if not isinstance(actual, dict) or not actual or actual.get("applicable") is False:
            errors.append(f"candidate scope missing applicable content: {scope}")
            continue
        if expected:
            errors.extend(_preserves_frozen(expected, actual, scope))
    return {
        "pass": not errors,
        "errors": errors,
        "obligations": obligations,
        "mode": "deterministic_frozen_world_obligations",
    }


def world_semantic_equivalence(task: dict, legacy: dict, shadow: dict) -> dict:
    legacy_result = compare_world_prepare_semantics(task, legacy)
    shadow_result = compare_world_prepare_semantics(task, shadow)
    return {
        "semantic_equivalent": bool(legacy_result["pass"] and shadow_result["pass"]),
        "legacy": legacy_result,
        "shadow": shadow_result,
        "mode": "both_candidates_satisfy_same_frozen_world_obligations",
    }


def compare_preimage_candidates(task: dict, legacy: dict, shadow: dict) -> dict:
    legacy_errors = preimage_task_contract.verify_candidate(legacy or {}, task)
    shadow_errors = preimage_task_contract.verify_candidate(shadow or {}, task)
    legacy_payload = (legacy or {}).get("payload") if isinstance(legacy, dict) else None
    shadow_payload = (shadow or {}).get("payload") if isinstance(shadow, dict) else None
    legacy_scopes = set(legacy_payload or {}) if isinstance(legacy_payload, dict) else set()
    shadow_scopes = set(shadow_payload or {}) if isinstance(shadow_payload, dict) else set()
    required = set(task.get("authority_scope") or [])
    structural_equal = (
        not legacy_errors
        and not shadow_errors
        and _sha(legacy_payload) == _sha(shadow_payload)
    )
    semantic = None
    if task.get("task_type") == "CHARACTER_FINALIZE" and not legacy_errors and not shadow_errors:
        semantic = character_semantic_equivalence(task, legacy, shadow)
    elif task.get("task_type") == "WORLD_PREPARE" and not legacy_errors and not shadow_errors:
        semantic = world_semantic_equivalence(task, legacy, shadow)
    return {
        "schema_version": 1,
        "task_id": task.get("task_id"),
        "snapshot_id": task.get("snapshot_id"),
        "comparison_mode": "deterministic_first",
        "legacy_valid": not legacy_errors,
        "shadow_valid": not shadow_errors,
        "legacy_errors": legacy_errors,
        "shadow_errors": shadow_errors,
        "required_scope_coverage": {
            "legacy": sorted(required.intersection(legacy_scopes)),
            "shadow": sorted(required.intersection(shadow_scopes)),
            "required": sorted(required),
        },
        "payload_sha256": {
            "legacy": _sha(legacy_payload),
            "shadow": _sha(shadow_payload),
        },
        "structural_equal": structural_equal,
        "domain_semantic": semantic,
        "needs_semantic_review": bool(
            not legacy_errors and not shadow_errors and not structural_equal
            and not (semantic or {}).get("semantic_equivalent")
        ),
        "canonical_side_effect": False,
    }
