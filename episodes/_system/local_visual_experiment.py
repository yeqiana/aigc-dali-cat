#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only KPI snapshot / A-B comparison for Local Visual Triage production runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import story_json

ROOT = Path(__file__).resolve().parents[2]
PERFORMANCE_REL = Path("meta/episode-performance-ledger.json")
TRIAGE_REL = Path("meta/runtime/diagnostics/local-visual-triage-summary.json")
CAPTION_REL = Path("meta/caption-image-audit.json")
SEMANTIC_REL = Path("meta/frame-semantic-review.json")


def _read(ep: Path, rel: Path) -> dict:
    path = ep / rel
    if not path.is_file():
        return {}
    data = story_json.read_json(path, default={})
    return data if isinstance(data, dict) else {}


def _num(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _int(value):
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def snapshot(ep: Path) -> dict:
    ep = Path(ep).resolve()
    if not ep.is_dir():
        raise ValueError(f"episode directory not found: {ep}")
    perf = _read(ep, PERFORMANCE_REL)
    triage = _read(ep, TRIAGE_REL)
    caption = _read(ep, CAPTION_REL)
    semantic = _read(ep, SEMANTIC_REL)

    perf_summary = perf.get("summary") if isinstance(perf.get("summary"), dict) else {}
    critical = perf_summary.get("critical_path") if isinstance(perf_summary.get("critical_path"), dict) else {}
    images = perf_summary.get("images") if isinstance(perf_summary.get("images"), dict) else {}
    slo = perf_summary.get("performance_slo") if isinstance(perf_summary.get("performance_slo"), dict) else {}
    execution = perf_summary.get("execution_wall") if isinstance(perf_summary.get("execution_wall"), dict) else {}
    caption_summary = caption.get("summary") if isinstance(caption.get("summary"), dict) else {}
    vision = caption_summary.get("vision_review_telemetry") if isinstance(caption_summary.get("vision_review_telemetry"), dict) else {}
    semantic_frames = semantic.get("frames") if isinstance(semantic.get("frames"), list) else []
    frame_count = _int(caption_summary.get("total_frames")) or len(semantic_frames) or None

    vision_tokens = vision.get("vision_tokens") if isinstance(vision.get("vision_tokens"), dict) else {}
    token_total = sum(
        int(value) for value in vision_tokens.values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ) if vision_tokens else None

    metrics = {
        "frame_count": frame_count,
        "critical_path_seconds": _num(critical.get("critical_path_seconds")),
        "active_wall_seconds": _num(slo.get("active_wall_seconds"))
            or _num(execution.get("active_wall_seconds")),
        "image_attempts": _int(images.get("attempts")),
        "repair_attempts": _int(images.get("repair_attempts")),
        "technical_failures_or_retries": _int(images.get("technical_failures_or_retries")),
        "image_backend_seconds": _num(images.get("image_backend_seconds")),
        "caption_vision_candidate_frames": _int(vision.get("vision_candidate_frames")),
        "caption_local_skipped_frames": _int(vision.get("local_skipped_frames")),
        "caption_vision_frames": _int(vision.get("vision_frames")),
        "caption_vision_call_count": _int(vision.get("vision_call_count")),
        "caption_vision_elapsed_seconds": _num(vision.get("vision_elapsed_seconds")),
        "caption_vision_token_total": token_total,
        "local_triage_report_count": _int(triage.get("report_count")),
        "local_triage_elapsed_seconds": _num(triage.get("local_triage_elapsed_seconds")),
        "near_duplicate_evidence_count": _int(triage.get("near_duplicate_evidence_count")),
        "repair_noop_count": _int(triage.get("repair_noop_count")),
    }
    if frame_count and frame_count > 0:
        for key in (
            "critical_path_seconds",
            "active_wall_seconds",
            "repair_attempts",
            "caption_vision_call_count",
            "caption_vision_elapsed_seconds",
            "caption_vision_token_total",
            "local_triage_elapsed_seconds",
        ):
            value = metrics.get(key)
            metrics[f"{key}_per_frame"] = round(float(value) / frame_count, 6) if value is not None else None

    quality = {
        "frame_semantic_passed": ((semantic.get("summary") or {}).get("passed") is True),
        "frame_semantic_issue_count": len(semantic.get("issue_codes") or []),
        "near_duplicate_final_count": len(semantic.get("near_duplicate_pairs") or []),
        "caption_image_passed": caption_summary.get("passed") is True,
    }
    sources = {
        "performance_ledger_present": bool(perf),
        "performance_ledger_finalized": perf.get("finalized_at") is not None,
        "caption_audit_present": bool(caption),
        "caption_vision_telemetry_present": bool(vision),
        "local_triage_summary_present": bool(triage),
        "frame_semantic_review_present": bool(semantic),
    }
    warnings = []
    if not sources["performance_ledger_present"]:
        warnings.append("PERFORMANCE_LEDGER_MISSING")
    if not sources["caption_vision_telemetry_present"]:
        warnings.append("CAPTION_VISION_TELEMETRY_MISSING")
    if not sources["local_triage_summary_present"]:
        warnings.append("LOCAL_TRIAGE_SUMMARY_MISSING")
    if perf and not sources["performance_ledger_finalized"]:
        warnings.append("PERFORMANCE_LEDGER_NOT_FINALIZED")
    return {
        "schema_version": 1,
        "read_only": True,
        "episode_path": ep.relative_to(ROOT).as_posix() if ep.is_relative_to(ROOT) else str(ep),
        "metrics": metrics,
        "quality": quality,
        "provider_status_counts": triage.get("provider_status_counts") or {},
        "triage_status_counts": triage.get("status_counts") or {},
        "sources": sources,
        "warnings": warnings,
    }


def _reduction_pct(baseline, treatment):
    if baseline is None or treatment is None or float(baseline) <= 0:
        return None
    return round((float(baseline) - float(treatment)) / float(baseline) * 100.0, 3)


def compare(baseline: dict, treatment: dict) -> dict:
    keys = {
        "critical_path_seconds_per_frame": 25.0,
        "repair_attempts_per_frame": 20.0,
        "caption_vision_call_count_per_frame": 40.0,
        "caption_vision_elapsed_seconds_per_frame": 40.0,
        "caption_vision_token_total_per_frame": 40.0,
    }
    deltas = {}
    missing = []
    for key, target in keys.items():
        base = (baseline.get("metrics") or {}).get(key)
        test = (treatment.get("metrics") or {}).get(key)
        reduction = _reduction_pct(base, test)
        deltas[key] = {
            "baseline": base,
            "treatment": test,
            "reduction_pct": reduction,
            "target_reduction_pct": target,
            "target_met": reduction is not None and reduction >= target,
        }
        if reduction is None:
            missing.append(key)
    baseline_quality = baseline.get("quality") or {}
    treatment_quality = treatment.get("quality") or {}
    quality_regression = (
        baseline_quality.get("frame_semantic_passed") is True
        and treatment_quality.get("frame_semantic_passed") is not True
    ) or (
        baseline_quality.get("caption_image_passed") is True
        and treatment_quality.get("caption_image_passed") is not True
    )
    measurable = not missing
    return {
        "schema_version": 1,
        "read_only": True,
        "status": "MEASURABLE" if measurable else "INSUFFICIENT_EVIDENCE",
        "baseline_episode": baseline.get("episode_path"),
        "treatment_episode": treatment.get("episode_path"),
        "deltas": deltas,
        "missing_primary_metrics": missing,
        "quality_regression": quality_regression,
        "all_targets_met": measurable
            and not quality_regression
            and all(row["target_met"] for row in deltas.values()),
        "note": (
            "Comparison normalizes primary metrics per frame. Historical episodes without "
            "current Vision telemetry or Local Triage evidence remain partial baselines."
        ),
    }


def treatment_readiness(data: dict) -> dict:
    metrics = data.get("metrics") or {}
    sources = data.get("sources") or {}
    quality = data.get("quality") or {}
    checks = {
        "performance_ledger": sources.get("performance_ledger_present") is True,
        "caption_vision_telemetry": sources.get("caption_vision_telemetry_present") is True,
        "local_triage_summary": sources.get("local_triage_summary_present") is True
            and (metrics.get("local_triage_report_count") or 0) > 0,
        "frame_semantic_pass": quality.get("frame_semantic_passed") is True,
        "caption_image_pass": quality.get("caption_image_passed") is True,
        "frame_count": (metrics.get("frame_count") or 0) > 0,
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "missing": [key for key, value in checks.items() if not value],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("snapshot")
    p.add_argument("episode")
    p = sub.add_parser("readiness")
    p.add_argument("episode")
    p = sub.add_parser("compare")
    p.add_argument("baseline")
    p.add_argument("treatment")
    args = parser.parse_args()
    if args.command == "snapshot":
        result = snapshot(Path(args.episode))
    elif args.command == "readiness":
        result = treatment_readiness(snapshot(Path(args.episode)))
    else:
        result = compare(snapshot(Path(args.baseline)), snapshot(Path(args.treatment)))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
