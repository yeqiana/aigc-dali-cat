from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_ocr_diagnostic
import local_vision_shadow
import frame_review_persistence
import frame_semantic_review
import incremental_frame_review
import visual_face_diagnostic


def _temp_episode():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="local-vision-shadow-", dir=base)


def test_caption_ocr_missing_dependency_is_skipped_and_writes_report():
    with _temp_episode() as raw:
        ep = Path(raw)
        with patch.dict(sys.modules, {"rapidocr": None}):
            data = local_vision_shadow.run_caption_ocr_shadow(ep)
        assert data["status"] == "SKIPPED"
        assert data["reason"] == "DEPENDENCY_MISSING"
        assert data["may_affect_gate"] is False
        assert (ep / local_vision_shadow.OCR_OUTPUT_REL).is_file()


def test_caption_ocr_diagnose_failure_is_fail_soft_and_writes_report():
    with _temp_episode() as raw:
        ep = Path(raw)
        fake = type("fake_rapidocr", (), {"RapidOCR": object})
        with patch.dict(sys.modules, {"rapidocr": fake}), \
                patch.object(caption_ocr_diagnostic, "diagnose",
                             side_effect=ValueError("layout audit is not canonical")):
            data = local_vision_shadow.run_caption_ocr_shadow(ep, keys=["01"])
        assert data["status"] == "SKIPPED"
        assert data["reason"] == "FAILED"
        assert "layout audit is not canonical" in data["detail"]
        assert (ep / local_vision_shadow.OCR_OUTPUT_REL).is_file()


def test_caption_ocr_passes_normalized_keys_through():
    with _temp_episode() as raw:
        ep = Path(raw)
        captured = {}

        def fake_diagnose(ep_arg, *, engine=None, keys=None):
            captured["keys"] = keys
            return {"diagnostic_only": True, "may_affect_gate": False,
                    "status": "COMPLETE", "summary": {}, "frames": {}}

        fake = type("fake_rapidocr", (), {"RapidOCR": object})
        with patch.dict(sys.modules, {"rapidocr": fake}), \
                patch.object(caption_ocr_diagnostic, "diagnose", side_effect=fake_diagnose):
            local_vision_shadow.run_caption_ocr_shadow(ep, keys=["1", "05"])
        assert captured["keys"] == {"01", "05"}


def test_visual_face_missing_model_is_skipped_and_writes_report():
    with _temp_episode() as raw:
        ep = Path(raw)
        with patch.object(local_vision_shadow, "resolve_yunet_model", return_value=None):
            data = local_vision_shadow.run_visual_face_shadow(ep)
        assert data["status"] == "SKIPPED"
        assert data["reason"] == "MODEL_MISSING"
        assert data["may_affect_gate"] is False
        assert (ep / local_vision_shadow.FACE_OUTPUT_REL).is_file()


def test_visual_face_success_is_visible_to_gate_hint():
    with _temp_episode() as raw:
        ep = Path(raw)
        model = ep / "face.onnx"
        model.write_bytes(b"model")
        with patch.object(local_vision_shadow, "resolve_yunet_model", return_value=model), \
                patch.object(visual_face_diagnostic, "diagnose", return_value={
                    "summary": {"detected_face_count": 2, "expected_primary_count": 2}}), \
                patch.object(local_vision_shadow, "gate_hint_enabled", return_value=True):
            data = local_vision_shadow.run_visual_face_shadow(ep)
            assert data["status"] == "COMPLETE"
            assert "2 candidate face" in local_vision_shadow.face_hint(ep)


def test_resolve_yunet_model_uses_env_override_first():
    with _temp_episode() as raw:
        model = Path(raw) / "yunet.onnx"
        model.write_bytes(b"onnx")
        with patch.dict(os.environ, {local_vision_shadow.YUNET_ENV: str(model)}):
            assert local_vision_shadow.resolve_yunet_model() == model


def test_shadow_runners_return_disabled_when_switch_is_off():
    with _temp_episode() as raw:
        ep = Path(raw)
        with patch.object(local_vision_shadow, "enabled", return_value=False):
            assert local_vision_shadow.run_caption_ocr_shadow(ep)["status"] == "DISABLED"
            assert local_vision_shadow.run_visual_face_shadow(ep)["status"] == "DISABLED"
        # Disabled runs must not write any report file.
        assert not (ep / local_vision_shadow.OCR_OUTPUT_REL).is_file()
        assert not (ep / local_vision_shadow.FACE_OUTPUT_REL).is_file()


