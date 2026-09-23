from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_ocr_diagnostic
import subtitle_render_integrity


def test_local_render_integrity_detects_only_definite_pixel_errors():
    base_dir = ROOT / "episodes/_tests"
    base_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="render-integrity-", dir=base_dir) as raw:
        ep = Path(raw)
        original = ep / "base.png"
        output = ep / "publish.png"
        Image.new("RGB", (100, 80), "white").save(original)
        rendered = Image.open(original).copy()
        ImageDraw.Draw(rendered).rectangle((25, 25, 35, 32), fill="black")
        rendered.save(output)
        layout = {"base_path": str(original), "output_path": str(output),
                  "base_sha256": caption_ocr_diagnostic._sha(original),
                  "output_sha256": caption_ocr_diagnostic._sha(output)}
        with patch.object(caption_ocr_diagnostic, "_subtitle_rect", return_value=(20, 20, 40, 40)):
            assert subtitle_render_integrity.inspect(layout)["status"] == "PASS"
            rendered.putpixel((90, 70), (0, 0, 0))
            rendered.save(output)
            layout["output_sha256"] = caption_ocr_diagnostic._sha(output)
            result = subtitle_render_integrity.inspect(layout)
            assert result["status"] == "FAIL"
            assert result["reason"] == "PIXELS_CHANGED_OUTSIDE_SUBTITLE"
            layout["output_sha256"] = "0" * 64
            assert subtitle_render_integrity.inspect(layout)["status"] == "UNKNOWN"
