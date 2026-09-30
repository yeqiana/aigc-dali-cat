from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import subtitle_layout  # noqa: E402


def test_subtitle_base_prefers_direct_user_final_publish(tmp_path):
    ep = tmp_path / "ep"
    publish = ep / "media/publish"
    publish.mkdir(parents=True)
    base = publish / "01-final.png"
    base.write_bytes(b"x")
    with patch.object(
        subtitle_layout.final_acceptance,
        "visual_asset_for_frame",
        return_value={"path": str(base), "sha256": "a" * 64, "frame": "01"},
    ), patch.object(subtitle_layout, "resolve_repo_file", return_value=base.resolve()):
        path, source = subtitle_layout.resolve_frame_base(
            ep, "01", {"approved_asset": {"path": "ignored.png"}}
        )
    assert path == base.resolve()
    assert source == "direct_user_final_publish"
