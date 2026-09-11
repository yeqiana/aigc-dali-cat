from pathlib import Path
import sys

SYSTEM_DIR = Path(__file__).resolve().parents[2] / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM_DIR))

from asset_boundary_gate import classify, check_asset_path


def test_placeholder_classification():
    assert classify("assets/placeholders/a.png") == "TEST_ASSET"


def test_placeholder_cannot_be_production_media():
    assert check_asset_path("assets/placeholders/a.png/media/raw/frame.png")


def test_normal_episode_media_not_blocked():
    assert not check_asset_path("episodes/10_x/media/raw/01.png")
