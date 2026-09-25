#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cheap deterministic visual fingerprints for Local Visual Triage.

This module deliberately avoids heavyweight ML dependencies.  The fingerprints
are derived diagnostics only; they never grant StoryOS production PASS.
"""
from __future__ import annotations

import hashlib
import math
import statistics
from pathlib import Path

ALGORITHM = "storyos-basic-visual-fingerprint-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _hex_from_bits(bits: list[bool]) -> str:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
    width = max(1, (len(bits) + 3) // 4)
    return f"{value:0{width}x}"


def hamming_hex(left: str, right: str) -> int:
    if not left or not right or len(left) != len(right):
        raise ValueError("hashes must be non-empty and have equal length")
    return (int(left, 16) ^ int(right, 16)).bit_count()


def _resample():
    from PIL import Image
    return getattr(Image, "Resampling", Image).LANCZOS


def average_hash(image) -> str:
    gray = image.convert("L").resize((8, 8), _resample())
    values = list(gray.getdata())
    mean = sum(values) / len(values)
    return _hex_from_bits([value >= mean for value in values])


def difference_hash(image) -> str:
    gray = image.convert("L").resize((9, 8), _resample())
    values = list(gray.getdata())
    bits = []
    for y in range(8):
        row = y * 9
        for x in range(8):
            bits.append(values[row + x] > values[row + x + 1])
    return _hex_from_bits(bits)


def perceptual_hash(image) -> str:
    """Small dependency-free pHash using a 32x32 grayscale DCT."""
    gray = image.convert("L").resize((32, 32), _resample())
    pixels = list(gray.getdata())
    cos_table = [
        [math.cos((2 * x + 1) * u * math.pi / 64.0) for x in range(32)]
        for u in range(8)
    ]
    coeffs: list[float] = []
    for v in range(8):
        cy = cos_table[v]
        for u in range(8):
            cx = cos_table[u]
            total = 0.0
            for y in range(32):
                offset = y * 32
                y_weight = cy[y]
                for x in range(32):
                    total += pixels[offset + x] * cx[x] * y_weight
            coeffs.append(total)
    threshold = statistics.median(coeffs[1:]) if len(coeffs) > 1 else coeffs[0]
    return _hex_from_bits([value >= threshold for value in coeffs])


def fingerprint(path: Path) -> dict:
    from PIL import Image, ImageFilter, ImageStat

    path = Path(path).resolve()
    with Image.open(path) as source:
        image = source.convert("RGB")
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        edge = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edge)
        return {
            "algorithm": ALGORITHM,
            "sha256": sha256_file(path),
            "width": int(image.width),
            "height": int(image.height),
            "ahash": average_hash(image),
            "dhash": difference_hash(image),
            "phash": perceptual_hash(image),
            "luma_mean": round(float(stat.mean[0]), 4),
            "luma_stddev": round(float(stat.stddev[0]), 4),
            "entropy": round(float(gray.entropy()), 4),
            "edge_mean": round(float(edge_stat.mean[0]), 4),
        }


def compare(left: dict, right: dict) -> dict:
    return {
        "same_sha256": bool(left.get("sha256") and left.get("sha256") == right.get("sha256")),
        "ahash_distance": hamming_hex(str(left["ahash"]), str(right["ahash"])),
        "dhash_distance": hamming_hex(str(left["dhash"]), str(right["dhash"])),
        "phash_distance": hamming_hex(str(left["phash"]), str(right["phash"])),
        "luma_mean_delta": round(abs(float(left.get("luma_mean") or 0.0) - float(right.get("luma_mean") or 0.0)), 4),
    }


def self_test() -> None:
    assert hamming_hex("0f", "0f") == 0
    assert hamming_hex("00", "ff") == 8
    print("VISUAL FINGERPRINT SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
