from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import capture_event_contract as capture  # noqa: E402
import voice_contract as voice  # noqa: E402
import wardrobe_contract as wardrobe  # noqa: E402


def _exercise_owner(monkeypatch, tmp_path, module, payload):
    calls = []
    monkeypatch.setattr(
        module.episode_contract_persistence,
        "load_latest",
        lambda _ep, _type, legacy_path=None: payload,
    )
    monkeypatch.setattr(
        module.episode_contract_persistence,
        "save",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {},
    )
    assert module.load(tmp_path) == payload
    assert module.exists(tmp_path) is True
    assert module.authority_sha256(tmp_path)
    assert module.save(tmp_path, payload) == payload
    assert calls[0][0][1] == module.CONTRACT_TYPE
    assert calls[0][0][2] == module.REL


def test_capture_event_owner(monkeypatch, tmp_path):
    _exercise_owner(
        monkeypatch,
        tmp_path,
        capture,
        {"schema_version": 1, "status": "LOCKED", "frames": {}},
    )


def test_voice_owner(monkeypatch, tmp_path):
    _exercise_owner(
        monkeypatch,
        tmp_path,
        voice,
        {"schema_version": 1, "status": "LOCKED", "voice_card": {}},
    )


def test_wardrobe_owner(monkeypatch, tmp_path):
    _exercise_owner(
        monkeypatch,
        tmp_path,
        wardrobe,
        {"schema_version": 1, "status": "LOCKED", "frames": {}},
    )
