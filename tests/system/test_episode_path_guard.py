from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import effective_config
import next_action
import runtime_evidence_contract
import runtime_portability


def test_repository_local_episode_must_live_under_episodes():
    assert runtime_portability.validate_episode_directory(ROOT / "episodes" / "_tests" / "ok") == []
    assert runtime_portability.validate_episode_directory(ROOT / "episodes" / "series" / "episode") == []
    errors = runtime_portability.validate_episode_directory(ROOT / "ep")
    assert errors and "under episodes/" in errors[0]
    with pytest.raises(ValueError, match="under episodes/"):
        runtime_portability.assert_episode_directory(ROOT / "ep")


def test_external_fixture_remains_allowed_for_unit_tests(tmp_path):
    fixture = tmp_path / "ep"
    assert runtime_portability.validate_episode_directory(fixture) == []
    label = runtime_portability.episode_label(fixture)
    assert label == "external-fixture/ep"
    assert str(tmp_path) not in label


def test_repository_root_pseudo_episode_is_rejected_by_runtime_writers(monkeypatch):
    pseudo = ROOT / "ep"
    with pytest.raises(ValueError, match="under episodes/"):
        effective_config.write(pseudo)
    with pytest.raises(ValueError, match="under episodes/"):
        runtime_evidence_contract.arm(pseudo)
    with pytest.raises(ValueError, match="under episodes/"):
        next_action.write(pseudo)
