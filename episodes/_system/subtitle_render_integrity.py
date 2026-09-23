#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local pixel proof that canonical subtitle rendering changed only its text area."""
from __future__ import annotations

from pathlib import Path


def inspect(layout: dict) -> dict:
    """Return PASS/FAIL/UNKNOWN. Only definite corruption is FAIL."""
    try:
        from PIL import Image, ImageChops
        import caption_ocr_diagnostic as ocr

        base = ocr._resolve_repo_file(layout.get("base_path"))
        output = ocr._resolve_repo_file(layout.get("output_path"))
        if (ocr._sha(base) != str(layout.get("base_sha256") or "").lower()
                or ocr._sha(output) != str(layout.get("output_sha256") or "").lower()):
            return {"status": "UNKNOWN", "reason": "SOURCE_SHA_DRIFT"}
        with Image.open(base) as original, Image.open(output) as published:
            if original.size != published.size:
                return {"status": "FAIL", "reason": "CANVAS_CHANGED"}
            if original.mode != "RGB" or published.mode != "RGB":
                return {"status": "UNKNOWN", "reason": "COLOR_MODE_UNSUPPORTED"}
            diff_box = ImageChops.difference(original, published).getbbox()
            rect = ocr._subtitle_rect(layout)
            if rect is None:
                return {"status": "UNKNOWN", "reason": "NO_SUBTITLE"}
            if diff_box is None:
                return {"status": "FAIL", "reason": "SUBTITLE_NOT_RENDERED"}
            # The canonical shadow is shifted by (1,2) and Gaussian-blurred.
            # A 20px margin contains both shadow and antialiasing.
            expected = (max(0, int(rect[0]) - 20), max(0, int(rect[1]) - 20),
                        min(original.width, int(rect[2]) + 20),
                        min(original.height, int(rect[3]) + 20))
            if not (expected[0] <= diff_box[0] and expected[1] <= diff_box[1]
                    and diff_box[2] <= expected[2] and diff_box[3] <= expected[3]):
                return {"status": "FAIL", "reason": "PIXELS_CHANGED_OUTSIDE_SUBTITLE",
                        "changed_box": list(diff_box), "expected_box": list(expected)}
            return {"status": "PASS", "changed_box": list(diff_box),
                    "base_sha256": layout["base_sha256"],
                    "output_sha256": layout["output_sha256"]}
    except Exception as exc:
        return {"status": "UNKNOWN", "reason": f"{type(exc).__name__}: {exc}"}


def inspect_frames(ep: Path, keys: list[str]) -> dict[str, dict]:
    """Inspect current canonical layout rows without changing Episode evidence."""
    try:
        import json
        import caption_ocr_diagnostic as ocr
        ep = Path(ep).resolve()
        report = json.loads((ep / ocr.LAYOUT_REPORT_REL).read_text(encoding="utf-8"))
        if report.get("engine") != ocr.LAYOUT_ENGINE or report.get("canonical_renderer") is not True:
            return {str(key).zfill(2): {"status": "UNKNOWN", "reason": "NONCANONICAL_LAYOUT"} for key in keys}
        layouts = report.get("frames") or {}
        return {str(key).zfill(2): inspect(layouts.get(str(key).zfill(2)) or {})
                for key in keys}
    except Exception as exc:
        return {str(key).zfill(2): {"status": "UNKNOWN", "reason": f"{type(exc).__name__}: {exc}"}
                for key in keys}
