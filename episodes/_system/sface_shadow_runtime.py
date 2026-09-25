#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-soft SFace shadow integration for generated candidates.

No threshold is used and no identity assignment is made. The result only ranks
candidate similarity against SHA-bound individual character-master crops.
"""
from __future__ import annotations

import os
from pathlib import Path

import story_json
import visual_fingerprint

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / ".storyos_cache" / "models"
YUNET_ENV = "STORY_OS_YUNET_MODEL"
SFACE_ENV = "STORY_OS_SFACE_MODEL"
CROPS_REL = Path("meta/character-master-crops.json")


def _resolve_model(env_name: str, pattern: str) -> Path | None:
    raw = os.environ.get(env_name)
    if raw:
        path = Path(raw)
        if path.is_file():
            return path.resolve()
    if MODELS_DIR.is_dir():
        rows = sorted(MODELS_DIR.glob(pattern))
        if rows:
            return rows[0].resolve()
    return None


def _repo_image(raw: object, sha256: object) -> Path | None:
    if not raw:
        return None
    path = Path(str(raw))
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        return None
    if not path.is_file():
        return None
    expected = str(sha256 or "").lower()
    if len(expected) == 64 and visual_fingerprint.sha256_file(path).lower() != expected:
        return None
    return path


def _references(ep: Path, max_references: int) -> list[dict]:
    manifest = Path(ep).resolve() / CROPS_REL
    data = story_json.read_json(manifest, default={}) if manifest.is_file() else {}
    rows = []
    for character_id, item in sorted((data.get("items") or {}).items()):
        if not isinstance(item, dict):
            continue
        path = _repo_image(item.get("path"), item.get("sha256"))
        if path is None:
            continue
        rows.append({
            "character_id": str(character_id),
            "path": path,
            "sha256": visual_fingerprint.sha256_file(path),
        })
        if len(rows) >= max_references:
            break
    return rows


def inspect(ep: Path, candidate: Path, config: dict) -> dict:
    if config.get("enabled") is not True:
        return {"status": "SKIPPED", "reason": "DISABLED", "diagnostic_only": True}
    yunet = _resolve_model(YUNET_ENV, "face_detection_yunet*.onnx")
    sface = _resolve_model(SFACE_ENV, "face_recognition_sface*.onnx")
    if yunet is None or sface is None:
        return {
            "status": "SKIPPED", "reason": "MODEL_MISSING", "diagnostic_only": True,
            "yunet_available": yunet is not None, "sface_available": sface is not None,
        }
    refs = _references(Path(ep), int(config.get("max_references") or 2))
    if not refs:
        return {"status": "SKIPPED", "reason": "INDIVIDUAL_MASTER_MISSING", "diagnostic_only": True}
    try:
        import identity_sface_diagnostic
        results = []
        for ref in refs:
            report = identity_sface_diagnostic.diagnose(
                Path(ep), str(ref["path"]), [str(Path(candidate).resolve())], yunet, sface
            )
            reference_count = int((report.get("summary") or {}).get("reference_face_count") or 0)
            ranking = report.get("candidate_ranking") or []
            top = ranking[0].get("top_cosine_similarity") if ranking else None
            results.append({
                "character_id": ref["character_id"],
                "reference_path": ref["path"].relative_to(ROOT).as_posix(),
                "reference_sha256": ref["sha256"],
                "reference_face_count": reference_count,
                "candidate_face_count": int(ranking[0].get("face_count") or 0) if ranking else 0,
                "top_cosine_similarity": top,
                "usable_single_face_reference": reference_count == 1,
            })
        usable = [row for row in results if row["usable_single_face_reference"] and row["top_cosine_similarity"] is not None]
        return {
            "status": "COMPLETE" if usable else "UNKNOWN",
            "diagnostic_only": True,
            "may_affect_gate": False,
            "threshold": "UNSET_REQUIRES_PROJECT_DATASET_CALIBRATION",
            "candidate_sha256": visual_fingerprint.sha256_file(Path(candidate)),
            "models": {
                "yunet": yunet.name,
                "sface": sface.name,
            },
            "results": results,
            "ranking": sorted(usable, key=lambda row: float(row["top_cosine_similarity"]), reverse=True),
        }
    except Exception as exc:
        return {"status": "FAILED", "diagnostic_only": True, "reason": f"{type(exc).__name__}: {exc}"}
