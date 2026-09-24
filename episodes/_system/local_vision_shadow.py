#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-soft local vision shadow wiring for production review entrypoints.

These helpers wrap the standalone diagnostics (caption_ocr_diagnostic and
visual_face_diagnostic) so the caption/image audit and the Visual Lock baseline
gate can record derived OCR/face hints without ever blocking a review, changing
a result, or mutating episode state. Every path returns a report dict and never
raises; missing models or dependencies are recorded as SKIPPED/FAILED reports.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = ROOT / ".storyos_cache"
MODELS_DIR = CACHE_ROOT / "models"
OCR_OUTPUT_REL = Path("meta/runtime/diagnostics/caption-ocr-shadow.json")
FACE_OUTPUT_REL = Path("meta/runtime/diagnostics/visual-face-shadow.json")
YUNET_ENV = "STORY_OS_YUNET_MODEL"


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _safe_write(path: Path, data: dict) -> None:
    try:
        _atomic_write(path, data)
    except Exception:
        pass


def _skipped(tool: dict, reason: str, detail: str, started: float) -> dict:
    return {
        "schema_version": 1,
        "diagnostic_only": True,
        "may_affect_gate": False,
        "status": "SKIPPED",
        "tool": tool,
        "reason": reason,
        "detail": detail,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def _finish(data: dict, started: float) -> dict:
    data["elapsed_seconds_total"] = round(time.perf_counter() - started, 3)
    return data


def _config_section() -> dict:
    try:
        import storyos_config
        data = storyos_config._load(storyos_config.CONFIG_PATH)
    except Exception:
        return {}
    return (data.get("runtime") or {}).get("review", {}).get("local_vision_shadow") or {}


def enabled() -> bool:
    """Whether the local shadow diagnostics should run at all (fail-safe: off)."""
    return _config_section().get("enabled") is True


def gate_hint_enabled() -> bool:
    """Whether shadow results may be injected as advisory hints into critics (off)."""
    return _config_section().get("gate_hint") is True


def local_gate_enabled() -> bool:
    """Allow a complete, narrowly defined local caption check to replace a vision call."""
    section = _config_section()
    return section.get("enabled") is True and section.get("local_gate_enabled") is True


def locally_clear_caption_frames(ep, keys, ocr_report: dict, integrity: dict | None = None) -> dict[str, dict]:
    """Return frames with current semantic support and complete local placement checks.

    Missing or stale evidence remains in the pixel critic lane. This policy
    deliberately accepts that OCR cannot detect covered people or props.
    """
    if not local_gate_enabled() or ocr_report.get("status") != "COMPLETE":
        return {}
    try:
        import caption_ocr_diagnostic as ocr
        import frame_review_persistence
        import frame_semantic_review as semantic
        import incremental_frame_review as incremental

        ep = Path(ep).resolve()
        if incremental.verify_episode(ep):
            return {}
        frames = semantic.frame_records(ep, require_files=True)
        captions = incremental.caption_state(ep, frames)
        frame_map = {row["frame"]: row for row in frames}
        layout_path = ep / ocr.LAYOUT_REPORT_REL
        if ocr_report.get("source", {}).get("layout_report_sha256") != ocr._sha(layout_path):
            return {}
        layouts = json.loads(layout_path.read_text(encoding="utf-8")).get("frames") or {}
        cleared = {}
        for raw_key in keys:
            key = str(raw_key).zfill(2)
            try:
                if (integrity or {}).get(key, {}).get("status") != "PASS":
                    continue
                result = (ocr_report.get("frames") or {}).get(key) or {}
                layout = layouts.get(key) or {}
                review = frame_review_persistence.load(ep, key) or {}
                source = frame_map[key]
                if (result.get("status") != "COMPLETE" or result.get("overlaps")
                        or result.get("base_sha256") != source["sha256"]
                        or str(layout.get("base_sha256") or "").lower() != source["sha256"]
                        or review.get("decision") != "pass"
                        or (review.get("checks") or {}).get("caption_image_support") is not True
                        or review.get("caption_sha256") != captions["frame_sha256"][key]):
                    continue
                rect = result.get("subtitle_box_xyxy")
                if not isinstance(rect, list) or len(rect) != 4:
                    continue
                image_path = ocr._resolve_repo_file(layout.get("base_path"))
                from PIL import Image
                with Image.open(image_path) as image:
                    box = tuple(int(value) for value in rect)
                    if (box[0] < 0 or box[1] < 0 or box[2] > image.width
                            or box[3] > image.height or box[2] <= box[0] or box[3] <= box[1]):
                        continue
                cleared[key] = {
                    "mode": "local_position_with_semantic_evidence",
                    "base_sha256": source["sha256"],
                    "layout_report_sha256": ocr_report["source"]["layout_report_sha256"],
                    "caption_sha256": captions["frame_sha256"][key],
                    "ocr_tool": ocr_report.get("tool"),
                    "render_integrity": (integrity or {}).get(key),
                    "review_source": "current_frame_semantic_review",
                }
            except Exception:
                continue
        return cleared
    except Exception:
        return {}


def local_caption_validation_context(ep) -> dict | None:
    """Load shared authority once when several locally reviewed frames are checked."""
    if not local_gate_enabled():
        return None
    try:
        import caption_ocr_diagnostic as ocr
        import frame_semantic_review as semantic
        import incremental_frame_review as incremental

        ep = Path(ep).resolve()
        if incremental.verify_episode(ep):
            return None
        frames = semantic.frame_records(ep, require_files=True)
        captions = incremental.caption_state(ep, frames)
        return {
            "frames": {row["frame"]: row for row in frames},
            "caption_sha": captions["frame_sha256"],
            "layout_sha": ocr._sha(ep / ocr.LAYOUT_REPORT_REL),
        }
    except Exception:
        return None


def local_caption_evidence_current(ep, key: str, evidence: dict, context: dict | None = None) -> bool:
    """Invalidate local passes when their semantic, caption, image, or layout input moves."""
    if not isinstance(evidence, dict) or not local_gate_enabled():
        return False
    context = context if context is not None else local_caption_validation_context(ep)
    if not context:
        return False
    try:
        import frame_review_persistence
        key = str(key).zfill(2)
        review = frame_review_persistence.load(ep, key) or {}
        return (
            evidence.get("base_sha256") == context["frames"][key]["sha256"]
            and evidence.get("layout_report_sha256") == context["layout_sha"]
            and evidence.get("caption_sha256") == context["caption_sha"][key]
            and review.get("decision") == "pass"
            and (review.get("checks") or {}).get("caption_image_support") is True
            and review.get("caption_sha256") == context["caption_sha"][key]
        )
    except Exception:
        return False


def _read_report(ep, rel: Path):
    path = Path(ep).resolve() / rel
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def ocr_hint(ep, keys=None) -> str:
    """Advisory OCR text for critics; empty unless gate_hint is enabled."""
    if not gate_hint_enabled():
        return ""
    report = _read_report(ep, OCR_OUTPUT_REL)
    if not report or report.get("status") not in ("COMPLETE", "PARTIAL"):
        return ""
    frames = report.get("frames") or {}
    hits = []
    for key in (keys or []):
        row = frames.get(str(key).zfill(2)) or {}
        overlaps = row.get("overlaps") or []
        if overlaps:
            texts = [str(o.get("recognized_text") or "")[:60] for o in overlaps[:3]]
            hits.append(f"frame {str(key).zfill(2)}: {len(overlaps)} overlap candidate(s), OCR text={texts}")
    if not hits:
        return ""
    return ("Local RapidOCR pre-scan (advisory, not authoritative) flagged: " + "; ".join(hits) +
            ". Inspect the final pixels yourself; no OCR hit does NOT mean no obstruction.")


def face_hint(ep) -> str:
    """Advisory face-box text for the baseline critic; empty unless gate_hint enabled."""
    if not gate_hint_enabled():
        return ""
    report = _read_report(ep, FACE_OUTPUT_REL)
    if not report or report.get("status") != "COMPLETE":
        return ""
    summary = report.get("summary") or {}
    count = summary.get("detected_face_count")
    if count is None:
        return ""
    return ("Local YuNet pre-scan (advisory) detected " + str(count) + " candidate face box(es); " +
            "expected primary count " + str(summary.get("expected_primary_count")) + ". " +
            "Verify identity/visibility on pixels yourself; a count match does NOT prove identity.")


def run_caption_ocr_shadow(ep, keys=None) -> dict:
    """Record native-text/subtitle overlap hints for the given frames; never raises."""
    ep = Path(ep).resolve()
    started = time.perf_counter()
    if not enabled():
        return {"status": "DISABLED", "diagnostic_only": True, "may_affect_gate": False}
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        data = _skipped({"name": "RapidOCR", "version": "unknown"},
                        "DEPENDENCY_MISSING", str(exc), started)
        _safe_write(ep / OCR_OUTPUT_REL, data)
        return data
    try:
        engine = RapidOCR()
    except Exception as exc:
        data = _skipped({"name": "RapidOCR", "version": "unknown"},
                        "INITIALIZATION_FAILED", f"{type(exc).__name__}: {exc}", started)
        _safe_write(ep / OCR_OUTPUT_REL, data)
        return data
    try:
        import caption_ocr_diagnostic
        key_set = None if keys is None else {str(key).zfill(2) for key in keys}
        data = caption_ocr_diagnostic.diagnose(ep, engine=engine, keys=key_set)
        data["shadow_invocation"] = {
            "entrypoint": "caption_image_audit",
            "frame_keys": sorted(key_set) if key_set is not None else None,
        }
        data = _finish(data, started)
        _safe_write(ep / OCR_OUTPUT_REL, data)
        return data
    except Exception as exc:
        data = _skipped({"name": "RapidOCR", "version": "unknown"},
                        "FAILED", f"{type(exc).__name__}: {exc}", started)
        _safe_write(ep / OCR_OUTPUT_REL, data)
        return data


def resolve_yunet_model():
    raw = os.environ.get(YUNET_ENV)
    if raw:
        candidate = Path(raw)
        if candidate.is_file():
            return candidate
    if MODELS_DIR.is_dir():
        matches = sorted(MODELS_DIR.glob("face_detection_yunet*.onnx"))
        if matches:
            return matches[0]
    return None


def run_visual_face_shadow(ep) -> dict:
    """Record candidate YuNet face boxes for the baseline; never raises."""
    ep = Path(ep).resolve()
    started = time.perf_counter()
    if not enabled():
        return {"status": "DISABLED", "diagnostic_only": True, "may_affect_gate": False}
    model = resolve_yunet_model()
    if model is None:
        data = _skipped(
            {"name": "OpenCV YuNet", "version": "unknown"},
            "MODEL_MISSING",
            "place YuNet ONNX at .storyos_cache/models/face_detection_yunet*.onnx or set STORY_OS_YUNET_MODEL",
            started,
        )
        _safe_write(ep / FACE_OUTPUT_REL, data)
        return data
    try:
        import cv2  # noqa: F401
    except ImportError as exc:
        data = _skipped({"name": "OpenCV YuNet", "version": "unknown"},
                        "DEPENDENCY_MISSING", str(exc), started)
        _safe_write(ep / FACE_OUTPUT_REL, data)
        return data
    try:
        import visual_face_diagnostic
        data = visual_face_diagnostic.diagnose(ep, model)
        data["status"] = "COMPLETE"
        data["shadow_invocation"] = {"entrypoint": "visual_lock_baseline_gate"}
        data = _finish(data, started)
        _safe_write(ep / FACE_OUTPUT_REL, data)
        return data
    except Exception as exc:
        data = _skipped({"name": "OpenCV YuNet", "version": "unknown"},
                        "FAILED", f"{type(exc).__name__}: {exc}", started)
        _safe_write(ep / FACE_OUTPUT_REL, data)
        return data
