from pathlib import Path
import sys

SYSTEM_DIR = Path(__file__).resolve().parents[2] / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM_DIR))

import json
import tempfile

from asset_boundary_gate import classify, check_asset_path, verify_episode


def test_placeholder_classification():
    assert classify("assets/placeholders/a.png") == "TEST_ASSET"


def test_placeholder_cannot_be_production_media():
    assert check_asset_path("assets/placeholders/a.png/media/raw/frame.png")


def test_normal_episode_media_not_blocked():
    assert not check_asset_path("episodes/10_x/media/raw/01.png")


def test_production_ledger_cannot_reference_test_asset():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir()
        (ep / "meta/production-ledger.json").write_text(json.dumps({
            "frames": {"01": {"approved_asset": {"path": "assets/placeholders/fake.png"}}}
        }), encoding="utf-8")
        errors = verify_episode(ep)
        assert errors and "approved_asset" in errors[0]


def test_release_assets_cannot_reference_demo_root():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir()
        (ep / "meta/release-manifest.json").write_text(json.dumps({
            "release": {"cover_path": "assets/demo/cover.png"}
        }), encoding="utf-8")
        errors = verify_episode(ep)
        assert errors and "cover_path" in errors[0]
