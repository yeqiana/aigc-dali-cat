#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional RTMPose-style ONNX diagnostic.

Supports direct keypoint tensors or SimCC x/y outputs. This is a triage hint,
not an anatomy PASS/FAIL authority.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import visual_fingerprint

ROOT = Path(__file__).resolve().parents[2]


def _model_file(config: dict) -> Path | None:
    raw = str(config.get("model_path") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    return path if path.is_file() else None


def available(config: dict) -> dict:
    if config.get("enabled") is not True:
        return {"available": False, "reason": "DISABLED"}
    model = _model_file(config)
    if model is None:
        return {"available": False, "reason": "MODEL_MISSING"}
    try:
        import numpy  # noqa: F401
        import onnxruntime  # noqa: F401
    except ImportError as exc:
        return {"available": False, "reason": "DEPENDENCY_MISSING", "detail": str(exc)}
    return {"available": True, "model_path": str(model)}


@lru_cache(maxsize=2)
def _session(model_path: str):
    import onnxruntime as ort
    return ort.InferenceSession(model_path, providers=ort.get_available_providers())


def _preprocess(path: Path, width: int, height: int):
    import numpy as np
    from PIL import Image
    resampling = getattr(Image, "Resampling", Image).BILINEAR
    with Image.open(path) as raw:
        original = raw.convert("RGB")
        original_size = original.size
        image = original.resize((width, height), resampling)
        array = np.asarray(image, dtype=np.float32) / 255.0
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    array = (array - mean) / std
    return np.transpose(array, (2, 0, 1))[None, ...], original_size


def _decode(outputs, original_size):
    import numpy as np
    width, height = original_size
    if len(outputs) >= 2:
        simcc_x, simcc_y = np.asarray(outputs[0]), np.asarray(outputs[1])
        while simcc_x.ndim > 3:
            simcc_x = simcc_x[0]
        while simcc_y.ndim > 3:
            simcc_y = simcc_y[0]
        if simcc_x.ndim == 3:
            simcc_x = simcc_x[0]
        if simcc_y.ndim == 3:
            simcc_y = simcc_y[0]
        if simcc_x.ndim == 2 and simcc_y.ndim == 2 and simcc_x.shape[0] == simcc_y.shape[0]:
            xs = simcc_x.argmax(axis=-1)
            ys = simcc_y.argmax(axis=-1)
            sx = simcc_x.max(axis=-1)
            sy = simcc_y.max(axis=-1)
            scores = np.sqrt(np.maximum(0.0, sx * sy))
            return [
                {"x": round(float(x) / max(1, simcc_x.shape[-1] - 1) * width, 2),
                 "y": round(float(y) / max(1, simcc_y.shape[-1] - 1) * height, 2),
                 "score": round(float(score), 6)}
                for x, y, score in zip(xs, ys, scores)
            ]
    first = np.asarray(outputs[0])
    while first.ndim > 3:
        first = first[0]
    if first.ndim == 3:
        first = first[0]
    if first.ndim == 2 and first.shape[-1] >= 2:
        rows = []
        for row in first:
            x, y = float(row[0]), float(row[1])
            score = float(row[2]) if row.shape[-1] >= 3 else 1.0
            rows.append({"x": round(x, 2), "y": round(y, 2), "score": round(score, 6)})
        return rows
    raise ValueError("unsupported RTMPose ONNX output shape")


def inspect(candidate: Path, config: dict) -> dict:
    info = available(config)
    if not info["available"]:
        return {"status": "SKIPPED", "diagnostic_only": True, **info}
    try:
        session = _session(info["model_path"])
        input_meta = session.get_inputs()[0]
        width = int(config.get("input_width") or 192)
        height = int(config.get("input_height") or 256)
        tensor, original_size = _preprocess(Path(candidate), width, height)
        outputs = session.run(None, {input_meta.name: tensor})
        keypoints = _decode(outputs, original_size)
        mean_score = sum(float(row["score"]) for row in keypoints) / max(1, len(keypoints))
        low = mean_score < float(config.get("mean_confidence_warn_below") or 0.15)
        issues = ["POSE_LOW_CONFIDENCE"] if low else []
        return {
            "status": "SUSPECT" if issues else "COMPLETE",
            "diagnostic_only": True,
            "may_affect_gate": False,
            "candidate_sha256": visual_fingerprint.sha256_file(Path(candidate)),
            "keypoint_count": len(keypoints),
            "mean_confidence": round(mean_score, 6),
            "keypoints": keypoints,
            "issues": issues,
        }
    except Exception as exc:
        return {"status": "FAILED", "diagnostic_only": True, "reason": f"{type(exc).__name__}: {exc}"}
