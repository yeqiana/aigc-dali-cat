#!/usr/bin/env python3
"""Read-only scan for existing, SHA-valid Final Semantic frame-set evidence."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "episodes/_system"))
sys.path.insert(0, str(ROOT / "episodes/_system/agents"))

import final_semantic_critic_adapter as critic
import frame_semantic_review

DEFAULT_OUTPUT = ROOT / "reports/p3-final-semantic-critic-real-smoke-candidates-20260928.json"


def scan() -> dict:
    rows = []
    summaries = sorted((ROOT / "episodes").rglob("frame-semantic-review.json"))
    for summary_path in summaries:
        ep = summary_path.parent.parent
        item = {
            "episode": ep.relative_to(ROOT).as_posix(),
            "canonical_review_path": summary_path.relative_to(ROOT).as_posix(),
            "canonical_review_exists": True,
            "review_pass": False,
            "reviewable_frame_count": 0,
            "source_sha_bound": False,
            "candidate_set_sha256": None,
            "eligible": False,
            "blockers": [],
        }
        try:
            state_path = ep / "meta/episode-state.json"
            if state_path.is_file():
                state = json.loads(state_path.read_text(encoding="utf-8-sig"))
                item["episode_state"] = state.get("current_state")
            else:
                item["episode_state"] = None
                item["blockers"].append("EPISODE_STATE_MISSING")
            if item["episode_state"] != "STORYBOARD_LOCKED":
                item["blockers"].append("EPISODE_NOT_IN_READ_ONLY_SMOKE_STATE")
                rows.append(item)
                continue
            review = json.loads(summary_path.read_text(encoding="utf-8-sig"))
            item["review_pass"] = (review.get("summary") or {}).get("passed") is True
            frames = frame_semantic_review.reviewable_frame_records(ep, require_files=True)
            item["reviewable_frame_count"] = len(frames)
            expected = [{"frame": row["frame"], "asset_sha256": row["sha256"]} for row in frames]
            item["source_sha_bound"] = review.get("frames") == expected
            story, storyboard = frame_semantic_review.episode_files(ep)
            item["story_sha_match"] = review.get("story_sha256") == critic.sha256_file(story)
            item["storyboard_sha_match"] = review.get("storyboard_sha256") == critic.sha256_file(storyboard)
            item["visual_contract_sha_match"] = review.get("visual_contract_sha256") == frame_semantic_review.sha256_json(
                frame_semantic_review.stable_visual_contract(ep)
            )
            binding_errors = frame_semantic_review.reviewable_phase4_binding_errors(ep, frames)
            if binding_errors:
                item["blockers"].extend(binding_errors[:8])
            if not item["source_sha_bound"]:
                item["blockers"].append("CURRENT_REVIEWABLE_SET_DIFFERS_FROM_CANONICAL_REVIEW")
            for field, code in (("story_sha_match", "CANONICAL_STORY_SOURCE_SHA_STALE"),
                                ("storyboard_sha_match", "CANONICAL_STORYBOARD_SOURCE_SHA_STALE"),
                                ("visual_contract_sha_match", "CANONICAL_VISUAL_CONTRACT_SHA_STALE")):
                if not item[field]:
                    item["blockers"].append(code)
            # A canonical FAIL is still a valid frozen comparison input. The
            # smoke checks wiring and records disagreement; it never treats
            # the existing model review as independent ground truth.
            if (not binding_errors and item["source_sha_bound"] and item["story_sha_match"]
                    and item["storyboard_sha_match"] and item["visual_contract_sha_match"] and frames
                    and item["episode_state"] == "STORYBOARD_LOCKED"):
                capsule = critic.build_frozen_review_capsule(ep)
                item["candidate_set_sha256"] = capsule["frame_set_sha256"]
                item["capsule_sha256"] = capsule["capsule_sha256"]
                item["canonical_semantic_failure_is_comparison_input"] = item["review_pass"] is False
                item["eligible"] = True
        except Exception as exc:
            item["blockers"].append(f"{type(exc).__name__}: {exc}")
        rows.append(item)
    eligible = [item for item in rows if item["eligible"]]
    return {
        "schema_version": 1,
        "kind": "p3_final_semantic_critic_real_smoke_candidates",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "model_invoked": False,
        "canonical_review_invoked": False,
        "episode_files_modified": False,
        "authority_modified": False,
        "production_ledger_modified": False,
        "image_generation_invoked": False,
        "candidate_count": len(rows),
        "eligible_count": len(eligible),
        "candidates": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = scan()
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        print(f"refusing to overwrite candidate evidence: {args.output}", file=sys.stderr)
        return 2
    print(json.dumps({key: result[key] for key in ("candidate_count", "eligible_count", "read_only", "image_generation_invoked")}, ensure_ascii=False))
    for item in result["candidates"]:
        print(json.dumps({key: item.get(key) for key in ("episode", "review_pass", "reviewable_frame_count", "source_sha_bound", "eligible", "blockers")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
