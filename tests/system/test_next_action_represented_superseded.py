from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import next_action  # noqa: E402


def test_superseded_original_with_real_output_remains_represented():
    q = {
        "items": [
            {
                "frame": 4,
                "kind": "original",
                "scope": "batch",
                "status": "superseded",
                "output_path": "episodes/x/media/candidates/scheduled/04-a1.png",
            },
            {
                "frame": 5,
                "kind": "original",
                "scope": "batch",
                "status": "superseded",
                "output_path": None,
            },
        ]
    }
    assert next_action._represented_original_frames(q) == {4}
