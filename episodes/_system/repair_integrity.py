#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local repair before/after integrity evidence.

Phase A is advisory only.  It catches exact/no-op repairs and records global
pixel drift.  Region-aware SAM2/SSIM/LPIPS enforcement is a later phase.
"""
from __future__ import annotations

from pathlib import Path

import production_ledger
import visual_fingerprint

ROOT = Path(__file__).resolve().parents[2]


def _resolve(raw: object) -> Path | None:
    if not raw:
        return None
    path = Path(str(raw))
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    return path if path.is_file() else None


def source_candidate(ep: Path, frame: int) -> dict | None:
    data = production_ledger.load_authority(Path(ep).resolve(), default={}) or {}
    row = (data.get("frames") or {}).get(f"{int(frame):02d}") or {}
    candidate = row.get("current_candidate")
    return candidate if isinstance(candidate, dict) and candidate.get("path") else None


def _block_ssim(left, right, *, size: int = 256, block: int = 8) -> float:
    """Dependency-light block SSIM on downscaled grayscale pixels."""
    import numpy as np
    from PIL import Image
    resampling = getattr(Image, "Resampling", Image).BILINEAR
    a = np.asarray(left.convert("L").resize((size, size), resampling), dtype=np.float32)
    b = np.asarray(right.convert("L").resize((size, size), resampling), dtype=np.float32)
    usable = (size // block) * block
    a = a[:usable, :usable].reshape(usable // block, block, usable // block, block)
    b = b[:usable, :usable].reshape(usable // block, block, usable // block, block)
    axes = (1, 3)
    mu_a, mu_b = a.mean(axis=axes), b.mean(axis=axes)
    var_a, var_b = a.var(axis=axes), b.var(axis=axes)
    cov = ((a - mu_a[:, None, :, None]) * (b - mu_b[:, None, :, None])).mean(axis=axes)
    c1, c2 = (0.01 * 255.0) ** 2, (0.03 * 255.0) ** 2
    score = ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / (
        (mu_a * mu_a + mu_b * mu_b + c1) * (var_a + var_b + c2)
    )
    return round(float(score.mean()), 6)


def inspect(ep: Path, item: dict, candidate_path: Path, candidate_fp: dict, config: dict) -> dict:
    if str(item.get("kind") or "") != "repair":
        return {"status": "NOT_APPLICABLE", "advisory_only": True}

    source = source_candidate(Path(ep), int(item["frame"]))
    if not source:
        return {"status": "UNKNOWN", "advisory_only": True, "reason": "SOURCE_CANDIDATE_MISSING"}

    source_path = _resolve(source.get("path"))
    if source_path is None:
        return {"status": "UNKNOWN", "advisory_only": True, "reason": "SOURCE_IMAGE_MISSING"}

    try:
        from PIL import Image, ImageChops, ImageStat
        source_fp = visual_fingerprint.fingerprint(source_path)
        comparison = visual_fingerprint.compare(source_fp, candidate_fp)
        with Image.open(source_path) as before, Image.open(candidate_path) as after:
            left = before.convert("RGB")
            right = after.convert("RGB")
            if left.size != right.size:
                return {
                    "status": "SUSPECT",
                    "advisory_only": True,
                    "reason": "REPAIR_CANVAS_CHANGED",
                    "source": source,
                    "comparison": comparison,
                }
            diff = ImageChops.difference(left, right)
            ssim = _block_ssim(left, right)
            bbox = diff.getbbox()
            stat = ImageStat.Stat(diff)
            rms = sum(float(x) for x in stat.rms) / max(1.0, 3.0 * 255.0)
            bbox_ratio = 0.0
            if bbox:
                bbox_ratio = ((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])) / float(left.width * left.height)
    except Exception as exc:
        return {
            "status": "UNKNOWN",
            "advisory_only": True,
            "reason": f"{type(exc).__name__}: {exc}",
            "source": source,
        }

    issues = []
    noop_rms_max = float(config.get("repair_noop_rms_max", 0.002))
    if comparison["same_sha256"]:
        issues.append("REPAIR_EXACT_NOOP")
    elif comparison["dhash_distance"] == 0 and rms <= noop_rms_max:
        issues.append("REPAIR_NEAR_NOOP")
    ssim_warn_below = float(config.get("repair_ssim_warn_below", 0.55))
    if ssim < ssim_warn_below:
        issues.append("REPAIR_GLOBAL_SSIM_LOW")

    return {
        "status": "SUSPECT" if issues else "PASS",
        "advisory_only": True,
        "issues": issues,
        "source": {
            "path": source.get("path"),
            "sha256": source_fp["sha256"],
            "attempt_id": source.get("attempt_id"),
        },
        "comparison": comparison,
        "pixel_delta": {
            "changed_bbox": list(bbox) if bbox else None,
            "changed_bbox_area_ratio": round(bbox_ratio, 6),
            "rms_normalized": round(rms, 6),
            "block_ssim": ssim,
        },
        "mask_policy": "NOT_AVAILABLE_PHASE_A",
    }
