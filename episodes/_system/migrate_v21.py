#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 9 migration/compatibility inspector.

Default behavior is READ-ONLY for existing episodes.
Legacy episodes are never upgraded by fabricating V2.1 evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Iterable

from story_os_contract import story_os_version

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "story-os-v21-migration-report.json"
MIN_V21 = (2, 1, 0)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)


def resolve_ep(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep


def discover() -> Iterable[Path]:
    root = ROOT / "episodes"
    if not root.is_dir():
        return []
    rows = []
    for state in root.rglob("meta/episode-state.json"):
        if "_system" in state.parts:
            continue
        rows.append(state.parents[1])
    return sorted(set(rows))


def detected_version(ep: Path) -> str:
    versions: list[tuple[tuple[int, ...], str]] = []
    for rel in ("meta/episode-state.json", "meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    return max(versions, key=lambda x: x[0])[1] if versions else "unversioned"


def evidence_presence(ep: Path) -> dict:
    checks = {
        "concept_ambition": "meta/concept-ambition-review.json",
        "environment_contract": "meta/story-gates.json",
        "frame_contract_index": "meta/runtime/contracts/frame-contract-index.json",
        "visual_lock_v21": "meta/visual-profile-review.json",
        "production_queue": "meta/production-queue.json",
        "fast_scout": "meta/frame-scout-summary.json",
        "final_snapshot": "meta/final-candidate-snapshot.json",
        "publish_event": "meta/publish-event.json",
        "post_publish_review": "meta/post-publish-review.json",
    }
    return {name: (ep / rel).is_file() for name, rel in checks.items()}


def classify(ep: Path) -> dict:
    raw_version = detected_version(ep)
    vt = version_tuple(raw_version)
    state_path = ep / "meta/episode-state.json"
    state = read_json(state_path) if state_path.is_file() else {}
    current_state = state.get("current_state")
    if raw_version == "unversioned":
        status = "UNVERSIONED_COMPAT"
        current_policy_required = False
    elif vt < MIN_V21:
        status = "LEGACY_COMPAT"
        current_policy_required = False
    else:
        status = "V21_ACTIVE"
        current_policy_required = True

    gates = read_json(ep / "meta/story-gates.json") if (ep / "meta/story-gates.json").is_file() else {}
    visual = gates.get("visual") or {}
    release = gates.get("release") or {}
    active_policies = {
        "concept_ambition_versioned": vt >= MIN_V21,
        "environment_contract_present": isinstance(visual.get("environment_contract"), dict),
        "frame_directives_present": isinstance(visual.get("frame_directives"), dict),
        "four_admission_visual_lock": ((visual.get("calibration") or {}).get("policy") == "four_admission_v21"),
        "fast_frame_scout": ((visual.get("fast_frame_scout") or {}).get("enabled") is True),
        "final_candidate_snapshot": ((release.get("final_candidate_snapshot") or {}).get("enabled") is True),
    }
    missing_policy = [k for k, v in active_policies.items() if current_policy_required and not v]
    return {
        "episode": ep.relative_to(ROOT).as_posix(),
        "detected_version": raw_version,
        "current_state": current_state,
        "compatibility_status": status,
        "current_v21_policy_required": current_policy_required,
        "automatic_evidence_backfill_allowed": False,
        "active_policies": active_policies,
        "missing_current_policy": missing_policy,
        "evidence_presence": evidence_presence(ep),
        "recommendation": (
            "KEEP_LEGACY_NO_BACKFILL"
            if status in {"LEGACY_COMPAT", "UNVERSIONED_COMPAT"}
            else ("CURRENT_V21_OK" if not missing_policy else "PLAN_EXPLICIT_V21_POLICY_ACTIVATION")
        ),
    }


def scan(write: bool = True) -> dict:
    rows = [classify(ep) for ep in discover()]
    report = {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "generated_at": now(),
        "policy": {
            "legacy_no_evidence_fabrication": True,
            "migration_default_read_only": True,
            "episode_stage_source_unchanged": "meta/episode-state.json",
        },
        "summary": {
            "episodes": len(rows),
            "legacy_compat": sum(x["compatibility_status"] == "LEGACY_COMPAT" for x in rows),
            "unversioned_compat": sum(x["compatibility_status"] == "UNVERSIONED_COMPAT" for x in rows),
            "v21_active": sum(x["compatibility_status"] == "V21_ACTIVE" for x in rows),
            "v21_missing_policy": sum(bool(x["missing_current_policy"]) for x in rows if x["compatibility_status"] == "V21_ACTIVE"),
        },
        "episodes": rows,
    }
    if write:
        write_json(REPORT, report)
    return report


def plan(ep: Path) -> dict:
    row = classify(ep)
    if row["compatibility_status"] != "V21_ACTIVE":
        row["activation_plan"] = {
            "action": "NO_OP",
            "reason": "Legacy/unversioned episode stays on its historical contract. Do not fabricate V2.1 evidence.",
        }
        return row
    row["activation_plan"] = {
        "action": "EXPLICIT_ONLY",
        "missing_policy": row["missing_current_policy"],
        "warning": "Activating a policy can make fresh evidence required. The migration tool will never author PASS evidence.",
    }
    return row


def activate(ep: Path) -> dict:
    row = classify(ep)
    if row["compatibility_status"] != "V21_ACTIVE":
        return {
            "status": "NO_OP",
            "episode": row["episode"],
            "reason": "Legacy/unversioned episode was not mutated.",
        }
    gates_path = ep / "meta/story-gates.json"
    if not gates_path.is_file():
        raise ValueError("V2.1 episode has no meta/story-gates.json; repair structural contract first")
    gates = read_json(gates_path)
    visual = gates.setdefault("visual", {})
    # Config only. NO evidence JSON is created here.
    visual.setdefault("fast_frame_scout", {
        "schema_version": 1,
        "enabled": True,
        "policy": "risk_based_v21",
        "final_critic_still_required": True,
        "high_risk_required": True,
    })
    release = gates.setdefault("release", {})
    release.setdefault("final_candidate_snapshot", {
        "schema_version": 1,
        "enabled": True,
        "delivery_must_consume_snapshot": True,
        "snapshot_is_authority": False,
    })
    post = gates.setdefault("post_publish", {})
    post.setdefault("data_review", {
        "schema_version": 1,
        "enabled": True,
        "checkpoints": ["6h", "24h", "48h", "7d"],
        "required_for_data_reviewed": ["48h"],
        "learning_packet_is_authority": False,
    })
    write_json(gates_path, gates)
    return {
        "status": "POLICY_CONFIG_ACTIVATED",
        "episode": row["episode"],
        "evidence_created": [],
        "note": "No PASS evidence was fabricated. Existing gates may now require honest fresh evidence before later transitions.",
    }


def verify() -> list[str]:
    errors = []
    report = scan(write=True)
    if report["policy"]["legacy_no_evidence_fabrication"] is not True:
        errors.append("legacy no-fabrication policy missing")
    for row in report["episodes"]:
        if row["compatibility_status"] in {"LEGACY_COMPAT", "UNVERSIONED_COMPAT"} and row["current_v21_policy_required"]:
            errors.append(f"{row['episode']}: legacy compatibility classification drift")
    return errors


def self_test() -> None:
    assert version_tuple("2.0.3.6") < MIN_V21
    assert version_tuple("2.1.0") >= MIN_V21
    assert version_tuple("unversioned") == (0,)
    print("MIGRATE V2.1 PHASE9 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    p = sub.add_parser("plan"); p.add_argument("episode_dir")
    p = sub.add_parser("activate"); p.add_argument("episode_dir")
    sub.add_parser("verify")
    sub.add_parser("show")
    sub.add_parser("self-test")
    args = ap.parse_args()
    try:
        if args.cmd == "self-test":
            self_test(); return 0
        if args.cmd == "scan":
            print(json.dumps(scan(write=True), ensure_ascii=False, indent=2)); return 0
        if args.cmd == "show":
            if not REPORT.is_file():
                scan(write=True)
            print(REPORT.read_text(encoding="utf-8")); return 0
        if args.cmd == "verify":
            errors = verify()
            if errors:
                for error in errors: print("FAIL:", error)
                return 2
            print("V2.1 MIGRATION COMPAT VERIFY PASS"); return 0
        ep = resolve_ep(args.episode_dir)
        data = plan(ep) if args.cmd == "plan" else activate(ep)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("MIGRATION ERROR:", exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
