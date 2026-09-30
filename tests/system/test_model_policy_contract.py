from __future__ import annotations

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import model_policy
import image_model_policy
import storyos_config


EXPECTED_PROFILES = {
    "orchestration", "authoring", "structured_text", "semantic_critic",
    "final_semantic", "vision_fast", "vision_final", "image_controller",
    "image_payload",
}
EXPECTED_ALIASES = {
    "orchestration": "orchestration",
    "story.authoring": "authoring",
    "preimage.character_finalize": "structured_text",
    "preimage.world_prepare": "structured_text",
    "preimage.frame_contract": "structured_text",
    "preimage.visual_narrative": "authoring",
    "prompt.production": "structured_text",
    "prompt.repair": "structured_text",
    "release": "structured_text",
    "critic.story": "semantic_critic",
    "critic.preimage": "semantic_critic",
    "critic.final": "final_semantic",
    "vision.fast": "vision_fast",
    "guardian": "vision_fast",
    "vision.visual_lock": "vision_final",
    "vision.final": "vision_final",
    "image.controller": "image_controller",
    "image.payload": "image_payload",
}


def test_nine_profiles_and_required_role_aliases_are_configured() -> None:
    policy = storyos_config.load_config()["models"]
    assert set(policy["profiles"]) == EXPECTED_PROFILES
    assert {key: policy["role_aliases"][key] for key in EXPECTED_ALIASES} == EXPECTED_ALIASES


@pytest.mark.parametrize(
    ("role", "profile", "model", "effort"),
    [
        ("story.authoring", "authoring", "gpt-6-luna", "high"),
        ("prompt.production", "structured_text", "gpt-6-luna", "high"),
        ("critic.story", "semantic_critic", "gpt-6-luna", "high"),
        ("critic.final", "final_semantic", "gpt-6-luna", "high"),
        ("vision.fast", "vision_fast", "gpt-6-luna", "low"),
        ("vision.visual_lock", "vision_final", "gpt-6-luna", "high"),
        ("image.controller", "image_controller", "gpt-6-luna", "high"),
    ],
)
def test_role_resolution_returns_profile_model_and_effort(role, profile, model, effort) -> None:
    resolved = model_policy.resolve(role)
    assert (resolved["profile"], resolved["model"], resolved["reasoning_effort"]) == (profile, model, effort)
    assert resolved["role"] == role
    assert len(resolved["model_policy_sha256"]) == 64


def test_image_fallback_candidates_keep_policy_order() -> None:
    assert model_policy.resolve_candidate("image.payload", 0)["model"] == "gpt-image-2.5-flare"
    assert model_policy.resolve_candidate("image.payload", 1)["model"] == "gpt-image-2.5-sunburst"
    assert model_policy.resolve_candidate("image.payload", 2)["model"] == "gpt-image-2"
    assert model_policy.next_fallback("image.payload", "MODEL_UNAVAILABLE")["model"] == "gpt-image-2.5-sunburst"
    assert model_policy.next_fallback("image.payload", "PROVIDER_CAPACITY")["model"] == "gpt-image-2.5-sunburst"


def test_image_fallback_uses_episode_bound_profile(monkeypatch, tmp_path: Path) -> None:
    bound = {
        "policy_version": "frozen-test",
        "policy_sha256": "a" * 64,
        "profiles": {
            "image_payload": {
                "model": "bound-primary",
                "quality": "high",
                "fallback_models": ["bound-fallback-1", "bound-fallback-2"],
            },
        },
        "role_aliases": {"image.payload": "image_payload"},
    }
    monkeypatch.setitem(sys.modules, "model_policy_persistence", SimpleNamespace(
        load=lambda episode: copy.deepcopy(bound),
    ))
    changed_global = copy.deepcopy(storyos_config.load_config())
    changed_global["models"]["profiles"]["image_payload"].update({
        "model": "new-global-primary",
        "fallback_models": ["new-global-fallback"],
    })
    monkeypatch.setattr(storyos_config, "load_config", lambda: changed_global)

    assert image_model_policy.next_fallback_model("bound-primary", episode=tmp_path) == "bound-fallback-1"
    assert image_model_policy.next_fallback_model("bound-fallback-1", episode=tmp_path) == "bound-fallback-2"
    assert image_model_policy.next_fallback_model("bound-fallback-2", episode=tmp_path) is None
    assert image_model_policy.next_fallback_model("new-global-primary", episode=tmp_path) is None
    assert image_model_policy.next_fallback_model(
        "bound-primary", strict_model=True, episode=tmp_path) is None


