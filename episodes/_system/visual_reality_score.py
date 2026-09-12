#!/usr/bin/env python3
"""Automated visual-risk score; it supplements, never replaces, human review."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import story_json

REL = Path("meta/visual-reality-score.json")
DIMENSIONS = ("phone_capture", "lighting_realism", "depth_realism", "human_naturalness", "scene_lived_in", "ai_artifact_risk")
THRESHOLD = 70
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def score(ep: Path, frame_id: str, dimensions: dict, *, threshold: int = THRESHOLD) -> dict:
    ep = Path(ep); invalid = [k for k in DIMENSIONS if not isinstance(dimensions.get(k), (int,float)) or isinstance(dimensions.get(k), bool) or not 0 <= dimensions[k] <= 100]
    if invalid: raise ValueError("invalid reality dimensions: " + ", ".join(invalid))
    # ai_artifact_risk is inverted so every public dimension is intuitively 0..100.
    values = [dimensions[k] if k != "ai_artifact_risk" else 100-dimensions[k] for k in DIMENSIONS]
    result = {"frame_id": f"{int(frame_id):02d}", "dimensions": dimensions, "score": round(sum(values)/len(values), 2), "threshold": threshold, "decision": "pass" if sum(values)/len(values) >= threshold else "repair_required", "automated_risk_detection_only": True}
    data = story_json.read_json(ep / REL, default={"schema_version":1,"frames":{}}) or {"schema_version":1,"frames":{}}
    data.setdefault("frames", {})[result["frame_id"]] = result; data["updated_at"] = now(); story_json.write_json(ep / REL, data)
    return result
def verify(ep: Path) -> list[str]:
    data = story_json.read_json(Path(ep)/REL, default=None)
    if not isinstance(data, dict): return ["Historical Evidence Missing: meta/visual-reality-score.json"]
    frames = data.get("frames") if isinstance(data.get("frames"), dict) else {}
    return [f"visual_reality_score_missing_or_low:{key}" for key, value in frames.items() if not isinstance(value,dict) or value.get("decision") != "pass"]
