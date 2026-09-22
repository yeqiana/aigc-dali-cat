from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import world_identity_contract as world  # noqa: E402


def _override():
    return {
        "schema_version": 1,
        "inherit_default": False,
        "profile_id": "EPISODE_WORLD_IDENTITY_OVERRIDE",
        "world": {
            "country": "Testland",
            "region": "Test Region",
            "culture_context": "test culture",
            "language_context": "test language",
            "architecture_context": "test architecture",
        },
        "population": {
            "nationality_context": "test",
            "resident_context": "test residents",
            "default_protagonist_age_range": [19, 30],
            "default_protagonist_identity": "ordinary resident",
        },
        "visual_rules": {},
    }


def test_effective_reads_override_from_contract_owner_without_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    payload = _override()
    monkeypatch.setattr(
        world.episode_contract_persistence,
        "load_latest",
        lambda _ep, _type, legacy_path=None: payload,
    )

    data = world.effective(ep)

    assert data["source"] == "EPISODE_OVERRIDE"
    assert data["world"]["country"] == "Testland"
    assert data["override_sha256"] == world.sha256_json(payload)
    assert not (ep / world.OVERRIDE_REL).exists()


def test_save_override_delegates_to_contract_owner(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    captured = []
    payload = _override()
    monkeypatch.setattr(
        world.episode_contract_persistence,
        "save",
        lambda *args, **kwargs: captured.append((args, kwargs)) or {},
    )

    result = world.save_override(ep, payload)

    assert result == payload
    assert captured[0][0][1] == world.CONTRACT_TYPE
    assert captured[0][0][2] == world.OVERRIDE_REL


def test_episode_version_reads_episode_state_authority(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        world.episode_state_persistence,
        "load",
        lambda _ep: {"tool_version": "2.6.1"},
    )

    assert world.episode_version(ep) == "2.6.1"
    assert world.required(ep) is True
