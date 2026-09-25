#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional LPIPS repair similarity diagnostic. Never installs/downloads models."""
from __future__ import annotations

import sys

from functools import lru_cache
from pathlib import Path

import isolated_ml_runtime

import visual_fingerprint


def available(config: dict) -> dict:
    if config.get("enabled") is not True:
        return {"available": False, "reason": "DISABLED"}
    dependencies = isolated_ml_runtime.dependency_status(("torch", "lpips"))
    missing = [name for name in ("torch", "lpips") if dependencies.get(name) is not True]
    if missing:
        return {"available": False, "reason": "DEPENDENCY_MISSING", "detail": ",".join(missing)}
    return {"available": True}


@lru_cache(maxsize=2)
def _model(net: str):
    import lpips
    model = lpips.LPIPS(net=net, verbose=False)
    model.eval()
    return model


def _tensor(path: Path, size: int):
    import numpy as np
    import torch
    from PIL import Image
    resampling = getattr(Image, "Resampling", Image).BILINEAR
    with Image.open(path) as raw:
        image = raw.convert("RGB")
        image.thumbnail((size, size), resampling)
        array = np.asarray(image, dtype=np.float32) / 127.5 - 1.0
    return torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)


def _compare_local(source: Path, candidate: Path, config: dict) -> dict:
    try:
        import torch
        net = str(config.get("net") or "alex")
        size = int(config.get("max_side") or 512)
        left, right = _tensor(Path(source), size), _tensor(Path(candidate), size)
        if left.shape != right.shape:
            return {"status": "UNKNOWN", "diagnostic_only": True, "reason": "RESIZED_SHAPE_MISMATCH"}
        with torch.inference_mode():
            score = float(_model(net)(left, right).reshape(-1)[0].item())
        warn = score > float(config.get("warn_above") or 0.45)
        issues = ["REPAIR_LPIPS_HIGH"] if warn else []
        return {
            "status": "SUSPECT" if issues else "COMPLETE",
            "diagnostic_only": True,
            "may_affect_gate": False,
            "source_sha256": visual_fingerprint.sha256_file(Path(source)),
            "candidate_sha256": visual_fingerprint.sha256_file(Path(candidate)),
            "net": net,
            "lpips": round(score, 6),
            "issues": issues,
        }
    except Exception as exc:
        return {"status": "FAILED", "diagnostic_only": True, "reason": f"{type(exc).__name__}: {exc}"}


def compare(source: Path, candidate: Path, config: dict) -> dict:
    info = available(config)
    if not info["available"]:
        return {"status": "SKIPPED", "diagnostic_only": True, **info}
    return isolated_ml_runtime.call(
        Path(__file__),
        {"source": str(Path(source).resolve()), "candidate": str(Path(candidate).resolve()), "config": config},
        timeout=int(config.get("timeout_seconds") or 180),
    )


def _isolated_handler(payload: dict) -> dict:
    return _compare_local(
        Path(payload["source"]),
        Path(payload["candidate"]),
        payload.get("config") or {},
    )


if __name__ == "__main__" and "--isolated-server" in sys.argv:
    isolated_ml_runtime.serve(_isolated_handler)
