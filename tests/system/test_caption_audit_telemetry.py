from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_image_audit


def _row(frame: str) -> dict:
    return {"frame": frame, "path": Path(frame + ".png"), "path_rel": frame + ".png",
            "sha256": ("a" * 64)[:62] + ("0" + frame)[-2:]}


def test_vision_call_telemetry_is_recorded():
    ep = Path("ep")
    row = _row("01")
    source = {"review_image": {"mode": "final_publish_with_subtitle", "layout_current": True}}
    result = {
        "frames": [{"frame": "01", "supported": True, "subtitle_unobstructed": True,
                    "suggested_y_ratio": None, "obstruction_reason": "", "notes": "ok"}],
        "summary": {"passed": True},
        "_vision_telemetry": {"vision_call": True, "elapsed_seconds": 1.5,
                               "tokens": {"input_tokens": 100, "output_tokens": 50}},
    }
    with patch.object(caption_image_audit.subtitle_layout, "configured_dirty_frames", return_value=[]), \
            patch.object(caption_image_audit, "dirty_frames", return_value=(
                [row], {"frames": {}}, {"01": row["sha256"]}, {"01": "b" * 64}, {"01": "zi mu"}, source)), \
            patch.object(caption_image_audit.base, "frame_records", return_value=[row]), \
            patch.object(caption_image_audit.local_vision_shadow, "run_caption_ocr_shadow", return_value={"status": "COMPLETE"}), \
            patch.object(caption_image_audit.local_vision_shadow, "locally_clear_caption_frames", return_value={}), \
            patch.object(caption_image_audit, "_run_chunk", return_value=result), \
            patch.object(caption_image_audit.runtime_router, "detect", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit.runtime_router, "vision_review_runtime", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit, "_write"):
        ok, evidence = caption_image_audit.ensure(ep, timeout=30)
    assert ok is True
    telemetry = evidence["summary"]["vision_review_telemetry"]
    assert telemetry["vision_call_count"] == 1
    assert telemetry["vision_frames"] == 1
    assert telemetry["vision_candidate_frames"] == 1
    assert telemetry["empty_caption_count"] == 0
    assert telemetry["local_skipped_frames"] == 0
    assert abs(telemetry["vision_elapsed_seconds"] - 1.5) < 1e-9
    assert telemetry["vision_tokens"] == {"input_tokens": 100, "output_tokens": 50}


def test_local_skip_and_empty_caption_counts():
    ep = Path("ep")
    rows = [_row("01"), _row("02"), _row("03")]
    source = {"review_image": {"mode": "final_publish_with_subtitle", "layout_current": True}}
    image_sha = {r["frame"]: r["sha256"] for r in rows}
    caption_sha = {"01": "x" * 64, "02": "y" * 64, "03": "z" * 64}
    texts = {"01": "zi mu A", "02": "zi mu B", "03": ""}
    result = {
        "frames": [{"frame": "02", "supported": True, "subtitle_unobstructed": True,
                    "suggested_y_ratio": None, "obstruction_reason": "", "notes": "ok"}],
        "summary": {"passed": True},
        "_vision_telemetry": {"vision_call": True, "elapsed_seconds": 0.7, "tokens": {}},
    }
    with patch.object(caption_image_audit.subtitle_layout, "configured_dirty_frames", return_value=[]), \
            patch.object(caption_image_audit, "dirty_frames", return_value=(
                rows, {"frames": {}}, image_sha, caption_sha, texts, source)), \
            patch.object(caption_image_audit.base, "frame_records", return_value=rows), \
            patch.object(caption_image_audit.local_vision_shadow, "run_caption_ocr_shadow", return_value={"status": "COMPLETE"}), \
            patch.object(caption_image_audit.local_vision_shadow, "locally_clear_caption_frames", return_value={"01": {"base_sha256": rows[0]["sha256"]}}), \
            patch.object(caption_image_audit, "_run_chunk", return_value=result), \
            patch.object(caption_image_audit.runtime_router, "detect", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit.runtime_router, "vision_review_runtime", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit, "_write"):
        ok, evidence = caption_image_audit.ensure(ep, timeout=30)
    assert ok is True
    telemetry = evidence["summary"]["vision_review_telemetry"]
    assert telemetry["empty_caption_count"] == 1
    assert telemetry["vision_candidate_frames"] == 2
    assert telemetry["local_skipped_frames"] == 1
    assert telemetry["vision_frames"] == 1
    assert telemetry["vision_call_count"] == 1


def test_missing_telemetry_stays_fail_soft_and_zero():
    ep = Path("ep")
    row = _row("01")
    source = {"review_image": {"mode": "final_publish_with_subtitle", "layout_current": True}}
    result = {
        "frames": [{"frame": "01", "supported": True, "subtitle_unobstructed": True,
                    "suggested_y_ratio": None, "obstruction_reason": "", "notes": "ok"}],
        "summary": {"passed": True},
    }
    with patch.object(caption_image_audit.subtitle_layout, "configured_dirty_frames", return_value=[]), \
            patch.object(caption_image_audit, "dirty_frames", return_value=(
                [row], {"frames": {}}, {"01": row["sha256"]}, {"01": "b" * 64}, {"01": "zi mu"}, source)), \
            patch.object(caption_image_audit.base, "frame_records", return_value=[row]), \
            patch.object(caption_image_audit.local_vision_shadow, "run_caption_ocr_shadow", return_value={"status": "COMPLETE"}), \
            patch.object(caption_image_audit.local_vision_shadow, "locally_clear_caption_frames", return_value={}), \
            patch.object(caption_image_audit, "_run_chunk", return_value=result), \
            patch.object(caption_image_audit.runtime_router, "detect", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit.runtime_router, "vision_review_runtime", return_value=("CODEX", "test")), \
            patch.object(caption_image_audit, "_write"):
        ok, evidence = caption_image_audit.ensure(ep, timeout=30)
    assert ok is True
    telemetry = evidence["summary"]["vision_review_telemetry"]
    assert telemetry["vision_call_count"] == 0
    assert telemetry["vision_frames"] == 1
    assert telemetry["vision_elapsed_seconds"] == 0.0
    assert telemetry["vision_tokens"] == {}

