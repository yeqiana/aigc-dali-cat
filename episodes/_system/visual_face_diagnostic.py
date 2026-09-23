#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional YuNet face-box shadow diagnostic for a Visual Lock baseline.

The result is derived evidence only. It does not assign characters, create face
crops, modify baseline review, or affect any gate or episode state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path

import visual_lock_baseline_gate
import character_visual_contract

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_REL = Path("meta/runtime/diagnostics/visual-face-shadow.json")
SCHEMA_VERSION = 1


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_image(cv2, path: Path):
    # cv2.imread can fail on non-ASCII Windows paths; decode bytes explicitly.
    import numpy as np
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def _iou(left: list[float], right: list[float]) -> float:
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    x1, y1 = max(lx, rx), max(ly, ry)
    x2, y2 = min(lx + lw, rx + rw), min(ly + lh, ry + rh)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = lw * lh + rw * rh - intersection
    return intersection / union if union else 0.0


def diagnose(ep: Path, model_path: Path, *, score_threshold: float = 0.6) -> dict:
    import cv2

    ep = Path(ep).resolve()
    model_path = Path(model_path).resolve()
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("episode directory must be inside the StoryOS repository") from exc
    if not ep.is_dir():
        raise ValueError(f"episode directory not found: {ep}")
    if not model_path.is_file():
        raise ValueError(f"YuNet model file not found: {model_path}")
    if not 0.0 < score_threshold < 1.0:
        raise ValueError("score_threshold must be between 0 and 1")

    try:
        baseline = visual_lock_baseline_gate.generated_baseline(ep)
    except ValueError:
        # Existing locked human-reviewed Visual Lock evidence remains a valid
        # comparison source when its historical queue row is no longer present.
        review = visual_lock_baseline_gate.read_json(ep / visual_lock_baseline_gate.REL)
        if review.get("status") != "LOCKED" or review.get("decision") != "PASS":
            raise
        asset = visual_lock_baseline_gate.repo_file(review.get("asset_path"))
        if _sha(asset) != str(review.get("sha256") or "").lower():
            raise ValueError("locked Visual Lock review source SHA is stale")
        baseline = {"frame": int(review["frame"]), "asset_path": visual_lock_baseline_gate.repo_rel(asset),
                    "sha256": _sha(asset), "frame_contract_sha256": review.get("frame_contract_sha256")}
    review_path = ep / visual_lock_baseline_gate.REL
    if review_path.is_file():
        review = visual_lock_baseline_gate.read_json(review_path)
        if (review.get("status") == "LOCKED" and review.get("decision") == "PASS"
                and str(review.get("sha256") or "").lower() == baseline["sha256"]):
            human_boxes = [row for row in (review.get("face_boxes") or [])
                           if all(isinstance(row.get(key), (int, float)) for key in ("x", "y", "w", "h"))]
        else:
            human_boxes = []
    else:
        human_boxes = []
    image_path = (ROOT / baseline["asset_path"]).resolve()
    image_path.relative_to(ROOT.resolve())
    if not image_path.is_file() or _sha(image_path) != baseline["sha256"]:
        raise ValueError("Visual Lock baseline image is missing or its SHA changed")

    started = time.perf_counter()
    image = _read_image(cv2, image_path)
    if image is None:
        raise ValueError("OpenCV could not decode the Visual Lock baseline image")
    height, width = image.shape[:2]
    if hasattr(cv2, "FaceDetectorYN"):
        detector = cv2.FaceDetectorYN.create(str(model_path), "", (width, height), score_threshold, 0.3, 5000)
    elif hasattr(cv2, "FaceDetectorYN_create"):
        detector = cv2.FaceDetectorYN_create(str(model_path), "", (width, height), score_threshold, 0.3, 5000)
    else:
        raise RuntimeError("installed OpenCV does not expose FaceDetectorYN")
    _retval, faces = detector.detect(image)
    face_rows = []
    for row in faces if faces is not None else []:
        x, y, box_w, box_h = [float(value) for value in row[:4]]
        confidence = float(row[-1])
        face_rows.append({
            "box_xywh": [round(x, 2), round(y, 2), round(box_w, 2), round(box_h, 2)],
            "box_normalized_xywh": [round(x / width, 6), round(y / height, 6),
                                    round(box_w / width, 6), round(box_h / height, 6)],
            "area_ratio": round((box_w * box_h) / (width * height), 6),
            "confidence": round(confidence, 6),
            "character_id": None,
            "suggestion": "CANDIDATE_FACE_BOX_REQUIRES_VISUAL_CONFIRMATION",
        })
    primary_ids = [str(row.get("character_id")) for row in human_boxes if row.get("character_id")]
    if not primary_ids:
        primary_ids = [str(value) for value in ((character_visual_contract.load(ep) or {}).get("primary_cast_ids") or [])]
    expected_count = len(human_boxes) if human_boxes else len(primary_ids)
    pairwise_iou = []
    for face_index, detected in enumerate(face_rows):
        for human in human_boxes:
            human_box = [float(human[key]) for key in ("x", "y", "w", "h")]
            pairwise_iou.append({"detected_face_index": face_index,
                                 "human_character_id": human.get("character_id"),
                                 "iou": round(_iou(detected["box_normalized_xywh"], human_box), 6)})
    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "may_affect_gate": False,
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "episode_id": ep.name,
        "tool": {"name": "OpenCV YuNet", "opencv_version": cv2.__version__,
                 "model_filename": model_path.name, "model_sha256": _sha(model_path)},
        "source": {"frame": int(baseline["frame"]), "image_path": baseline["asset_path"],
                   "image_sha256": baseline["sha256"],
                   "frame_contract_sha256": baseline["frame_contract_sha256"]},
        "human_review_face_boxes": human_boxes,
        "human_box_iou_comparisons": pairwise_iou,
        "policy": {"score_threshold": score_threshold, "character_assignment": "NOT_PERFORMED",
                   "face_crop_creation": "NOT_PERFORMED"},
        "summary": {
            "image_width": width, "image_height": height,
            "primary_character_ids": primary_ids,
            "expected_primary_count": expected_count,
            "detected_face_count": len(face_rows),
            "count_matches_primary_count": len(face_rows) == expected_count,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "note": "Count comparison is a diagnostic hint; it does not prove identity or visibility suitability.",
        },
        "faces": face_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    parser.add_argument("--model", required=True, help="Path to the locally downloaded YuNet ONNX model")
    parser.add_argument("--score-threshold", type=float, default=0.6)
    args = parser.parse_args()
    ep = Path(args.episode_dir).resolve()
    try:
        data = diagnose(ep, Path(args.model), score_threshold=args.score_threshold)
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "diagnostic_only": True,
                          "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    target = ep / OUTPUT_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "report": target.relative_to(ROOT).as_posix(),
                      "summary": data["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
