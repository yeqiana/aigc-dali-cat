from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import auto_repair_enqueue  # noqa: E402


def test_marked_production_scout_finding_waits_for_first_pass_barrier(monkeypatch, tmp_path):
    queue = {
        "items": [
            {
                "id": "q16",
                "frame": 16,
                "status": "scout_repair",
                "vision_batch_review": {
                    "issue_codes": [
                        "GHOST_CAMERA_ALL_PARTICIPANTS_VISIBLE",
                        "P01_WARDROBE_AND_ROLE_DRIFT",
                    ],
                    "reason": "camera authorship and wardrobe continuity failed",
                },
            }
        ]
    }
    monkeypatch.setattr(auto_repair_enqueue.scheduler_core, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(auto_repair_enqueue.scheduler_core,"queue_transaction",lambda _ep: __import__("contextlib").nullcontext())
    monkeypatch.setattr(auto_repair_enqueue.scheduler_core,"save_queue",lambda *_args:None)
    from unittest.mock import patch
    with patch.object(auto_repair_enqueue,"enqueue") as enqueue:
        result = auto_repair_enqueue.enqueue_marked_repairs(tmp_path)

    assert result["marked"] == 1
    assert result["repair_items_ready"] == 0
    assert result["results"][0]["status"] == "DEFERRED_FIRST_PASS_BARRIER"
    enqueue.assert_not_called()
