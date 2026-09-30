#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from story_os_contract import canonical_stages
import story_json
import episode_state_persistence
import story_review
import visual_profile_review_persistence
import production_ledger
import runtime_command
import evidence_reuse
import model_policy_persistence

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
STATES = canonical_stages()


def run(args: list[object]) -> tuple[int, str]:
    cp = runtime_command.run_argv([str(x) for x in args], cwd=ROOT, capture=True)
    return cp.returncode, cp.stdout


def read_json(path: Path) -> dict:
    return story_json.read_json(path, default={})


def current_state(ep: Path) -> str:
    return str((episode_state_persistence.load(ep) or {}).get("current_state") or "UNKNOWN")


def state_at_least(state: str, target: str) -> bool:
    return state in STATES and STATES.index(state) >= STATES.index(target)


def command_ok(script: str, subcommand: str, ep: Path, *extra: str) -> tuple[bool, str]:
    rc, out = run([sys.executable, SYSTEM / script, subcommand, ep, *extra])
    return rc == 0, out[-2500:]


def subtitle_required(ep: Path) -> bool:
    gates = read_json(ep / "meta/story-gates.json")
    value = ((gates.get("subtitles") or {}).get("required"))
    return value is not False


def _bound_policy_sha(ep: Path, role: str) -> str | None:
    try:
        bound = model_policy_persistence.load(Path(ep).resolve())
        if not isinstance(bound, dict):
            return None
        policy = bound.get("policy") if isinstance(bound.get("policy"), dict) else bound
        profile_name = (policy.get("role_aliases") or {}).get(role)
        if not profile_name or not isinstance((policy.get("profiles") or {}).get(profile_name), dict):
            return None
        value = policy.get("policy_sha256")
        return str(value).strip().lower() if value else None
    except Exception:
        return None


def _review_reuse_detail(
    *,
    ep: Path,
    evidence: dict,
    evidence_type: str,
    role: str,
    source_artifact_sha: str | None,
    source_contract_sha: str | None,
    relevant_context_sha: str | None,
    schema_version: str | int | None,
    verify_ok: bool,
) -> dict:
    """A valid current review is reusable only when its frozen policy identity is recorded."""
    policy_sha = _bound_policy_sha(ep, role)
    # Resolve only the Episode-bound policy; no global config fallback is used.
    if not policy_sha:
        policy_sha = None
    identity = {
        "evidence_type": evidence_type,
        "source_artifact_sha": source_artifact_sha,
        "source_contract_sha": source_contract_sha,
        "relevant_context_sha": relevant_context_sha,
        "bound_model_policy_sha": policy_sha,
        "review_schema_version": schema_version,
    }
    validation = evidence_reuse.validate_reusable(
        evidence,
        expected=identity,
        verify_errors=[] if verify_ok else ["formal verifier rejected evidence"],
    )
    provenance = evidence.get("critic_provenance") if isinstance(evidence.get("critic_provenance"), dict) else {}
    recorded_policy_sha = (evidence.get("model_policy_sha256") or
                           provenance.get("model_policy_sha256"))
    old_fingerprint = evidence_reuse.compute_fingerprint(
        evidence_type=evidence_type,
        source_artifact_sha=evidence.get("source_artifact_sha"),
        source_contract_sha=evidence.get("source_contract_sha"),
        relevant_context_sha=evidence.get("relevant_context_sha"),
        bound_model_policy_sha=recorded_policy_sha,
        review_schema_version=evidence.get("schema_version"),
    )
    if not policy_sha:
        validation["reusable"] = False
        validation["reasons"] = list(dict.fromkeys(["BOUND_POLICY_SHA_UNAVAILABLE", *validation["reasons"]]))
    return {
        "state": "CLEAN" if validation["reusable"] else "DIRTY",
        "action": "REUSE" if validation["reusable"] else "VERIFY",
        "reason": "PASS_FINGERPRINT_MATCH" if validation["reusable"] else validation["reasons"],
        "evidence_fingerprint": validation["fingerprint"],
        "old_fingerprint": old_fingerprint,
        "new_fingerprint": validation["fingerprint"],
        "policy_sha256": policy_sha,
    }


