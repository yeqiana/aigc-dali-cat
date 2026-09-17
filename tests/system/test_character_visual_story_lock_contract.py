from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import character_visual_contract
import machine_gate


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _episode(root: Path) -> Path:
    ep = root / "episode"
    _write(ep / "meta/episode-state.json", {
        "tool_version": "2.7.0",
        "current_state": "IDEA_LOCKED",
    })
    _write(ep / "meta/release-manifest.json", {"tool_version": "2.7.0"})
    _write(ep / "meta/story-gates.json", {
        "tool_version": "2.7.0",
        "machine_contract": {"strict": True, "version": 1},
    })
    _write(ep / "meta/character-contract.json", {
        "schema_version": 1,
        "status": "LOCKED",
        "cast": {
            "members": [
                {"id": "P01", "gender": "male", "hair": "short black hair"},
                {"id": "P02", "gender": "female", "hair": "shoulder-length black hair"},
            ]
        },
        "pov": {"character_id": "P01"},
    })
    return ep


def _lock_visual_contract(ep: Path) -> dict:
    data = character_visual_contract.prepare(ep, force=False)
    data["status"] = "LOCKED"
    for cid, row in (data.get("members") or {}).items():
        row["face_identity"]["identity_spec_locked"] = True
        if cid == "P01":
            row["hair"]["haircut_anchor"] = "natural short black crop"
            row["hair"]["hair_length_anchor"] = "above ears and collar"
        else:
            row["hair"]["haircut_anchor"] = "natural shoulder-length straight black hair"
            row["hair"]["hair_length_anchor"] = "shoulder to collarbone"
    _write(ep / character_visual_contract.REL, data)
    return data


def test_story_lock_fails_before_preimage_when_character_visual_contract_is_missing() -> None:
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tests_root) as td:
        ep = _episode(Path(td))
        failures = [x for x in machine_gate.validate(ep, "STORYBOARD_LOCKED") if x.level == "FAIL"]
        assert any(x.code == "character_visual_contract" for x in failures)
        assert any("missing" in x.message for x in failures if x.code == "character_visual_contract")


def test_character_visual_prepare_is_text_only_scaffold_and_locked_contract_passes_story_lock() -> None:
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tests_root) as td:
        ep = _episode(Path(td))
        scaffold = character_visual_contract.prepare(ep, force=False)
        assert scaffold["status"] == "DRAFT"
        assert not (ep / character_visual_contract.PIXEL_MASTER_REL).exists()
        assert character_visual_contract.validate(ep, require_locked=True)

        _lock_visual_contract(ep)
        assert character_visual_contract.validate(ep, require_locked=True) == []
        failures = [x for x in machine_gate.validate(ep, "STORYBOARD_LOCKED") if x.level == "FAIL"]
        assert not [x for x in failures if x.code == "character_visual_contract"]
        assert not (ep / character_visual_contract.PIXEL_MASTER_REL).exists()


def test_character_visual_contract_rejects_cast_drift_before_preimage() -> None:
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tests_root) as td:
        ep = _episode(Path(td))
        data = _lock_visual_contract(ep)
        del data["members"]["P02"]
        _write(ep / character_visual_contract.REL, data)
        errors = character_visual_contract.validate(ep, require_locked=True)
        assert any("missing cast ids: P02" in error for error in errors)
