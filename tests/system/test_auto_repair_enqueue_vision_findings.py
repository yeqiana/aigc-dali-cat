from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import auto_repair_enqueue  # noqa: E402


def test_marked_repair_carries_vision_review_findings(monkeypatch, tmp_path):
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
    captured = {}

    monkeypatch.setattr(auto_repair_enqueue.scheduler_core, "load_queue", lambda _ep: queue)

    def fake_enqueue(_ep, *, frame, findings, source, review_note):
        captured.update(
            frame=frame,
            findings=list(findings),
            source=source,
            review_note=review_note,
        )
        return {"status": "NOT_REPAIRABLE", "frame": frame}

    monkeypatch.setattr(auto_repair_enqueue, "enqueue", fake_enqueue)

    result = auto_repair_enqueue.enqueue_marked_repairs(tmp_path)

    assert result["marked"] == 1
    assert captured["frame"] == 16
    assert captured["source"] == "PRODUCTION_REVIEW"
    assert "GHOST_CAMERA_ALL_PARTICIPANTS_VISIBLE" in captured["findings"]
    assert "P01_WARDROBE_AND_ROLE_DRIFT" in captured["findings"]
    assert "camera authorship and wardrobe continuity failed" in captured["findings"]