def plan(ep: Path) -> dict:
    state = current_state(ep)
    result: dict = {
        "episode": ep.relative_to(ROOT).as_posix(),
        "state": state,
        "story": "NOT_APPLICABLE",
        "visual": "NOT_APPLICABLE",
        "frames": "NOT_APPLICABLE",
        "frame_plan": None,
        "subtitle": "NOT_APPLICABLE",
        "action": "RUN_WORKER",
        "missing": [],
        "details": {},
        "evidence_plan": {},
        "dirty_frames": [],
        "reused_frames": [],
        "context_frames": [],
        "missing_evidence_frames": [],
        "summary": {
            "reusable_evidence_count": 0,
            "recompute_evidence_count": 0,
            "missing_evidence_count": 0,
            "full_review_count": 0,
            "patch_review_count": 0,
        },
    }

    story_data = story_review.load_review(ep)
    if isinstance(story_data, dict):
        ok, _ = command_ok("story_review.py", "verify", ep)
        story_identity = evidence_reuse.compute_fingerprint(
            evidence_type="STORY_SEMANTIC",
            source_artifact_sha=story_data.get("story_sha256"),
            source_contract_sha=story_data.get("storyboard_sha256"),
            relevant_context_sha=story_data.get("story_os_version"),
            bound_model_policy_sha=_bound_policy_sha(ep, "critic.story"),
            review_schema_version=story_data.get("schema_version"),
        )
        # Translate the validated, established Story Review source bindings into
        # the common identity shape; the receipt still must carry the frozen
        # Model Policy SHA to become reusable.
        normalized_story = dict(story_data)
        normalized_story["source_artifact_sha"] = story_data.get("story_sha256")
        normalized_story["source_contract_sha"] = story_data.get("storyboard_sha256")
        normalized_story["relevant_context_sha"] = story_data.get("story_os_version")
        detail = _review_reuse_detail(
            ep=ep,
            evidence=normalized_story,
            evidence_type="STORY_SEMANTIC",
            role="critic.story",
            source_artifact_sha=story_data.get("story_sha256"),
            source_contract_sha=story_data.get("storyboard_sha256"),
            relevant_context_sha=story_data.get("story_os_version"),
            schema_version=story_data.get("schema_version"),
            verify_ok=ok,
        )
        detail["evidence_fingerprint"] = story_identity
        result["details"]["story"] = detail
        result["story"] = detail["state"]
        result["summary"]["reusable_evidence_count"] += int(detail["state"] == "CLEAN")
        result["summary"]["recompute_evidence_count"] += int(detail["state"] != "CLEAN")
    elif state_at_least(state, "STORYBOARD_LOCKED"):
        result["story"] = "MISSING"; result["missing"].append("meta/story-semantic-review.json")
        result["details"]["story"] = {
            "state": "MISSING", "action": "GENERATE_EVIDENCE", "reason": "MISSING_EVIDENCE"
        }
        result["summary"]["missing_evidence_count"] += 1

    visual_data = visual_profile_review_persistence.load(ep)
    if isinstance(visual_data, dict):
        ok, _ = command_ok("visual_review.py", "verify", ep)
        profile_sha = visual_data.get("profile_sha256")
        calibration_sha = evidence_reuse.canonical_sha256([
            {
                "id": row.get("id"),
                "sha256": row.get("sha256"),
                "frame_contract_sha256": row.get("frame_contract_sha256"),
            }
            for row in (visual_data.get("calibration") or [])
            if isinstance(row, dict)
        ])
        visual_context_sha = str(visual_data.get("story_os_version") or "")
        normalized_visual = dict(visual_data)
        normalized_visual["source_artifact_sha"] = calibration_sha
        normalized_visual["source_contract_sha"] = profile_sha
        normalized_visual["relevant_context_sha"] = visual_context_sha
        detail = _review_reuse_detail(
            ep=ep,
            evidence=normalized_visual,
            evidence_type="VISUAL_PROFILE",
            role="vision.visual_lock",
            source_artifact_sha=calibration_sha,
            source_contract_sha=profile_sha,
            relevant_context_sha=visual_context_sha,
            schema_version=visual_data.get("schema_version"),
            verify_ok=ok,
        )
        result["details"]["visual"] = detail
        result["visual"] = detail["state"]
        result["summary"]["reusable_evidence_count"] += int(detail["state"] == "CLEAN")
        result["summary"]["recompute_evidence_count"] += int(detail["state"] != "CLEAN")
    elif state_at_least(state, "VISUAL_CALIBRATED"):
        result["visual"] = "MISSING"; result["missing"].append("meta/visual-profile-review.json")
        result["details"]["visual"] = {
            "state": "MISSING", "action": "GENERATE_EVIDENCE", "reason": "MISSING_EVIDENCE"
        }
        result["summary"]["missing_evidence_count"] += 1

    ledger_data = production_ledger.load_authority(ep, default=None)
    if isinstance(ledger_data, dict):
        rc, out = run([sys.executable, SYSTEM / "incremental_frame_review.py", "plan", ep])
        if rc == 0:
            try:
                fp = json.loads(out)
            except Exception:
                fp = {"action": "ERROR", "raw": out[-1000:]}
            result["frame_plan"] = fp
            if fp.get("action") == "ERROR":
                result["frames"] = "ERROR"
            else:
                result["frames"] = "CLEAN" if fp.get("action") in {"NOOP", "NOT_REQUIRED"} else "DIRTY"
                dirty = list(fp.get("dirty_frames") or fp.get("selected_frames") or [])
                reused = list(fp.get("reused_frames") or [])
                contexts = list(fp.get("context_frames") or [])
                missing_frames = list(fp.get("missing_evidence_frames") or [])
                fp.setdefault("dirty_frames", dirty)
                fp.setdefault("reused_frames", reused)
                fp.setdefault("context_frames", contexts)
                fp.setdefault("missing_evidence_frames", missing_frames)
                result["summary"]["reusable_evidence_count"] += len(reused)
                result["summary"]["recompute_evidence_count"] += len(dirty)
                result["dirty_frames"] = dirty
                result["reused_frames"] = reused
                result["context_frames"] = contexts
                result["missing_evidence_frames"] = missing_frames
                result["summary"]["full_review_count"] = int(fp.get("action") == "FULL")
                result["summary"]["patch_review_count"] = int(fp.get("action") == "PATCH")
        else:
            result["frames"] = "ERROR"
            result["frame_plan"] = {"action": "ERROR", "returncode": rc, "raw": out[-1500:]}
    elif state_at_least(state, "PRODUCTION_PASSED"):
        result["frames"] = "MISSING"; result["missing"].append("meta/production-ledger.json")
        result["details"]["frames"] = {
            "state": "MISSING", "action": "GENERATE_EVIDENCE", "reason": "MISSING_EVIDENCE"
        }
        result["summary"]["missing_evidence_count"] += 1

    audit = ep / "meta/subtitle-layout-audit.json"
    if subtitle_required(ep):
        if audit.is_file():
            ok, _ = command_ok("subtitle_layout.py", "audit", ep)
            result["subtitle"] = "CLEAN" if ok else "DIRTY"
            result["details"]["subtitle"] = {
                "state": result["subtitle"],
                "action": "REUSE" if ok else "VERIFY",
                "reason": "AUDIT_PASS" if ok else "AUDIT_INVALID",
            }
            result["summary"]["reusable_evidence_count"] += int(ok)
            result["summary"]["recompute_evidence_count"] += int(not ok)
        elif state_at_least(state, "PUBLISH_READY"):
            result["subtitle"] = "MISSING"; result["missing"].append("meta/subtitle-layout-audit.json")
            result["details"]["subtitle"] = {
                "state": "MISSING", "action": "GENERATE_EVIDENCE", "reason": "MISSING_EVIDENCE"
            }
            result["summary"]["missing_evidence_count"] += 1
    else:
        result["subtitle"] = "NOT_APPLICABLE"

    ordered = [result["story"], result["visual"], result["frames"], result["subtitle"]]
    if "ERROR" in ordered:
        result["action"] = "ERROR"
    elif "MISSING" in ordered:
        result["action"] = "MISSING_EVIDENCE"
    elif result["story"] == "DIRTY":
        result["action"] = "STORY_REVIEW_REQUIRED"
    elif result["visual"] == "DIRTY":
        result["action"] = "VISUAL_REVIEW_REQUIRED"
    elif result["frames"] == "DIRTY":
        result["action"] = "PRODUCTION_INCREMENTAL_REQUIRED"
    elif result["subtitle"] == "DIRTY":
        result["action"] = "SUBTITLE_REVIEW_REQUIRED"
    else:
        clean_core = all(x in {"CLEAN", "NOT_APPLICABLE"} for x in (result["story"], result["visual"], result["frames"]))
        release_ready = result["subtitle"] in {"CLEAN", "NOT_APPLICABLE"}
        if clean_core and release_ready and state in {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}:
            result["action"] = "POSTFLIGHT_ONLY"
        elif clean_core and release_ready and state == "PRODUCTION_PASSED":
            # Only safe when release text/subtitle evidence already exists.
            result["action"] = "POSTFLIGHT_ONLY" if (ep / "meta/text-audit.json").is_file() else "RUN_WORKER"
        else:
            result["action"] = "RUN_WORKER"
    for key in ("story", "visual", "frames", "subtitle"):
        state_value = result[key]
        detail = result["details"].get(key)
        if not isinstance(detail, dict):
            detail = {
                "state": state_value,
                "action": "NOT_REQUIRED" if state_value == "NOT_APPLICABLE" else "VERIFY",
                "reason": "NOT_APPLICABLE" if state_value == "NOT_APPLICABLE" else "PLANNER_RESULT",
            }
        result["evidence_plan"][key] = detail
    result["summary"]["missing_evidence_count"] = max(
        result["summary"]["missing_evidence_count"],
        len(result["missing"]) + len(result["missing_evidence_frames"]),
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Story OS V2.1 state-aware minimal-closure planner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("episode_dir"); p.add_argument("--json", action="store_true")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        assert state_at_least("PUBLISH_READY", "STORYBOARD_LOCKED")
        assert not state_at_least("IDEA_LOCKED", "STORYBOARD_LOCKED")
        print("INCREMENTAL CLOSURE V2.1 SELF-TEST PASS")
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    result = plan(ep)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Planner/inner-action failure is technical failure. Returning 0 here lets
    # runtime_dag record the outer INCREMENTAL_PLAN step as PASS, which is false.
    return 4 if result.get("action") == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
