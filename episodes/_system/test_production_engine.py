#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from canvas_spec import DEFAULT_ASPECT_RATIO, resolve_canvas_spec
from production_ledger import LEDGER_FILE, init_ledger, image_dimensions


def write_png(path: Path, width: int, height: int) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 1))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


class CanvasTests(unittest.TestCase):
    def test_default_canvas_is_4_5(self):
        self.assertEqual(DEFAULT_ASPECT_RATIO, "4:5")
        spec = resolve_canvas_spec(None)
        self.assertEqual((spec.width, spec.height), (1080, 1350))

    def test_9_16_supported(self):
        spec = resolve_canvas_spec("9:16")
        self.assertEqual((spec.width, spec.height), (1080, 1920))


class LedgerTests(unittest.TestCase):
    def make_episode(self, root: Path, ratio: str | None = None) -> Path:
        ep = root / "episodes" / "10_test" / "01_demo"
        (ep / "meta").mkdir(parents=True)
        manifest = {
            "episode": {"id": "10-01", "series": "10_test", "title": "demo"},
            "release": {"body_frame_count": 3},
        }
        if ratio:
            manifest["episode"]["aspect_ratio"] = ratio
        (ep / "meta" / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return ep

    def test_manifest_omitted_ratio_defaults_4_5(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self.make_episode(Path(td))
            data = init_ledger(ep)
            self.assertEqual(data["canvas"]["aspect_ratio"], "4:5")
            self.assertEqual((data["canvas"]["width"], data["canvas"]["height"]), (1080, 1350))
            self.assertTrue((ep / LEDGER_FILE).exists())
            self.assertEqual(len(data["frames"]), 3)

    def test_manifest_9_16_is_respected(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self.make_episode(Path(td), "9:16")
            data = init_ledger(ep)
            self.assertEqual((data["canvas"]["width"], data["canvas"]["height"]), (1080, 1920))

    def test_png_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.png"
            write_png(p, 1080, 1350)
            self.assertEqual(image_dimensions(p), (1080, 1350))


if __name__ == "__main__":
    unittest.main()
