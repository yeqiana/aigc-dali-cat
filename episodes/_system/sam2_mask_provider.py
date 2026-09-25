#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional local-only SAM2 repair-region mask diagnostic."""
from __future__ import annotations

import sys

from functools import lru_cache
from pathlib import Path

import isolated_ml_runtime

import visual_fingerprint

ROOT = Path(__file__).resolve().parents[2]


def _model_dir(config: dict) -> Path | None:
    raw = str(config.get("model_path") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    return path if path.is_dir() else None


def available(config: dict) -> dict:
    if config.get("enabled") is not True:
        return {"available": False, "reason": "DISABLED"}
    model = _model_dir(config)
    if model is None:
        return {"available": False, "reason": "MODEL_MISSING"}
    dependencies = isolated_ml_runtime.dependency_status(("torch", "transformers"))
    missing = [name for name in ("torch", "transformers") if dependencies.get(name) is not True]
    if missing:
        return {"available": False, "reason": "DEPENDENCY_MISSING", "detail": ",".join(missing)}
    return {"available": True, "model_path": str(model)}


@lru_cache(maxsize=1)
def _load(model_path: str):
    from transformers import Sam2Model, Sam2Processor
    processor = Sam2Processor.from_pretrained(model_path, local_files_only=True)
    model = Sam2Model.from_pretrained(model_path, local_files_only=True)
    model.eval()
    return processor, model


def _segment_local(candidate: Path, box_xyxy, config: dict, info: dict) -> dict:
    try:
        import numpy as np
        import torch
        from PIL import Image
        processor, model = _load(info["model_path"])
        with Image.open(candidate) as raw:
            image = raw.convert("RGB")
            width, height = image.size
            box = [max(0.0, float(v)) for v in box_xyxy]
            box[2] = min(float(width), box[2])
            box[3] = min(float(height), box[3])
            inputs = processor(images=image, input_boxes=[[box]], return_tensors="pt")
        with torch.inference_mode():
            outputs = model(**inputs, multimask_output=False)
        masks = processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"])
        mask = masks[0]
        if hasattr(mask, "detach"):
            mask = mask.detach().cpu().numpy()
        array = np.asarray(mask)
        while array.ndim > 2:
            array = array[0]
        binary = array > 0
        area_ratio = float(binary.mean()) if binary.size else 0.0
        broad = area_ratio > float(config.get("broad_mask_warn_above") or 0.65)
        issues = ["REPAIR_MASK_TOO_BROAD"] if broad else []
        return {
            "status": "SUSPECT" if issues else "COMPLETE",
            "diagnostic_only": True,
            "may_affect_gate": False,
            "candidate_sha256": visual_fingerprint.sha256_file(Path(candidate)),
            "prompt_box_xyxy": [round(float(x), 2) for x in box],
            "mask_area_ratio": round(area_ratio, 6),
            "issues": issues,
        }
    except Exception as exc:
        return {"status": "FAILED", "diagnostic_only": True, "reason": f"{type(exc).__name__}: {exc}"}


def segment_change_region(candidate: Path, box_xyxy: list[int] | tuple[int, int, int, int] | None, config: dict) -> dict:
    if not box_xyxy:
        return {"status": "SKIPPED", "diagnostic_only": True, "reason": "NO_CHANGE_BOX"}
    info = available(config)
    if not info["available"]:
        return {"status": "SKIPPED", "diagnostic_only": True, **info}
    return isolated_ml_runtime.call(
        Path(__file__),
        {"candidate": str(Path(candidate).resolve()), "box_xyxy": list(box_xyxy), "config": config, "info": info},
        timeout=int(config.get("timeout_seconds") or 180),
    )


def _isolated_handler(payload: dict) -> dict:
    return _segment_local(
        Path(payload["candidate"]),
        payload.get("box_xyxy"),
        payload.get("config") or {},
        payload.get("info") or {},
    )


if __name__ == "__main__" and "--isolated-server" in sys.argv:
    isolated_ml_runtime.serve(_isolated_handler)
