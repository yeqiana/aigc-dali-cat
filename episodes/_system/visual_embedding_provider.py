#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional ONNX visual-embedding provider for Local Visual Triage.

The provider never downloads models. It is disabled until an operator supplies
an explicit local ONNX model. Output is advisory embedding evidence only.
"""
from __future__ import annotations

import hashlib
import math
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_ENV = "STORY_OS_DINO_ONNX_MODEL"


def _model_path(config: dict) -> Path | None:
    raw = os.environ.get(MODEL_ENV) or str(config.get("model_path") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    return path if path.is_file() else None


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@lru_cache(maxsize=2)
def _session(model_path: str):
    import onnxruntime as ort
    return ort.InferenceSession(model_path, providers=ort.get_available_providers())


def available(config: dict) -> dict:
    if config.get("enabled") is not True:
        return {"available": False, "reason": "DISABLED"}
    path = _model_path(config)
    if path is None:
        return {"available": False, "reason": "MODEL_MISSING"}
    try:
        import onnxruntime  # noqa: F401
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        return {"available": False, "reason": "DEPENDENCY_MISSING", "detail": str(exc)}
    return {"available": True, "model_path": str(path), "model_sha256": _sha(path)}


def _preprocess(path: Path, size: int):
    import numpy as np
    from PIL import Image
    resampling = getattr(Image, "Resampling", Image).BICUBIC
    with Image.open(path) as source:
        image = source.convert("RGB").resize((size, size), resampling)
        array = np.asarray(image, dtype=np.float32) / 255.0
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    array = (array - mean) / std
    return np.transpose(array, (2, 0, 1))[None, ...]


def _vector(output) -> list[float]:
    import numpy as np
    value = np.asarray(output)
    if value.ndim == 3:
        value = value[:, 0, :]
    if value.ndim > 2:
        value = value.reshape(value.shape[0], -1)
    if value.ndim == 1:
        flat = value
    elif value.ndim == 2:
        flat = value[0]
    else:
        raise ValueError(f"unsupported embedding output rank: {value.ndim}")
    flat = flat.astype(np.float32)
    norm = float(np.linalg.norm(flat))
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError("embedding norm is zero/non-finite")
    return [round(float(x / norm), 7) for x in flat.tolist()]


def embed(path: Path, config: dict) -> dict:
    info = available(config)
    if not info["available"]:
        return {"status": "SKIPPED", **info}
    model = Path(info["model_path"])
    try:
        session = _session(str(model))
        inputs = session.get_inputs()
        if len(inputs) != 1:
            raise ValueError("embedding ONNX must expose exactly one image input")
        size = int(config.get("input_size") or 224)
        tensor = _preprocess(Path(path), size)
        outputs = session.run(None, {inputs[0].name: tensor})
        if not outputs:
            raise ValueError("embedding ONNX returned no outputs")
        vector = _vector(outputs[0])
        return {
            "status": "COMPLETE",
            "provider": "onnx",
            "model_path": str(model),
            "model_sha256": info["model_sha256"],
            "dimension": len(vector),
            "vector": vector,
        }
    except Exception as exc:
        return {"status": "FAILED", "provider": "onnx", "reason": f"{type(exc).__name__}: {exc}"}


def cosine(left: list[float], right: list[float]) -> float | None:
    if not left or len(left) != len(right):
        return None
    value = sum(float(a) * float(b) for a, b in zip(left, right))
    return round(value, 7)
