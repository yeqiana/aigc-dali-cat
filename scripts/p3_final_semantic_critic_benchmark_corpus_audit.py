#!/usr/bin/env python3
"""Read-only feasibility audit for independent Final Semantic visual benchmark data."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
REVIEW_PATTERNS = ("meta/frame-semantic-review*.json", "meta/frame-semantic-candidate*.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _gt_independent(sample: dict) -> bool:
    source = str(sample.get("ground_truth_source") or "").lower()
    kind = str(sample.get("ground_truth_type") or "").lower()
    return bool(sample.get("ground_truth_sha256")) and (
        kind in {"deterministic_regression_fixture", "frozen_manual_visual_label", "frozen_expected_visual_defect"}
        or source in {"deterministic_regression_fixture", "frozen_manual_visual_label", "frozen_expected_visual_defect"}
    ) and sample.get("critic_derived") is not True and sample.get("label_source_is_model_review") is not True


def validate_sample(sample: dict, root: Path = ROOT) -> list[str]:
    """Return fail-closed rejection reasons for a proposed immutable corpus sample."""
    reasons: list[str] = []
    if not _gt_independent(sample):
        reasons.append("NO_INDEPENDENT_GROUND_TRUTH")
        if sample.get("label_source_is_model_review") is True:
            reasons.append("MODEL_REVIEW_ONLY_LABEL")
    frames = sample.get("frames") if isinstance(sample.get("frames"), list) else []
    if not frames:
        reasons.append("NO_VISUAL_ASSETS")
        reasons.append("TEXT_ONLY_FIXTURE")
    for frame in frames:
        rel = Path(str(frame.get("path") or ""))
        path = (root / rel).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            reasons.append("MISSING_FRAME_ASSET")
            continue
        if not frame.get("sha256") or sha256(path) != frame.get("sha256"):
            reasons.append("FRAME_SHA_DRIFT")
    if not sample.get("source_bindings") or any(not row.get("sha256") for row in sample.get("source_bindings", [])):
        reasons.append("SOURCE_BINDING_INCOMPLETE")
    return sorted(set(reasons))


def evaluate_corpus(samples: list[dict], root: Path = ROOT) -> dict:
    seen: set[str] = set()
    accepted: list[dict] = []
    rejected: list[dict] = []
    for sample in samples:
        reasons = validate_sample(sample, root)
        key = str(sample.get("frozen_source_set_sha256") or "")
        if key and key in seen:
            reasons.append("DUPLICATE_FROZEN_SOURCE_SET")
        if key:
            seen.add(key)
        (rejected if reasons else accepted).append({"sample_id": sample.get("sample_id"), "reasons": sorted(set(reasons))} if reasons else sample)
    passes = sum(str(row.get("ground_truth_label", "")).upper() == "PASS" for row in accepted)
    fails = sum(str(row.get("ground_truth_label", "")).upper() in {"FAIL", "REPAIR"} for row in accepted)
    eligible = len(accepted) >= 5 and passes >= 2 and fails >= 2
    return {"accepted": accepted, "rejected": rejected, "eligible": eligible,
            "eligible_frozen_visual_sets": len(accepted), "pass_label_count": passes,
            "fail_label_count": fails, "blockers": [] if eligible else ["LABELLED_FINAL_SEMANTIC_SAMPLE_SET_INSUFFICIENT"]}


def _git_paths(args: list[str]) -> list[str]:
    try:
        result = subprocess.run(["git", "log", "--all", "--name-only", "--pretty=format:", "--", *args],
                                cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except (OSError, subprocess.CalledProcessError):
        return []
    return sorted({line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()})


def _review_paths() -> list[Path]:
    found: set[Path] = set()
    episodes = ROOT / "episodes"
    for pattern in REVIEW_PATTERNS:
        found.update(episodes.glob(f"**/{pattern}"))
    return sorted(path for path in found if path.is_file())


def _review_sample(path: Path, all_images: list[Path]) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sample_id": path.relative_to(ROOT).as_posix(), "reasons": ["INVALID_REVIEW_EVIDENCE"]}
    episode = path.parent.parent
    frame_rows = data.get("frames") if isinstance(data.get("frames"), list) else []
    image_hashes: dict[str, Path] = {}
    for image in all_images:
        try:
            image_hashes.setdefault(sha256(image), image)
        except OSError:
            continue
    matched = []
    missing = 0
    for frame in frame_rows:
        digest = frame.get("asset_sha256")
        asset = image_hashes.get(str(digest))
        if asset:
            matched.append({"frame": frame.get("frame"), "path": asset.relative_to(ROOT).as_posix(), "sha256": digest})
        else:
            missing += 1
    provenance = data.get("critic_provenance") or {}
    is_model_label = bool(provenance.get("runtime") or provenance.get("reviewer_mode") or provenance.get("execution_source"))
    independent = False
    findings = []
    if not frame_rows:
        findings.append("NO_VISUAL_ASSETS")
    if missing:
        findings.append("FRAME_SHA_UNRECOVERABLE")
    if is_model_label:
        findings.extend(["NO_INDEPENDENT_GROUND_TRUTH", "MODEL_REVIEW_ONLY_LABEL"])
    else:
        findings.append("NO_INDEPENDENT_GROUND_TRUTH")
    findings.append("SOURCE_BINDING_INCOMPLETE")
    return {"sample_id": path.relative_to(ROOT).as_posix(), "sample_type": "historical_review",
            "episode": episode.parent.name, "review_path": path.relative_to(ROOT).as_posix(),
            "review_sha256": sha256(path), "review_label": "PASS" if (data.get("summary") or {}).get("passed") is True else "FAIL",
            "ground_truth_independent": independent, "model_derived_label": is_model_label,
            "frame_count": len(frame_rows), "frame_sha_matches_found": len(matched), "frame_sha_unrecoverable": missing,
            "matched_frames": matched, "reasons": sorted(set(findings))}


def build_audit() -> dict:
    review_paths = _review_paths()
    all_images = [p for p in (ROOT / "episodes").rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    all_images += [p for p in (ROOT / "tests/fixtures").rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    historical_review_paths = _git_paths([":(glob)episodes/**/meta/frame-semantic-review*.json", ":(glob)episodes/**/meta/frame-semantic-candidate*.json"])
    historical_visual_paths = _git_paths([":(glob)episodes/**/*.png", ":(glob)episodes/**/*.jpg", ":(glob)episodes/**/*.jpeg", ":(glob)episodes/**/*.webp", ":(glob)tests/fixtures/**/*.png", ":(glob)tests/fixtures/**/*.jpg", ":(glob)tests/fixtures/**/*.jpeg", ":(glob)tests/fixtures/**/*.webp"])
    review_sets = [_review_sample(path, all_images) for path in review_paths]

    fixture_path = ROOT / "tests/fixtures/p3_final_semantic_critic/cases.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8")) if fixture_path.is_file() else {"cases": []}
    rejected_fixtures = [{"sample_id": row.get("sample_id"), "reasons": ["NO_VISUAL_ASSETS", "NO_INDEPENDENT_GROUND_TRUTH", "TEXT_ONLY_FIXTURE"]}
                         for row in fixture.get("cases", [])]
    git_image_paths = [p for p in historical_visual_paths if Path(p).suffix.lower() in IMAGE_SUFFIXES]
    report = {
        "schema_version": 1, "kind": "p3_final_semantic_critic_benchmark_corpus_audit",
        "episodes_scanned": len({p.parent.parent for p in review_paths}),
        "historical_review_sets_scanned": len(review_paths), "fixture_sets_scanned": len(fixture.get("cases", [])),
        "git_historical_review_paths": historical_review_paths,
        "git_historical_visual_asset_paths": git_image_paths,
        "visual_asset_sets_found": sum(bool(row.get("frame_count")) and row.get("frame_sha_unrecoverable") == 0 for row in review_sets),
        "independent_ground_truth_sets": 0,
        "eligible_frozen_visual_sets": 0,
        "pass_label_count": 0, "fail_label_count": 0, "repair_label_count": 0,
        "duplicate_source_sets_rejected": 0,
        "model_derived_labels_rejected": sum(row.get("model_derived_label") is True for row in review_sets),
        "text_only_fixtures_rejected": len(rejected_fixtures),
        "historical_review_findings": review_sets,
        "fixture_rejections": rejected_fixtures,
        "other_independent_visual_label_records": [],
        "manual_review_records_rejected": [
            {"path": "episodes/07_误入/05_误入桃花源/release/production-review.md", "reason": "ACCEPTANCE_OF_KNOWN_DEFECTS_NOT_INDEPENDENT_PER_SAMPLE_VISUAL_LABEL"}
        ],
        "eligible": False,
        "blockers": ["LABELLED_FINAL_SEMANTIC_SAMPLE_SET_INSUFFICIENT", "INDEPENDENT_VISUAL_GROUND_TRUTH_INSUFFICIENT"],
        "audit_scope": {"local_episode_reviews": len(review_paths), "current_episode_images": len(all_images),
                        "git_history_review_paths": len(historical_review_paths), "git_history_visual_asset_paths": len(git_image_paths),
                        "git_history_read_only": True}
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/p3-final-semantic-critic-benchmark-corpus-audit-20260928.json")
    args = parser.parse_args()
    out = ROOT / args.output
    if out.exists():
        raise SystemExit(f"refusing to overwrite immutable evidence: {out}")
    report = build_audit()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("episodes_scanned", "historical_review_sets_scanned", "visual_asset_sets_found", "eligible_frozen_visual_sets", "eligible", "blockers")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
