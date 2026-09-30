from __future__ import annotations

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))
sys.path.insert(0, str(SYSTEM / "agents"))

import final_semantic_critic_adapter as final_critic
import model_policy
import preimage_semantic_critic_adapter as preimage_critic
import story_semantic_critic_adapter as story_critic
import storyos_config


CRITICS = [
    (story_critic, "critic.story", "gpt-6-luna", "high", story_critic.CriticDecisionError),
    (preimage_critic, "critic.preimage", "gpt-6-luna", "high", preimage_critic.PreimageCriticError),
    (final_critic, "critic.final", "gpt-6-luna", "high", final_critic.FinalSemanticCriticError),
]


def _bound_policy() -> dict:
    config = storyos_config.load_config()
    return {
        **copy.deepcopy(config["models"]),
        "policy_sha256": model_policy.policy_sha256(config),
    }


@pytest.mark.parametrize(("adapter", "role", "expected_model", "expected_effort", "_error"), CRITICS)
def test_critic_model_effort_come_from_episode_policy_not_codex_config(
    adapter, role, expected_model, expected_effort, _error, monkeypatch, tmp_path: Path
) -> None:
    episode = tmp_path / "episode"
    episode.mkdir()
    config_home = tmp_path / "codex"
    config_home.mkdir()
    config_path = config_home / "config.toml"
    config_path.write_text('model = "first-user-default"\nmodel_reasoning_effort = "low"\n', encoding="utf-8")

    monkeypatch.setattr(model_policy, "_load_bound_policy", lambda _episode: _bound_policy())
    monkeypatch.setitem(sys.modules, "codex_user_runner", SimpleNamespace(
        codex_home=lambda: (config_home, "test")
    ))
    getter = getattr(adapter, "configured_cli_model", None) or adapter._configured_cli_model

    first = getter(episode)
    config_path.write_text('model = "second-user-default"\nmodel_reasoning_effort = "high"\n', encoding="utf-8")
    second = getter(episode)

    assert first == second == (expected_model, expected_effort)
    assert model_policy.resolve(role, episode)["model"] == expected_model


@pytest.mark.parametrize(("adapter", "role", "_model", "_effort", "error_type"), CRITICS)
def test_critic_resolution_fails_closed_without_episode_binding(
    adapter, role, _model, _effort, error_type, monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(model_policy, "_load_bound_policy", lambda _episode: None)
    getter = getattr(adapter, "configured_cli_model", None) or adapter._configured_cli_model

    assert getter(tmp_path) == (None, None)
    with pytest.raises(error_type, match="Episode-bound"):
        adapter.legacy_execution_target(tmp_path)
