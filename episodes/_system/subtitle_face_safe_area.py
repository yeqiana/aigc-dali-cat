#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YuNet subtitle-vs-face safe-area shadow diagnostic.

This evidence is advisory only. It does not change local caption PASS policy or
Episode state; the Caption/Image Critic receives overlap hints when available.
"""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import caption_ocr_diagnostic as ocr
import local_vision_shadow
import story_json
import visual_fingerprint

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/runtime/diagnostics/subtitle-face-safe-area.json")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _intersection(left, right) -> tuple[float, float]:
    x1, y1 = max(left[0], right[0]), max(left[1], right[1])
    x2, y2 = min(left[2], right[2]), min(left[3], right[3])
    area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    subtitle_area = max(1.0, (left[2] - left[0]) * (left[3] - left[1]))
    return area, area / subtitle_area


def _faces(path: Path, model: Path, *, threshold: float = 0.6) -> list[dict]:
    import cv2
    import numpy as np
    pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if pixels is None:
        raise ValueError("OpenCV could not decode subtitle base image")
    height, width = pixels.shape[:2]
    if hasattr(cv2, "FaceDetectorYN"):
        detector = cv2.FaceDetectorYN.create(str(model), "", (width, height), threshold, 0.3, 5000)
    elif hasattr(cv2, "FaceDetectorYN_create"):
        detector = cv2.FaceDetectorYN_create(str(model), "", (width, height), threshold, 0.3, 5000)
    else:
        raise RuntimeError("installed OpenCV does not expose FaceDetectorYN")
    _retval, raw_faces = detector.detect(pixels)
    rows = []
    for raw in raw_faces if raw_faces is not None else []:
        x, y, w, h = [float(value) for value in raw[:4]]
        rows.append({
            "box_xyxy": [round(x, 2), round(y, 2), round(x + w, 2), round(y + h, 2)],
            "confidence": round(float(raw[-1]), 6),
        })
    return rows


def run(ep: Path, keys: list[str] | None = None) -> dict:
    ep = Path(ep).resolve()
    started = time.perf_counter()
    model = local_vision_shadow.resolve_yunet_model()
    if model is None:
        report = {
            "schema_version": 1, "status": "SKIPPED", "diagnostic_only": True,
            "may_affect_gate": False, "reason": "MODEL_MISSING", "generated_at": now(),
        }
        story_json.write_json(ep / REL, report)
        return report
    layout_path = ep / ocr.LAYOUT_REPORT_REL
    try:
        layout = story_json.read_json(layout_path)
        requested = None if keys is None else {str(key).zfill(2) for key in keys}
        rows = {}
        overlap_frames = []
        unknown_frames = []
        no_subtitle_frames = []
        for key, item in sorted((layout.get("frames") or {}).items()):
            if requested is not None and key not in requested:
                continue
            rect = ocr._subtitle_rect(item)
            if rect is None:
                rows[key] = {"status": "NO_SUBTITLE", "face_count": 0, "overlaps": []}
                no_subtitle_frames.append(key)
                continue
            image = ocr._resolve_repo_file(item.get("base_path"))
            expected = str(item.get("base_sha256") or "").lower()
            actual = visual_fingerprint.sha256_file(image)
            if expected and expected != actual:
                rows[key] = {"status": "UNKNOWN", "reason": "BASE_SHA_DRIFT", "overlaps": []}
                unknown_frames.append(key)
                continue
            faces = _faces(image, model)
            overlaps = []
            for index, face in enumerate(faces):
                area, ratio = _intersection(rect, face["box_xyxy"])
                if area > 0:
                    overlaps.append({
                        "face_index": index,
                        "face_box_xyxy": face["box_xyxy"],
                        "confidence": face["confidence"],
                        "overlap_pixels": round(area, 2),
                        "subtitle_overlap_ratio": round(ratio, 6),
                    })
            if overlaps:
                overlap_frames.append(key)
            rows[key] = {
                "status": "COMPLETE",
                "base_sha256": actual,
                "subtitle_box_xyxy": [round(float(x), 2) for x in rect],
                "face_count": len(faces),
                "overlaps": overlaps,
            }
        valid_count = len(rows) - len(unknown_frames)
        overall_status = (
            "COMPLETE" if not unknown_frames
            else "PARTIAL" if valid_count > 0
            else "UNKNOWN"
        )
        report = {
            "schema_version": 1, "status": overall_status, "diagnostic_only": True,
            "may_affect_gate": False, "generated_at": now(),
            "layout_report_sha256": visual_fingerprint.sha256_file(layout_path),
            "tool": {"name": "OpenCV YuNet", "model_filename": model.name,
                     "model_sha256": visual_fingerprint.sha256_file(model)},
            "frames": rows,
            "summary": {
                "checked_frames": len(rows),
                "face_overlap_frames": sorted(overlap_frames),
                "face_overlap_count": len(overlap_frames),
                "unknown_frames": sorted(unknown_frames),
                "unknown_count": len(unknown_frames),
                "no_subtitle_frames": sorted(no_subtitle_frames),
                "valid_count": valid_count,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
            },
        }
    except Exception as exc:
        report = {
            "schema_version": 1, "status": "FAILED", "diagnostic_only": True,
            "may_affect_gate": False, "generated_at": now(),
            "reason": f"{type(exc).__name__}: {exc}",
        }
    story_json.write_json(ep / REL, report)
    return report


def hint(ep: Path, keys: list[str]) -> str:
    ep = Path(ep).resolve()
    path = ep / REL
    if not path.is_file():
        return ""
    report = story_json.read_json(path, default={})
    if report.get("status") not in {"COMPLETE", "PARTIAL"}:
        return ""
    layout = ep / ocr.LAYOUT_REPORT_REL
    if not layout.is_file() or report.get("layout_report_sha256") != visual_fingerprint.sha256_file(layout):
        return ""
    hits = []
    for key in keys:
        row = (report.get("frames") or {}).get(str(key).zfill(2)) or {}
        overlaps = row.get("overlaps") or []
        if overlaps:
            hits.append(f"frame {str(key).zfill(2)}: subtitle overlaps {len(overlaps)} YuNet face box(es)")
    if not hits:
        return ""
    return "Local YuNet subtitle-face pre-scan (advisory): " + "; ".join(hits) + ". Verify on actual pixels."
