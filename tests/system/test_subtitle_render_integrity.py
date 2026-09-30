from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes" / "_system"))

import subtitle_layout
import subtitle_render_integrity


class SubtitleRenderIntegrityTests(unittest.TestCase):
    def test_normalized_publish_canvas_is_compared_before_subtitle_delta(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as raw_tmp:
            tmp = Path(raw_tmp)
            source = tmp / "source.png"
            output = tmp / "output.png"
            Image.new("RGB", (1122, 1402), (72, 89, 101)).save(source)
            normalization = subtitle_layout.render_one(
                source, output, "字幕检查", y=702,
                font_path=Path("C:/Windows/Fonts/msyhbd.ttc"),
                target_size=(1080, 1350),
            )
            sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            layout = {
                **normalization,
                "base_path": source.relative_to(ROOT).as_posix(),
                "base_sha256": sha(source),
                "output_path": output.relative_to(ROOT).as_posix(),
                "output_sha256": sha(output),
                "x": 72,
                "y": 702,
                "line_height": 54,
                "lines": ["字幕检查"],
            }
            self.assertEqual(subtitle_render_integrity.inspect(layout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
