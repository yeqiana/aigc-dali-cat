from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import auto_repair_enqueue


def test_repair_prompt_is_story_neutral() -> None:
    prompt = auto_repair_enqueue.repair_prompt(3, ["ANOMALY_NOT_READABLE"])
    assert "天界" not in prompt
    assert "不改故事" in prompt
    assert len(prompt) <= 260
    assert len(prompt.encode("utf-8")) <= 900


def test_repair_prompt_lifts_frame_contract_cues_and_camera_authorship() -> None:
    prompt = auto_repair_enqueue.repair_prompt(
        3,
        ["ANOMALY_NOT_READABLE", "POV_RECORDER_OBVIOUSLY_ILLEGAL"],
        required_visual_cues=[
            "dust-covered furniture",
            "clean enamel tea mug containing fresh water",
        ],
        camera_owner="P01",
        camera_position="doorway chest height",
    )
    assert "dust-covered furniture" in prompt
    assert "clean enamel tea mug containing fresh water" in prompt
    assert "持机人=P01" in prompt
    assert "禁止幽灵机位" in prompt
    assert "天界" not in prompt
    assert len(prompt) <= 260
    assert len(prompt.encode("utf-8")) <= 900
