#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only benchmark for cheap Local Visual Triage pixel primitives."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import image_technical_gate

ROOT = Path(__file__).resolve().parents[2]


def run(image: Path, *, iterations: int = 5, expected_size=None) -> dict:
    image = Path(image).resolve()
    if not image.is_file():
        raise ValueError(f"image missing: {image}")
    samples = []
    last = None
    for _ in range(max(1, int(iterations))):
        started = time.perf_counter()
        last = image_technical_gate.inspect(image, expected_size=expected_size, config={})
        samples.append(time.perf_counter() - started)
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, max(0, int(round(0.95 * len(ordered) + 0.5)) - 1))
    fp = (last or {}).get("fingerprint") or {}
    return {
        "schema_version": 1,
        "read_only": True,
        "image": str(image),
        "iterations": len(samples),
        "status": (last or {}).get("status"),
        "image_size": [fp.get("width"), fp.get("height")],
        "seconds": {
            "min": round(min(samples), 6),
            "median": round(statistics.median(samples), 6),
            "mean": round(statistics.fmean(samples), 6),
            "p95": round(ordered[p95_index], 6),
            "max": round(max(samples), 6),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    args = parser.parse_args()
    expected = (args.width, args.height) if args.width and args.height else None
    report = run(Path(args.image), iterations=args.iterations, expected_size=expected)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
