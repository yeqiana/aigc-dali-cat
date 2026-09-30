from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from subtitle_layout import normalize_publish_canvas


def test_noncanonical_accepted_publish_image_is_padded_without_cropping(tmp_path):
    source = tmp_path / "accepted.png"
    Image.new("RGB", (1092, 1440), (80, 120, 160)).save(source)

    canvas, audit = normalize_publish_canvas(source, (1080, 1350))

    assert canvas.size == (1080, 1350)
    assert audit["operation"] == "RESIZE_LANCZOS_PAD_NO_CROP"
    assert audit["crop_applied"] is False
    assert audit["source_size"] == [1092, 1440]
    assert audit["target_size"] == [1080, 1350]
    assert source.exists()


def test_canonical_publish_image_is_not_resized(tmp_path):
    source = tmp_path / "accepted.png"
    Image.new("RGB", (1080, 1350), (80, 120, 160)).save(source)

    canvas, audit = normalize_publish_canvas(source, (1080, 1350))

    assert canvas.size == (1080, 1350)
    assert audit["operation"] == "NOOP"
    assert audit["crop_applied"] is False
