#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified Local Visual Triage entrypoint for generated candidates.

Derived evidence may block only deterministic technical commit failures.  All
content/semantic suspicions remain advisory and flow to existing critics.
"""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import image_technical_gate
import local_visual_triage_summary
import repair_integrity
import sface_shadow_runtime
import story_json
import storyos_config
import visual_fingerprint
import visual_embedding_provider

ROOT = Path(__file__).resolve().parents[2]
REL_ROOT = Path("meta/runtime/diagnostics/local-visual-triage")
SCHEMA_VERSION = 1


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _config() -> dict:
    cfg = storyos_config.load_config()
    row = storyos_config.get_path(cfg, "production.local_visual_triage", {})
    return row if isinstance(row, dict) else {}


def enabled() -> bool:
    return _config().get("enabled") is True


def _expected_canvas(ep: Path) -> tuple[int, int] | None:
    try:
        import production_ledger
        data = production_ledger.load_authority(Path(ep).resolve(), default={}) or {}
        canvas = data.get("canvas") or {}
        width, height = int(canvas.get("width") or 0), int(canvas.get("height") or 0)
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass
    cfg = storyos_config.load_config()
    ratio = str(storyos_config.get_path(cfg, "image.default_aspect_ratio", "4:5"))
    canvas = storyos_config.get_path(cfg, f"image.canvases.{ratio}", {}) or {}
    try:
        return int(canvas["width"]), int(canvas["height"])
    except Exception:
        return None


def diagnostic_rel(item_id: object) -> Path:
    token = "".join(ch for ch in str(item_id or "candidate") if ch.isalnum() or ch in "-_")
    return REL_ROOT / f"{token or 'candidate'}.json"


def _previous_reports(ep: Path) -> list[dict]:
    root = Path(ep).resolve() / REL_ROOT
    if not root.is_dir():
        return []
    rows = []
    for path in sorted(root.glob("*.json")):
        try:
            data = story_json.read_json(path, default={})
            if isinstance(data, dict) and isinstance(data.get("fingerprint"), dict):
                rows.append(data)
        except Exception:
            continue
    return rows


def _duplicate_evidence(ep: Path, item: dict, fp: dict, config: dict) -> list[dict]:
    frame = int(item.get("frame") or 0)
    pmax = int(config.get("near_duplicate_phash_max_distance", 4))
    dmax = int(config.get("near_duplicate_dhash_max_distance", 4))
    hits = []
    for row in _previous_reports(ep):
        if int(row.get("frame") or 0) == frame:
            continue
        other = row.get("fingerprint") or {}
        try:
            comparison = visual_fingerprint.compare(fp, other)
        except Exception:
            continue
        exact = comparison["same_sha256"]
        near = comparison["phash_distance"] <= pmax and comparison["dhash_distance"] <= dmax
        if exact or near:
            hits.append({
                "frame": row.get("frame"),
                "queue_item_id": row.get("queue_item_id"),
                "candidate_sha256": other.get("sha256"),
                "kind": "EXACT_DUPLICATE" if exact else "NEAR_DUPLICATE",
                **comparison,
            })
    return hits


def queue_summary(report: dict) -> dict:
    return {
        "status": report.get("status"),
        "block_commit": bool(report.get("block_commit")),
        "failure_code": report.get("failure_code"),
        "issue_codes": list(report.get("issue_codes") or []),
        "diagnostic_path": report.get("diagnostic_path"),
        "candidate_sha256": report.get("candidate_sha256"),
    }


def inspect_candidate(ep: Path, item: dict, output: Path) -> dict:
    ep = Path(ep).resolve()
    output = Path(output).resolve()
    config = _config()
    started = time.perf_counter()
    if config.get("enabled") is not True:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "SKIPPED",
            "block_commit": False,
            "reason": "LOCAL_VISUAL_TRIAGE_DISABLED",
        }

    try:
        technical = image_technical_gate.inspect(
            output,
            expected_size=_expected_canvas(ep),
            config=config,
        )
        fp = technical.get("fingerprint")
        duplicates = _duplicate_evidence(ep, item, fp, config) if isinstance(fp, dict) else []
        repair = (
            repair_integrity.inspect(ep, item, output, fp, config)
            if isinstance(fp, dict)
            else {"status": "UNKNOWN", "advisory_only": True, "reason": "FINGERPRINT_UNAVAILABLE"}
        )
        embedding = visual_embedding_provider.embed(output, config.get("embedding") or {})
        sface = sface_shadow_runtime.inspect(ep, output, config.get("sface") or {})
        issues = list(technical.get("hard_errors") or []) + list(technical.get("warnings") or [])
        issues.extend(str(row.get("kind")) for row in duplicates)
        issues.extend(str(x) for x in (repair.get("issues") or []))
        hard_fail = technical.get("status") == "FAIL"
        suspect = bool(duplicates) or technical.get("status") == "SUSPECT" or repair.get("status") == "SUSPECT"
        block = bool(hard_fail and config.get("hard_failures_block_commit") is True)
        status = "FAIL" if hard_fail else ("SUSPECT" if suspect else "PASS")
        rel = diagnostic_rel(item.get("id"))
        report = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": now(),
            "derived_evidence": True,
            "stage_authority": False,
            "frame": int(item.get("frame") or 0),
            "queue_item_id": item.get("id"),
            "candidate_kind": item.get("kind"),
            "candidate_path": output.resolve().relative_to(ROOT.resolve()).as_posix()
                if output.is_relative_to(ROOT.resolve()) else str(output),
            "candidate_sha256": (fp or {}).get("sha256"),
            "status": status,
            "block_commit": block,
            "failure_code": technical.get("failure_code") if block else None,
            "issue_codes": sorted(set(issues)),
            "technical": technical,
            "fingerprint": fp,
            "duplicates": duplicates,
            "repair_integrity": repair,
            "embedding": embedding,
            "sface_shadow": sface,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "diagnostic_path": rel.as_posix(),
        }
        target = ep / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(target, report)
        try:
            local_visual_triage_summary.collect(ep, write=True)
        except Exception:
            pass
        return report
    except Exception as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": now(),
            "derived_evidence": True,
            "stage_authority": False,
            "frame": int(item.get("frame") or 0),
            "queue_item_id": item.get("id"),
            "status": "UNKNOWN",
            "block_commit": False,
            "issue_codes": ["LOCAL_TRIAGE_INTERNAL_ERROR"],
            "reason": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.perf_counter() - started, 4),
        }


def latest_for_frame(ep: Path, frame: int, candidate_sha256: str | None = None) -> dict | None:
    rows = [
        row for row in _previous_reports(Path(ep).resolve())
        if int(row.get("frame") or 0) == int(frame)
    ]
    if candidate_sha256:
        wanted = str(candidate_sha256).lower()
        rows = [row for row in rows if str(row.get("candidate_sha256") or "").lower() == wanted]
    if not rows:
        return None
    rows.sort(key=lambda row: str(row.get("generated_at") or ""))
    return rows[-1]


def hint_for_frame(ep: Path, frame: int, candidate_sha256: str | None = None) -> str:
    row = latest_for_frame(ep, frame, candidate_sha256)
    if not row or row.get("status") != "SUSPECT":
        return ""
    issues = [str(x) for x in (row.get("issue_codes") or [])][:8]
    repair = row.get("repair_integrity") or {}
    delta = repair.get("pixel_delta") or {}
    extra = []
    if delta.get("block_ssim") is not None:
        extra.append(f"repair_block_ssim={delta['block_ssim']}")
    if delta.get("changed_bbox_area_ratio") is not None:
        extra.append(f"repair_changed_bbox_ratio={delta['changed_bbox_area_ratio']}")
    detail = ", ".join(issues + extra)
    return (
        f"Local Visual Triage advisory for frame {int(frame):02d}: {detail}. "
        "These are deterministic/heuristic hints only; independently inspect actual pixels."
    )


def self_test() -> None:
    assert diagnostic_rel("abc-123").as_posix().endswith("abc-123.json")
    print("LOCAL VISUAL TRIAGE SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
