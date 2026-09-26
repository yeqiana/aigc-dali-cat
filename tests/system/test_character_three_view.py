from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import character_three_view as three_view  # noqa: E402


def test_absent_three_view_is_optional(tmp_path):
    assert three_view.validate(tmp_path) == []
    assert three_view.summary(tmp_path) == {"applicable": False}
    assert three_view.reference(tmp_path, "P01") is None


def test_three_view_reference_binds_front_side_back_board(monkeypatch, tmp_path):
    asset = tmp_path / "P01-three-view.png"
    asset.write_bytes(b"three-view-board")
    manifest = tmp_path / three_view.MANIFEST_REL
    manifest.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        three_view.character_contract,
        "load",
        lambda _ep: {"cast": {"members": [{"id": "P01"}]}},
    )
    monkeypatch.setattr(three_view, "repo_asset", lambda _raw: asset)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "characters": {
                    "P01": {
                        "board": "ignored.png",
                        "sha256": three_view.sha_file(asset),
                        "views": ["front", "side", "back"],
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert three_view.validate(tmp_path) == []
    summary = three_view.summary(tmp_path)
    assert summary["applicable"] is True
    assert summary["role"] == "PREPRODUCTION_IDENTITY_ANCHOR"
    ref = three_view.reference(tmp_path, "P01")
    assert ref["role"] == "character_three_view:P01"
    assert ref["kind"] == "identity"
    assert ref["views"] == ["front", "side", "back"]


def test_three_view_rejects_incomplete_view_declaration(monkeypatch, tmp_path):
    asset = tmp_path / "P01-three-view.png"
    asset.write_bytes(b"three-view-board")
    manifest = tmp_path / three_view.MANIFEST_REL
    manifest.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        three_view.character_contract,
        "load",
        lambda _ep: {"cast": {"members": [{"id": "P01"}]}},
    )
    monkeypatch.setattr(three_view, "repo_asset", lambda _raw: asset)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "characters": {
                    "P01": {
                        "board": "ignored.png",
                        "sha256": three_view.sha_file(asset),
                        "views": ["front", "side"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    assert any("front/side/back" in error for error in three_view.validate(tmp_path))
