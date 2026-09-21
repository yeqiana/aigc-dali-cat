from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import character_visual_contract as visual  # noqa: E402


def _spec():
    return {
        "schema_version": 2,
        "status": "LOCKED",
        "primary_cast_ids": ["P01"],
        "members": {"P01": {}},
    }


def test_owner_load_save_and_authority_sha(monkeypatch, tmp_path):
    payload = _spec()
    calls = []
    monkeypatch.setattr(
        visual.episode_contract_persistence,
        "load_latest",
        lambda _ep, _type, legacy_path=None: payload,
    )
    monkeypatch.setattr(
        visual.episode_contract_persistence,
        "save",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {},
    )

    assert visual.load(tmp_path) == payload
    assert visual.exists(tmp_path) is True
    assert visual.authority_sha256(tmp_path)
    assert visual.save(tmp_path, payload) == payload
    assert calls[0][0][1] == visual.CONTRACT_TYPE
    assert calls[0][0][2] == visual.REL


def test_materialize_export_does_not_restore_legacy_authority(monkeypatch, tmp_path):
    payload = _spec()
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(visual, "load", lambda _ep: payload)
    monkeypatch.setattr(visual.runtime_workspace, "runtime_root", lambda: runtime)

    exported = visual.materialize_export(tmp_path)

    assert exported is not None and exported.is_file()
    assert exported.name == "character-visual-contract.json"
    assert not (tmp_path / visual.REL).exists()


def test_pixel_master_binds_authority_sha_not_legacy_file(monkeypatch, tmp_path):
    payload = _spec()
    asset = tmp_path / "master.png"
    asset.write_bytes(b"pixels")
    monkeypatch.setattr(visual, "load", lambda _ep: payload)
    monkeypatch.setattr(visual, "validate", lambda _ep, _locked=True: [])
    monkeypatch.setattr(visual, "_repo_asset", lambda _raw: asset)
    monkeypatch.setattr(visual, "repo_rel", lambda _path: "tests/runtime/master.png")

    row = visual._pixel_master_data(
        tmp_path,
        frame=1,
        asset_path="ignored.png",
        asset_sha256=visual.sha_file(asset),
        frame_contract_sha256="f" * 64,
        status="PROVISIONAL",
    )

    assert row["character_visual_contract_sha256"] == visual.authority_sha256(tmp_path)
    assert not (tmp_path / visual.REL).exists()


def test_pixel_master_accepts_legacy_byte_sha_when_mysql_authority_is_semantically_equal(
    monkeypatch, tmp_path
):
    payload = _spec()
    legacy = tmp_path / visual.REL
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    asset = tmp_path / "master.png"
    asset.write_bytes(b"pixels")
    pixel_master = tmp_path / visual.PIXEL_MASTER_REL
    pixel_master.parent.mkdir(parents=True, exist_ok=True)
    pixel_master.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "status": "LOCKED",
                "source_role": "ordinary_baseline",
                "frame": "01",
                "asset_path": "master.png",
                "sha256": visual.sha_file(asset),
                "frame_contract_sha256": "f" * 64,
                "character_visual_contract_sha256": visual.sha_file(legacy),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(visual, "load", lambda _ep: payload)
    monkeypatch.setattr(visual, "_repo_asset", lambda _raw: asset)

    assert visual.validate_pixel_master(tmp_path) == []


def test_pixel_master_rejects_legacy_sha_when_mysql_authority_semantically_drifted(
    monkeypatch, tmp_path
):
    historical = _spec()
    current = _spec()
    current["primary_cast_ids"] = ["P01", "P02"]
    legacy = tmp_path / visual.REL
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(
        json.dumps(historical, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    asset = tmp_path / "master.png"
    asset.write_bytes(b"pixels")
    pixel_master = tmp_path / visual.PIXEL_MASTER_REL
    pixel_master.parent.mkdir(parents=True, exist_ok=True)
    pixel_master.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "status": "LOCKED",
                "source_role": "ordinary_baseline",
                "frame": "01",
                "asset_path": "master.png",
                "sha256": visual.sha_file(asset),
                "frame_contract_sha256": "f" * 64,
                "character_visual_contract_sha256": visual.sha_file(legacy),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(visual, "load", lambda _ep: current)
    monkeypatch.setattr(visual, "_repo_asset", lambda _raw: asset)

    assert "character pixel master spec sha stale" in visual.validate_pixel_master(
        tmp_path
    )
