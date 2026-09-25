#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional local-only Grounding DINO object-presence diagnostic.

The provider never downloads models. It consumes explicit object/prop references
from a queue item or its Resolved Frame Contract and returns advisory evidence.
"""
from __future__ import annotations

import hashlib
import sys
from functools import lru_cache
from pathlib import Path

import story_json
import isolated_ml_runtime
import visual_fingerprint

ROOT = Path(__file__).resolve().parents[2]


def _resolve_repo_file(raw: object) -> Path | None:
    if not raw:
        return None
    path = Path(str(raw))
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def _model_dir(config: dict) -> Path | None:
    raw = str(config.get("model_path") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    return path if path.is_dir() else None


def _manifest_sha(path: Path) -> str:
    h = hashlib.sha256()
    for child in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_file():
            continue
        stat = child.stat()
        h.update(child.name.encode("utf-8"))
        h.update(str(stat.st_size).encode("ascii"))
        if child.name in {"config.json", "preprocessor_config.json", "processor_config.json"}:
            h.update(child.read_bytes())
    return h.hexdigest()


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
    return {"available": True, "model_path": str(model), "model_manifest_sha256": _manifest_sha(model)}


def _frame_contract_data(ep: Path, item: dict) -> dict:
    row = item.get("frame_contract") if isinstance(item.get("frame_contract"), dict) else {}
    path = _resolve_repo_file(row.get("path"))
    if path is None:
        # Runtime contract caches are derived evidence; absence is a clean skip.
        fallback = Path(ep).resolve() / "meta/runtime/contracts/frames" / f"{int(item.get('frame') or 0):02d}.json"
        path = fallback if fallback.is_file() else None
    if path is None:
        return {}
    data = story_json.read_json(path, default={})
    return data if isinstance(data, dict) else {}


def _query_text(row: dict) -> str | None:
    for key in ("object", "label", "name", "display_name", "role", "description"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:160]
    return None


def object_queries(ep: Path, item: dict, config: dict) -> list[str]:
    explicit = item.get("object_queries")
    values: list[str] = []
    if isinstance(explicit, list):
        values.extend(str(x).strip() for x in explicit if str(x).strip())
    contract = _frame_contract_data(Path(ep), item)
    material = contract.get("hash_material") if isinstance(contract.get("hash_material"), dict) else contract
    stack = [material]
    allowed_kinds = {"prop", "object", "vehicle", "device", "screen", "animal", "key_prop"}
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            kind = str(current.get("kind") or current.get("reference_kind") or "").strip().lower()
            if kind in allowed_kinds:
                text = _query_text(current)
                if text:
                    values.append(text)
            for key, value in current.items():
                if key in {"prompt_contract", "story_text", "caption"}:
                    continue
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    unique = []
    seen = set()
    limit = int(config.get("max_queries") or 8)
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
        if len(unique) >= limit:
            break
    return unique


@lru_cache(maxsize=1)
def _load(model_path: str):
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
    processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(model_path, local_files_only=True)
    model.eval()
    return processor, model


def _inspect_local(candidate: Path, queries: list[str], config: dict, info: dict) -> dict:
    try:
        import torch
        from PIL import Image
        processor, model = _load(info["model_path"])
        with Image.open(candidate) as raw:
            image = raw.convert("RGB")
            target_size = [(image.height, image.width)]
            text_labels = [queries]
            inputs = processor(images=image, text=text_labels, return_tensors="pt")
        with torch.inference_mode():
            outputs = model(**inputs)
        rows = processor.post_process_grounded_object_detection(
            outputs,
            inputs["input_ids"],
            threshold=float(config.get("box_threshold") or 0.35),
            text_threshold=float(config.get("text_threshold") or 0.25),
            target_sizes=target_size,
        )
        first = rows[0] if rows else {}
        boxes = first.get("boxes")
        scores = first.get("scores")
        labels = first.get("text_labels") or first.get("labels") or []
        boxes = boxes.tolist() if hasattr(boxes, "tolist") else list(boxes or [])
        scores = scores.tolist() if hasattr(scores, "tolist") else list(scores or [])
        detections = []
        for index, box in enumerate(boxes):
            detections.append({
                "label": str(labels[index]) if index < len(labels) else "",
                "score": round(float(scores[index]), 6) if index < len(scores) else None,
                "box_xyxy": [round(float(x), 2) for x in box],
            })
        detected_text = " ".join(str(row["label"]).casefold() for row in detections)
        missing = [query for query in queries if query.casefold() not in detected_text]
        issues = ["OBJECT_QUERY_NO_DETECTION"] if missing and config.get("flag_missing_queries") is True else []
        return {
            "status": "SUSPECT" if issues else "COMPLETE",
            "diagnostic_only": True,
            "may_affect_gate": False,
            "candidate_sha256": visual_fingerprint.sha256_file(Path(candidate)),
            "model_manifest_sha256": info["model_manifest_sha256"],
            "queries": queries,
            "detections": detections,
            "missing_queries": missing,
            "issues": issues,
        }
    except Exception as exc:
        return {
            "status": "FAILED", "diagnostic_only": True, "may_affect_gate": False,
            "queries": queries, "reason": f"{type(exc).__name__}: {exc}",
        }


def inspect(ep: Path, item: dict, candidate: Path, config: dict) -> dict:
    if config.get("enabled") is not True:
        return {"status": "SKIPPED", "diagnostic_only": True, "reason": "DISABLED", "queries": []}
    queries = object_queries(Path(ep), item, config)
    if not queries:
        return {"status": "SKIPPED", "diagnostic_only": True, "reason": "NO_OBJECT_QUERIES", "queries": []}
    info = available(config)
    if not info["available"]:
        return {"status": "SKIPPED", "diagnostic_only": True, "queries": queries, **info}
    return isolated_ml_runtime.call(
        Path(__file__),
        {
            "candidate": str(Path(candidate).resolve()),
            "queries": queries,
            "config": config,
            "info": info,
        },
        timeout=int(config.get("timeout_seconds") or 180),
    )


def _isolated_handler(payload: dict) -> dict:
    return _inspect_local(
        Path(payload["candidate"]),
        [str(x) for x in payload.get("queries") or []],
        payload.get("config") or {},
        payload.get("info") or {},
    )


if __name__ == "__main__" and "--isolated-server" in sys.argv:
    isolated_ml_runtime.serve(_isolated_handler)