def test_ocr_hint_is_empty_unless_gate_hint_enabled():
    with _temp_episode() as raw:
        ep = Path(raw)
        with patch.object(local_vision_shadow, "gate_hint_enabled", return_value=False):
            assert local_vision_shadow.ocr_hint(ep, keys=["01"]) == ""
        with patch.object(local_vision_shadow, "gate_hint_enabled", return_value=True), \
                patch.object(local_vision_shadow, "_read_report", return_value={
                    "status": "COMPLETE",
                    "frames": {"01": {"overlaps": [
                        {"recognized_text": "招牌", "subtitle_overlap_ratio": 0.5},
                    ]}},
                }):
            hint = local_vision_shadow.ocr_hint(ep, keys=["01"])
        assert "frame 01" in hint
        assert "招牌" in hint
        assert "advisory" in hint


def test_face_hint_renders_detected_count_when_enabled():
    with _temp_episode() as raw:
        ep = Path(raw)
        with patch.object(local_vision_shadow, "gate_hint_enabled", return_value=False):
            assert local_vision_shadow.face_hint(ep) == ""
        with patch.object(local_vision_shadow, "gate_hint_enabled", return_value=True), \
                patch.object(local_vision_shadow, "_read_report", return_value={
                    "status": "COMPLETE",
                    "summary": {"detected_face_count": 2, "expected_primary_count": 2},
                }):
            hint = local_vision_shadow.face_hint(ep)
        assert "2" in hint
        assert "advisory" in hint


def test_local_caption_gate_requires_current_evidence_and_render_integrity():
    from PIL import Image
    with _temp_episode() as raw:
        ep = Path(raw)
        image = ep / "base.png"
        Image.new("RGB", (80, 80), (30, 30, 30)).save(image)
        image_sha = caption_ocr_diagnostic._sha(image)
        layout = ep / caption_ocr_diagnostic.LAYOUT_REPORT_REL
        layout.parent.mkdir(parents=True, exist_ok=True)
        layout.write_text(__import__("json").dumps({"frames": {"01": {
            "base_path": str(image), "base_sha256": image_sha,
        }}}), encoding="utf-8")
        caption_sha = "c" * 64
        report = {
            "status": "COMPLETE",
            "source": {"layout_report_sha256": caption_ocr_diagnostic._sha(layout)},
            "frames": {"01": {"status": "COMPLETE", "base_sha256": image_sha,
                              "subtitle_box_xyxy": [5, 5, 50, 30], "overlaps": []}},
            "tool": {"name": "RapidOCR"},
        }
        frames = [{"frame": "01", "sha256": image_sha}]
        review = {"decision": "pass", "checks": {"caption_image_support": True},
                  "caption_sha256": caption_sha}
        with patch.object(local_vision_shadow, "local_gate_enabled", return_value=True), \
                patch.object(incremental_frame_review, "verify_episode", return_value=[]), \
                patch.object(frame_semantic_review, "frame_records", return_value=frames), \
                patch.object(incremental_frame_review, "caption_state", return_value={
                    "frame_sha256": {"01": caption_sha}}), \
                patch.object(frame_review_persistence, "load", return_value=review):
            integrity = {"01": {"status": "PASS"}}
            cleared = local_vision_shadow.locally_clear_caption_frames(ep, ["01"], report, integrity)
            assert "01" in cleared
            assert local_vision_shadow.local_caption_evidence_current(ep, "01", cleared["01"])
            report["frames"]["01"]["overlaps"] = [{"recognized_text": "sign"}]
            assert local_vision_shadow.locally_clear_caption_frames(ep, ["01"], report, integrity) == {}
            report["frames"]["01"]["overlaps"] = []
            assert local_vision_shadow.locally_clear_caption_frames(ep, ["01"], report) == {}
            layout.write_text(layout.read_text(encoding="utf-8") + " ", encoding="utf-8")
            assert not local_vision_shadow.local_caption_evidence_current(ep, "01", cleared["01"])
