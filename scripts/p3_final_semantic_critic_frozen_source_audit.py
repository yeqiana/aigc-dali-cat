#!/usr/bin/env python3
"""Read-only byte-exact audit and runtime-only recovery for a Final Review source set."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import frame_semantic_review
import production_ledger

EPISODE = ROOT / "episodes/误入桃花源"
REVIEW_PATH = EPISODE / frame_semantic_review.SUMMARY_REL
DEFAULT_REPORT = ROOT / "reports/p3-final-semantic-critic-frozen-source-audit-20260928.json"
DEFAULT_BUNDLE = ROOT / ".storyos/p3-final-semantic-critic/historical-frozen-source/误入桃花源/frame-semantic-review-attempt-2"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_json(value: object) -> str:
    return sha_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def git_exact_blob(rel_path: str, target_sha: str) -> tuple[bytes, str] | None:
    commits = subprocess.run(
        ["git", "log", "--all", "--format=%H", "--", rel_path],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.splitlines()
    for commit in commits:
        result = subprocess.run(
            ["git", "show", f"{commit}:{rel_path}"], cwd=ROOT,
            check=False, capture_output=True,
        )
        if result.returncode == 0 and sha_bytes(result.stdout) == target_sha:
            return result.stdout, commit
    return None


def source_record(kind: str, rel_path: str, bound_sha: str, current_path: Path) -> tuple[dict, bytes | None]:
    current_sha = sha_file(current_path) if current_path.is_file() else None
    if current_sha == bound_sha:
        return ({"kind": kind, "path": rel_path, "review_bound_sha256": bound_sha,
                 "current_sha256": current_sha, "current_match": True,
                 "historical_exact_found": False, "recovery_origin": "current_file",
                 "git_commit": None, "recovered_sha256": current_sha, "exact_match": True}, None)
    recovered = git_exact_blob(rel_path, bound_sha)
    if recovered is None:
        return ({"kind": kind, "path": rel_path, "review_bound_sha256": bound_sha,
                 "current_sha256": current_sha, "current_match": False,
                 "historical_exact_found": False, "recovery_origin": None,
                 "git_commit": None, "recovered_sha256": None, "exact_match": False}, None)
    raw, commit = recovered
    return ({"kind": kind, "path": rel_path, "review_bound_sha256": bound_sha,
             "current_sha256": current_sha, "current_match": False,
             "historical_exact_found": True, "recovery_origin": "git_exact_blob",
             "git_commit": commit, "recovered_sha256": sha_bytes(raw), "exact_match": True}, raw)


def _write_immutable(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise RuntimeError(f"immutable evidence already exists with different bytes: {path}")


def audit(*, create_bundle: bool = True, report_path: Path = DEFAULT_REPORT,
          bundle_path: Path = DEFAULT_BUNDLE) -> dict:
    report_path = report_path if report_path.is_absolute() else ROOT / report_path
    bundle_path = bundle_path if bundle_path.is_absolute() else ROOT / bundle_path
    review_raw = REVIEW_PATH.read_bytes()
    review = json.loads(review_raw.decode("utf-8-sig"))
    story, storyboard = frame_semantic_review.episode_files(EPISODE)
    bindings: list[dict] = []
    recovered_bytes: dict[str, bytes] = {}

    text_sources = (
        ("story", story),
        ("storyboard", storyboard),
        ("caption_source", ROOT / str(review.get("caption_source") or "")),
    )
    for kind, path in text_sources:
        rel = path.resolve().relative_to(ROOT.resolve()).as_posix()
        bound = review.get({"story": "story_sha256", "storyboard": "storyboard_sha256",
                            "caption_source": "caption_source_sha256"}[kind])
        record, raw = source_record(kind, rel, str(bound or ""), path)
        bindings.append(record)
        if raw is not None:
            recovered_bytes[kind] = raw

    visual_contract = frame_semantic_review.stable_visual_contract(EPISODE)
    visual_sha = sha_json(visual_contract)
    bindings.append({"kind": "visual_contract_projection", "path": "episodes/误入桃花源/meta/story-gates.json#stable_visual_contract",
                     "review_bound_sha256": review.get("visual_contract_sha256"),
                     "current_sha256": visual_sha, "current_match": visual_sha == review.get("visual_contract_sha256"),
                     "historical_exact_found": False, "recovery_origin": "current_authority_projection",
                     "git_commit": None, "recovered_sha256": visual_sha,
                     "exact_match": visual_sha == review.get("visual_contract_sha256")})

    ledger = production_ledger.load_authority(EPISODE, default={}) or {}
    ledger_frames = ledger.get("frames") or {}
    frame_records = []
    for row in review.get("frames") or []:
        key = str(row.get("frame")).zfill(2)
        frame = ledger_frames.get(key) or {}
        asset = frame.get("approved_asset") or {}
        raw_path = asset.get("path") or asset.get("asset_path")
        bound = str(row.get("asset_sha256") or "")
        path = (ROOT / str(raw_path)).resolve() if raw_path else ROOT / "__missing__"
        current_sha = sha_file(path) if path.is_file() else None
        ledger_sha = str(asset.get("sha256") or "")
        exact = current_sha == bound and ledger_sha == bound
        frame_records.append({"frame": key, "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else None,
                              "review_bound_sha256": bound, "current_sha256": current_sha,
                              "canonical_ledger_sha256": ledger_sha,
                              "canonical_ledger_status": frame.get("status"),
                              "current_match": exact, "historical_exact_found": False,
                              "recovery_origin": "current_reviewed_asset" if exact else None,
                              "recovered_sha256": current_sha, "exact_match": exact})

    frame_set_sha_match = len(frame_records) == len(review.get("frames") or []) == 20 and all(
        row["exact_match"] for row in frame_records)
    all_exact = all(row.get("exact_match") is True for row in bindings) and frame_set_sha_match
    exact_count = sum(bool(row.get("exact_match")) for row in bindings) + sum(bool(row.get("exact_match")) for row in frame_records)
    total_count = len(bindings) + len(frame_records)
    status = "RECOVERABLE_EXACT" if all_exact else ("PARTIALLY_RECOVERABLE" if exact_count else "UNRECOVERABLE")

    manifest = None
    bundle_rel = None
    if create_bundle and status == "RECOVERABLE_EXACT":
        copied = []
        for kind, filename in (("story", "story.md"), ("storyboard", "storyboard.md"), ("caption_source", "subtitles.yaml")):
            item = next(row for row in bindings if row["kind"] == kind)
            raw = recovered_bytes.get(kind)
            if raw is None:
                raw = (ROOT / item["path"]).read_bytes()
            if sha_bytes(raw) != item["review_bound_sha256"]:
                raise RuntimeError(f"byte-exact source recovery failed before capsule write: {kind}")
            _write_immutable(bundle_path / filename, raw)
            copied.append({**item, "bundle_path": (bundle_path / filename).resolve().relative_to(ROOT).as_posix(),
                           "byte_exact": True})
        manifest = {
            "schema_version": 1,
            "episode": "episodes/误入桃花源",
            "source_type": "historical_final_semantic_exact",
            "canonical_final_review_path": REVIEW_PATH.relative_to(ROOT).as_posix(),
            "canonical_final_review_sha256": sha_bytes(review_raw),
            "source_set_status": status,
            "runtime_evidence_only": True,
            "canonical": False,
            "canonical_write": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sources": copied + [row for row in bindings if row["kind"] == "visual_contract_projection"],
            "frame_set": frame_records,
            "frame_set_sha_match": frame_set_sha_match,
            "authority_write": False,
            "episode_transition": False,
            "image_generation_invoked": False,
        }
        manifest_raw = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        _write_immutable(bundle_path / "source-manifest.json", manifest_raw)
        bundle_rel = bundle_path.resolve().relative_to(ROOT).as_posix()

    report = {
        "schema_version": 1,
        "kind": "p3_final_semantic_critic_frozen_source_audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "episode": "episodes/误入桃花源",
        "canonical_review_path": REVIEW_PATH.relative_to(ROOT).as_posix(),
        "canonical_review_sha256": sha_bytes(review_raw),
        "historical_git_commit": next((row["git_commit"] for row in bindings if row.get("git_commit")), None),
        "source_bindings": bindings,
        "frame_assets": frame_records,
        "frame_set_sha_match": frame_set_sha_match,
        "visual_contract_match": next(row["exact_match"] for row in bindings if row["kind"] == "visual_contract_projection"),
        "source_set_status": status,
        "exact_binding_count": exact_count,
        "binding_count": total_count,
        "historical_bundle_path": bundle_rel,
        "historical_bundle_manifest_sha256": sha_bytes((bundle_path / "source-manifest.json").read_bytes()) if manifest else None,
        "canonical_files_modified": False,
        "episode_modified": False,
        "authority_modified": False,
        "image_generation_invoked": False,
    }
    report_raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _write_immutable(report_path, report_raw)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-bundle", action="store_true", help="audit only; do not create runtime bundle")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args()
    report = audit(create_bundle=not args.no_bundle, report_path=args.report, bundle_path=args.bundle)
    print(json.dumps({key: report.get(key) for key in (
        "episode", "source_set_status", "exact_binding_count", "binding_count",
        "frame_set_sha_match", "visual_contract_match", "historical_bundle_path",
    )}, ensure_ascii=False))
    return 0 if report["source_set_status"] == "RECOVERABLE_EXACT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
