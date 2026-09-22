from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import character_contract as contract  # noqa: E402


def test_load_delegates_to_episode_contract_owner(monkeypatch, tmp_path):
    payload = {"schema_version": 1, "status": "LOCKED", "cast": {"members": []}}
    monkeypatch.setattr(
        contract.episode_contract_persistence,
        "load_latest",
        lambda _ep, _type, legacy_path=None: payload,
    )
    assert contract.load(tmp_path) == payload
    assert contract.authority_sha256(tmp_path)


def test_save_delegates_to_episode_contract_owner(monkeypatch, tmp_path):
    payload = {"schema_version": 1, "status": "LOCKED"}
    captured = []
    monkeypatch.setattr(
        contract.episode_contract_persistence,
        "save",
        lambda *args, **kwargs: captured.append((args, kwargs)) or {},
    )
    assert contract.save(tmp_path, payload) == payload
    assert captured[0][0][1] == contract.CONTRACT_TYPE
    assert captured[0][0][2] == contract.REL


def test_prompt_block_uses_authority_without_compatibility_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        contract,
        "load",
        lambda _ep: {"schema_version": 1, "status": "LOCKED"},
    )
    assert '"status": "LOCKED"' in contract.prompt_block(tmp_path)
