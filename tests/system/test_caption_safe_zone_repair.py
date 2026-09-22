from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_image_audit
import story_json
import subtitle_layout


def _temp_episode():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="caption-safe-zone-", dir=base)


def test_pixel_safe_override_is_bounded_to_one_move():
    with _temp_episode() as raw:
        ep = Path(raw)
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        story_json.write_json(ep / "meta/production-ledger.json", {
            "canvas": {"width": 1080, "height": 1350},
            "frames": {"01": {}},
        })
        story_json.write_json(ep / subtitle_layout.REPORT_REL, {
            "frames": {"01": {"y_ratio": 0.52, "y": 702}},
        })
        result = subtitle_layout.apply_pixel_safe_overrides(ep, {
            "01": {"y_ratio": 0.32, "reason": "face occupies left-middle"},
        })
        assert result["updated"] == ["01"]
        cfg = story_json.read_json(ep / "meta/subtitle-layout.json")
        assert cfg["frames"]["01"]["y"] == 432
        assert cfg["frames"]["01"]["auto_placement_repairs_used"] == 1
        try:
            subtitle_layout.apply_pixel_safe_overrides(ep, {
                "01": {"y_ratio": 0.70, "reason": "second move forbidden"},
            })
            raise AssertionError("second automatic placement repair must fail")
        except RuntimeError as exc:
            assert "budget exhausted" in str(exc)


def test_configured_dirty_frames_recovers_override_before_next_audit():
    with _temp_episode() as raw:
        ep = Path(raw)
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        story_json.write_json(ep / "meta/subtitle-layout.json", {
            "frames": {"01": {"y": 432, "auto_placement_repairs_used": 1}},
        })
        story_json.write_json(ep / subtitle_layout.REPORT_REL, {
            "frames": {"01": {"y": 702}},
        })
        assert subtitle_layout.configured_dirty_frames(ep) == ["01"]
        story_json.write_json(ep / subtitle_layout.REPORT_REL, {
            "frames": {"01": {"y": 432}},
        })
        assert subtitle_layout.configured_dirty_frames(ep) == []


def test_caption_audit_moves_only_obstructed_frame_then_reaudits_new_pixels():
    ep = Path("ep")
    old = {"frame": "01", "path": Path("old.png"), "path_rel": "old.png", "sha256": "a" * 64}
    new = {"frame": "01", "path": Path("new.png"), "path_rel": "new.png", "sha256": "b" * 64}
    source_meta = {"source_path": "captions.yaml", "source_sha256": "c" * 64,
                   "review_image": {"mode": "final_publish_with_subtitle", "layout_current": True}}
    first = {
        "frames": [{"frame": "01", "supported": True, "subtitle_unobstructed": False,
                    "suggested_y_ratio": 0.32, "obstruction_reason": "subtitle covers face", "notes": "face overlap"}],
        "summary": {"passed": False},
        "critic_provenance": {"runtime": "CODEX_ISOLATED"},
    }
    second = {
        "frames": [{"frame": "01", "supported": True, "subtitle_unobstructed": True,
                    "suggested_y_ratio": None, "obstruction_reason": "", "notes": "clear"}],
        "summary": {"passed": True},
        "critic_provenance": {"runtime": "CODEX_ISOLATED"},
    }
    calls = []

    def run_chunk(*args, **kwargs):
        calls.append(kwargs.get("cycle", 1))
        return first if len(calls) == 1 else second

    with patch.object(caption_image_audit.subtitle_layout, "configured_dirty_frames", return_value=[]), \
            patch.object(caption_image_audit, "dirty_frames", return_value=(
                [old], {"frames": {}}, {"01": "a" * 64}, {"01": "d" * 64}, {"01": "文案"}, source_meta)), \
            patch.object(caption_image_audit.base, "frame_records", return_value=[old]), \
            patch.object(caption_image_audit, "_run_chunk", side_effect=run_chunk), \
            patch.object(caption_image_audit.subtitle_layout, "current_frame_y_ratio", return_value=0.52), \
            patch.object(caption_image_audit, "_placement_repairs_used", return_value=0), \
            patch.object(caption_image_audit.subtitle_layout, "apply_pixel_safe_overrides") as apply_override, \
            patch.object(caption_image_audit.subtitle_layout, "render_frames") as render_frames, \
            patch.object(caption_image_audit, "_review_frame_records", return_value=(
                [new], {"mode": "final_publish_with_subtitle", "layout_current": True, "layout_audit_sha256": "e" * 64})), \
            patch.object(caption_image_audit, "_hashes", return_value=(
                {"01": "b" * 64}, {"01": "d" * 64}, {"01": "文案"}, {"source_path": "captions.yaml", "source_sha256": "c" * 64})), \
            patch.object(caption_image_audit.runtime_router, "detect", return_value=("WORK", "test")), \
            patch.object(caption_image_audit.runtime_router, "vision_review_runtime", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit, "_write"):
        ok, evidence = caption_image_audit.ensure(ep, codex_raw=None, timeout=30)
    assert ok is True
    assert calls == [1, 2]
    apply_override.assert_called_once()
    render_frames.assert_called_once_with(ep.resolve(), ["01"])
    assert evidence["frames"]["01"]["image_sha256"] == "b" * 64
    assert evidence["frames"]["01"]["review_cycle"] == 2
    assert evidence["summary"]["auto_repaired_frames"] == ["01"]