@pytest.mark.parametrize("failure_class", ["CONTENT_REJECTED", "AUTH_401", "RATE_LIMIT_429", "NETWORK_ERROR", ""])
def test_non_availability_failures_do_not_advance_model(failure_class: str) -> None:
    assert model_policy.next_fallback("image.payload", failure_class) is None


def test_controller_and_payload_are_separate_capability_profiles() -> None:
    controller = model_policy.resolve("image.controller")
    payload = model_policy.resolve("image.payload")
    assert controller["profile"] != payload["profile"]
    assert controller["model"] != payload["model"]
    assert "reasoning_effort" in controller
    assert "quality" in payload and payload["quality"] == "high"
    assert model_policy.validate_capability_profiles() == []


def test_schema_validator_fails_closed_on_missing_profile_or_bad_alias() -> None:
    config = copy.deepcopy(storyos_config.load_config())
    del config["models"]["profiles"]["structured_text"]
    config["models"]["role_aliases"]["prompt.production"] = "missing_profile"
    errors = storyos_config.validate(config)
    assert any("models.profiles missing required profiles" in error for error in errors)
    assert any("models.role_aliases.prompt.production" in error for error in errors)


def test_freeze_and_episode_resolution_use_immutable_persisted_policy(monkeypatch, tmp_path: Path) -> None:
    bound_payload: dict = {}
    calls: list[tuple[str, object]] = []

    def freeze(ep: Path, payload: dict) -> dict:
        bound_payload.update(copy.deepcopy(payload))
        calls.append(("freeze", ep))
        return {"policy": copy.deepcopy(payload), "policy_sha256": payload["policy_sha256"], "created": True}

    def load(ep: Path) -> dict:
        calls.append(("load", ep))
        return copy.deepcopy(bound_payload) or None

    def validate_bound_policy(ep: Path, expected_sha256: str | None = None) -> list[str]:
        calls.append(("validate", expected_sha256))
        return [] if bound_payload else ["episode model policy is not frozen"]

    monkeypatch.setitem(sys.modules, "model_policy_persistence", SimpleNamespace(
        freeze=freeze, load=load, validate_bound_policy=validate_bound_policy,
    ))

    ep = tmp_path / "episode"
    with pytest.raises(ValueError, match="MODEL_POLICY_NOT_BOUND"):
        model_policy.resolve("story.authoring", ep)
    frozen = model_policy.freeze_for_episode(ep)
    assert frozen["created"] is True
    payload = frozen["policy"]
    assert payload["bound_at"]
    assert payload["policy_sha256"] == model_policy.policy_sha256()
    assert payload["fallback_candidates"]["image_payload"] == [
        "gpt-image-2.5-sunburst", "gpt-image-2",
    ]

    # Episode resolution uses bound aliases and profile data even if current
    # config changes after the freeze.
    changed_config = copy.deepcopy(storyos_config.load_config())
    changed_config["models"]["profiles"]["authoring"]["model"] = "changed-current-config-model"
    monkeypatch.setattr(storyos_config, "load_config", lambda: changed_config)
    resolved = model_policy.resolve("story.authoring", ep)
    assert resolved["model"] == "gpt-6-luna"
    assert resolved["reasoning_effort"] == "high"
    assert resolved["profile"] == "authoring"
    assert resolved["model_policy_sha256"] == payload["policy_sha256"]
    assert model_policy.validate_bound_policy(ep) == []
    assert any(name == "freeze" for name, _ in calls)
    assert any(name == "load" for name, _ in calls)
    assert any(name == "validate" for name, _ in calls)
