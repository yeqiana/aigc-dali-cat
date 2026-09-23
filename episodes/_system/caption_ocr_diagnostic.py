#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional local OCR shadow diagnostic for subtitle/native-text overlap.

This module writes derived diagnostics only. It never changes caption audit,
production gates, approved pixels, or episode state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT_REPORT_REL = Path("meta/subtitle-layout-audit.json")
OUTPUT_REL = Path("meta/runtime/diagnostics/caption-ocr-shadow.json")
LAYOUT_ENGINE = "story_os_subtitle_layout_v1"
SCHEMA_VERSION = 1
OVERLAP_WARNING_RATIO = 0.10


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _sha(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_repo_file(raw: object) -> Path:
    path = Path(str(raw or ""))
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    path.relative_to(ROOT.resolve())
    if not path.is_file():
        raise ValueError(f"base image not found: {raw}")
    return path


def _rect_union(rects: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float] | None:
    if not rects:
        return None
    return (
        min(row[0] for row in rects), min(row[1] for row in rects),
        max(row[2] for row in rects), max(row[3] for row in rects),
    )


def _subtitle_rect(layout: dict) -> tuple[float, float, float, float] | None:
    lines = [str(line) for line in layout.get("lines") or [] if str(line)]
    if not lines:
        return None
    from PIL import Image, ImageDraw, ImageFont

    font_path = str(layout.get("font") or "")
    font_size = int(layout.get("font_size") or 42)
    stroke = int(layout.get("stroke_width") or 4)
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    x = int(layout.get("x") or 0)
    y = int(layout.get("y") or 0)
    line_height = int(layout.get("line_height") or 54)
    boxes = []
    for index, line in enumerate(lines):
        bounds = draw.textbbox((x, y + index * line_height), line, font=font, stroke_width=stroke)
        # Include a small margin for the blurred shadow drawn by subtitle_layout.
        boxes.append((bounds[0] - 4, bounds[1] - 4, bounds[2] + 4, bounds[3] + 4))
    return _rect_union(boxes)


def _box_to_rect(box: object) -> tuple[float, float, float, float] | None:
    try:
        points = box.tolist() if hasattr(box, "tolist") else box
        if not isinstance(points, (list, tuple)) or len(points) < 4:
            return None
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return min(xs), min(ys), max(xs), max(ys)
    except (TypeError, ValueError, IndexError):
        return None


def _intersection_ratio(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> float:
    x1, y1 = max(left[0], right[0]), max(left[1], right[1])
    x2, y2 = min(left[2], right[2]), min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    return intersection / area if area else 0.0


def _texts(result: object) -> tuple[list, list, list]:
    """Read current RapidOCR dataclass output, with tuple/list compatibility."""
    boxes = getattr(result, "boxes", None)
    texts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    if boxes is None and isinstance(result, (tuple, list)) and result:
        legacy = result[0]
        if isinstance(legacy, (tuple, list)):
            boxes = [row[0] for row in legacy if len(row) >= 3]
            texts = [row[1] for row in legacy if len(row) >= 3]
            scores = [row[2] for row in legacy if len(row) >= 3]
    def as_list(value):
        if value is None:
            return []
        return value.tolist() if hasattr(value, "tolist") else list(value)
    return as_list(boxes), as_list(texts), as_list(scores)


def diagnose(ep: Path, *, engine=None, keys=None) -> dict:
    ep = Path(ep).resolve()
    if not ep.is_dir():
        raise ValueError(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("episode directory must be inside the StoryOS repository") from exc
    layout_path = ep / LAYOUT_REPORT_REL
    if not layout_path.is_file():
        raise ValueError(f"subtitle layout audit missing: {layout_path}")
    report = json.loads(layout_path.read_text(encoding="utf-8"))
    if report.get("engine") != LAYOUT_ENGINE or report.get("canonical_renderer") is not True:
        raise ValueError("subtitle layout audit is not canonical")

    started = time.perf_counter()
    if engine is None:
        from rapidocr import RapidOCR
        engine = RapidOCR()
    frames = report.get("frames") or {}
    if keys is not None:
        keys = {str(key).zfill(2) for key in keys}
        frames = {key: value for key, value in frames.items() if key in keys}
    rows = {}
    errors = []
    for key, layout in sorted(frames.items()):
        frame_started = time.perf_counter()
        if not isinstance(layout, dict):
            elapsed = round(time.perf_counter() - frame_started, 4)
            errors.append(f"{key}: invalid layout row")
            rows[key] = {"status": "ERROR", "error": "invalid layout row",
                         "elapsed_seconds": elapsed, "overlaps": []}
            continue
        subtitle_box = _subtitle_rect(layout)
        if subtitle_box is None:
            rows[key] = {"status": "NO_SUBTITLE", "detected_text_count": 0,
                         "elapsed_seconds": round(time.perf_counter() - frame_started, 4),
                         "overlaps": []}
            continue
        try:
            image = _resolve_repo_file(layout.get("base_path"))
            expected_sha = str(layout.get("base_sha256") or "").lower()
            actual_sha = _sha(image)
            if len(expected_sha) != 64 or actual_sha != expected_sha:
                raise ValueError("base image SHA mismatch")
            # Decode by bytes so RapidOCR works with non-ASCII Windows paths.
            import cv2
            import numpy as np
            pixels = cv2.imdecode(np.fromfile(str(image), dtype=np.uint8), cv2.IMREAD_COLOR)
            if pixels is None:
                raise ValueError("OpenCV could not decode the base image")
            result = engine(pixels)
            boxes, recognized, scores = _texts(result)
            overlaps = []
            detection_count = min(len(boxes), max(len(recognized), len(scores), len(boxes)))
            for index in range(detection_count):
                text_box = _box_to_rect(boxes[index])
                if text_box is None:
                    continue
                ratio = _intersection_ratio(text_box, subtitle_box)
                if ratio >= OVERLAP_WARNING_RATIO:
                    try:
                        confidence = float(scores[index]) if index < len(scores) else None
                    except (TypeError, ValueError):
                        confidence = None
                    overlaps.append({
                        "recognized_text": str(recognized[index])[:120] if index < len(recognized) else "",
                        "confidence": confidence,
                        "text_box_xyxy": [round(value, 2) for value in text_box],
                        "subtitle_overlap_ratio": round(ratio, 4),
                        "suggestion": "REVIEW_POSSIBLE_NATIVE_TEXT_OBSTRUCTION",
                    })
            rows[key] = {
                "status": "COMPLETE",
                "base_path": image.relative_to(ROOT).as_posix(),
                "base_sha256": actual_sha,
                "elapsed_seconds": round(time.perf_counter() - frame_started, 4),
                "subtitle_box_xyxy": [round(value, 2) for value in subtitle_box],
                "detected_text_count": len(boxes),
                "overlaps": overlaps,
            }
        except Exception as exc:
            errors.append(f"{key}: {type(exc).__name__}: {exc}")
            rows[key] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}",
                         "elapsed_seconds": round(time.perf_counter() - frame_started, 4),
                         "overlaps": []}

    try:
        version = importlib.metadata.version("rapidocr")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    complete = sum(row.get("status") == "COMPLETE" for row in rows.values())
    overlap_count = sum(len(row.get("overlaps") or []) for row in rows.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "may_affect_gate": False,
        "generated_at": _now(),
        "episode_id": ep.name,
        "tool": {"name": "RapidOCR", "version": version},
        "source": {
            "layout_report_path": layout_path.relative_to(ROOT).as_posix(),
            "layout_report_sha256": _sha(layout_path),
            "caption_source_sha256": report.get("source_sha256"),
        },
        "status": "COMPLETE" if not errors else ("PARTIAL" if complete else "FAILED"),
        "thresholds": {"warning_overlap_ratio": OVERLAP_WARNING_RATIO},
        "summary": {
            "frame_count": len(rows), "complete_frames": complete,
            "overlap_candidates": overlap_count,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "errors": errors,
        },
        "frames": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    args = parser.parse_args()
    ep = Path(args.episode_dir).resolve()
    try:
        data = diagnose(ep)
    except ImportError as exc:
        message = ("RapidOCR is not installed. Install the optional runtime with: "
                   "python -m pip install -r episodes/_system/requirements-ocr.txt")
        print(json.dumps({"status": "SKIPPED_DEPENDENCY", "diagnostic_only": True,
                          "error": message, "detail": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "diagnostic_only": True,
                          "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    target = ep / OUTPUT_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": data["status"], "report": target.relative_to(ROOT).as_posix(),
                      "summary": data["summary"]}, ensure_ascii=False, indent=2))
    return 0 if data["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
