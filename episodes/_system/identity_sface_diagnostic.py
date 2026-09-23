#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional SFace identity-similarity shadow diagnostic for two images.

This tool compares YuNet-detected faces in explicitly selected reference and
candidate images. Scores are diagnostic hints only: no character is assigned,
no frame review is written, and no production gate is affected.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_REL = Path("meta/runtime/diagnostics/identity-sface-shadow.json")
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


def _repo_image(raw: str, label: str) -> Path:
    path = Path(raw).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} image must be inside the StoryOS repository") from exc
    if not path.is_file():
        raise ValueError(f"{label} image not found: {path}")
    return path


def _detect(cv2, model_path: Path, image):
    height, width = image.shape[:2]
    if hasattr(cv2, "FaceDetectorYN"):
        detector = cv2.FaceDetectorYN.create(str(model_path), "", (width, height), 0.6, 0.3, 5000)
    elif hasattr(cv2, "FaceDetectorYN_create"):
        detector = cv2.FaceDetectorYN_create(str(model_path), "", (width, height), 0.6, 0.3, 5000)
    else:
        raise RuntimeError("installed OpenCV does not expose FaceDetectorYN")
    _retval, faces = detector.detect(image)
    return [] if faces is None else [row for row in faces]


def _face_summary(row, image) -> dict:
    height, width = image.shape[:2]
    x, y, box_w, box_h = [float(value) for value in row[:4]]
    return {
        "box_xywh": [round(x, 2), round(y, 2), round(box_w, 2), round(box_h, 2)],
        "box_normalized_xywh": [round(x / width, 6), round(y / height, 6),
                                round(box_w / width, 6), round(box_h / height, 6)],
        "confidence": round(float(row[-1]), 6),
    }


def diagnose(episode_dir: Path, reference_image: str, candidate_images: list[str],
             yunet_model: Path, sface_model: Path) -> dict:
    import cv2

    episode_dir = Path(episode_dir).resolve()
    try:
        episode_dir.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("episode directory must be inside the StoryOS repository") from exc
    if not episode_dir.is_dir():
        raise ValueError(f"episode directory not found: {episode_dir}")
    yunet_model = Path(yunet_model).resolve()
    sface_model = Path(sface_model).resolve()
    if not yunet_model.is_file():
        raise ValueError(f"YuNet model file not found: {yunet_model}")
    if not sface_model.is_file():
        raise ValueError(f"SFace model file not found: {sface_model}")
    reference_path = _repo_image(reference_image, "reference")
    candidate_paths = [_repo_image(raw, f"candidate[{index}]")
                       for index, raw in enumerate(candidate_images)]

    started = time.perf_counter()
    reference = _read_image(cv2, reference_path)
    if reference is None:
        raise ValueError("OpenCV could not decode the reference image")
    reference_faces = _detect(cv2, yunet_model, reference)
    candidate_rows = []
    candidate_pixels = []
    for path in candidate_paths:
        pixels = _read_image(cv2, path)
        if pixels is None:
            raise ValueError(f"OpenCV could not decode candidate image: {path}")
        faces = _detect(cv2, yunet_model, pixels)
        candidate_pixels.append(pixels)
        candidate_rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": _sha(path),
                               "face_count": len(faces), "faces": [_face_summary(row, pixels) for row in faces],
                               "top_cosine_similarity": None})
    if not reference_faces or not any(row["face_count"] for row in candidate_rows):
        status = "NO_FACE_DETECTED"
        comparisons = []
    else:
        if hasattr(cv2, "FaceRecognizerSF"):
            recognizer = cv2.FaceRecognizerSF.create(str(sface_model), "")
        elif hasattr(cv2, "FaceRecognizerSF_create"):
            recognizer = cv2.FaceRecognizerSF_create(str(sface_model), "")
        else:
            raise RuntimeError("installed OpenCV does not expose FaceRecognizerSF")
        ref_features = [recognizer.feature(recognizer.alignCrop(reference, row)) for row in reference_faces]
        comparisons = []
        for ref_index, ref_feature in enumerate(ref_features):
            for candidate_index, (candidate, candidate_row) in enumerate(zip(candidate_pixels, candidate_rows)):
                raw_candidate_faces = _detect(cv2, yunet_model, candidate)
                candidate_features = [recognizer.feature(recognizer.alignCrop(candidate, row))
                                       for row in raw_candidate_faces]
                for face_index, candidate_feature in enumerate(candidate_features):
                    score = float(recognizer.match(ref_feature, candidate_feature, cv2.FaceRecognizerSF_FR_COSINE))
                    comparisons.append({"reference_face_index": ref_index,
                                        "candidate_index": candidate_index,
                                        "candidate_path": candidate_row["path"],
                                        "candidate_face_index": face_index,
                                        "cosine_similarity": round(score, 6)})
                    current = candidate_row["top_cosine_similarity"]
                    candidate_row["top_cosine_similarity"] = round(score, 6) if current is None else max(current, round(score, 6))
        comparisons.sort(key=lambda row: row["cosine_similarity"], reverse=True)
        candidate_rows.sort(key=lambda row: row["top_cosine_similarity"] if row["top_cosine_similarity"] is not None else -2,
                            reverse=True)
        status = "DIAGNOSTIC_READY"

    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "may_affect_gate": False,
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "episode_id": episode_dir.name,
        "status": status,
        "tool": {"name": "OpenCV YuNet + SFace", "opencv_version": cv2.__version__,
                 "yunet_model_filename": yunet_model.name, "yunet_model_sha256": _sha(yunet_model),
                 "sface_model_filename": sface_model.name, "sface_model_sha256": _sha(sface_model)},
        "inputs": {
            "reference": {"path": reference_path.relative_to(ROOT).as_posix(), "sha256": _sha(reference_path)},
            "candidate_count": len(candidate_paths),
        },
        "policy": {"character_assignment": "NOT_PERFORMED", "frame_review_write": "NOT_PERFORMED",
                   "threshold": "UNSET_REQUIRES_PROJECT_DATASET_CALIBRATION",
                   "note": "Similarity ranking is a triage hint; style, pose, lighting, occlusion, and face size can change scores."},
        "summary": {"reference_face_count": len(reference_faces),
                    "candidate_count": len(candidate_paths),
                    "candidate_with_face_count": sum(row["face_count"] > 0 for row in candidate_rows),
                    "top_candidate_match": comparisons[0] if comparisons else None,
                    "elapsed_seconds": round(time.perf_counter() - started, 3)},
        "reference_faces": [_face_summary(row, reference) for row in reference_faces],
        "candidate_ranking": candidate_rows,
        "comparisons": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True, action="append",
                        help="Candidate image; may be supplied repeatedly for cross-frame ranking")
    parser.add_argument("--yunet-model", required=True)
    parser.add_argument("--sface-model", required=True)
    args = parser.parse_args()
    episode_dir = Path(args.episode_dir).resolve()
    try:
        data = diagnose(episode_dir, args.reference, args.candidate,
                        Path(args.yunet_model), Path(args.sface_model))
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "diagnostic_only": True,
                          "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    target = episode_dir / OUTPUT_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "report": target.relative_to(ROOT).as_posix(),
                      "summary": data["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
