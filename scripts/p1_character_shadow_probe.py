#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only Character Finalize shadow probe against a real Episode authority.

prepare:
  Reads the Episode through canonical authority APIs and writes an isolated
  capsule under .storyos/tmp. It does not mutate the Episode.

validate:
  Validates an independently authored shadow Candidate against the frozen task,
  compares it with the current canonical character.finalize payload, and proves
  the source authority hashes did not change.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import agent_shadow_compare
import character_contract
import character_visual_contract
import episode_state_persistence
import preimage_authority_snapshot
import preimage_task_contract
import story_json

DEFAULT_CAPSULE = ROOT / ".storyos/tmp/p1-character-shadow-input.json"
DEFAULT_CANDIDATE = ROOT / ".storyos/tmp/p1-character-shadow-candidate.json"
DEFAULT_REPORT = ROOT / "reports/p1-character-shadow-probe-20260926.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _canonical_sha(value) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _source_fingerprint(ep: Path) -> dict:
    gates = story_json.read_json(ep / "meta/story-gates.json", default={}) or {}
    return {
        "episode_state": (episode_state_persistence.load(ep) or {}).get("current_state"),
        "story_gates_sha256": _canonical_sha(gates),
        "character_contract_sha256": character_contract.authority_sha256(ep),
        "character_visual_contract_sha256": character_visual_contract.authority_sha256(ep),
    }


def prepare(ep: Path, capsule_path: Path) -> dict:
    ep = ep.resolve()
    before = _source_fingerprint(ep)
    snapshot = preimage_authority_snapshot.build(ep, write=False)
    task = preimage_task_contract.task_contract(
        ep, "CHARACTER_FINALIZE", snapshot, resume=True
    )
    gates = story_json.read_json(ep / "meta/story-gates.json", default={}) or {}
    canonical_payload = ((gates.get("character") or {}).get("finalize") or {})
    if not isinstance(canonical_payload, dict) or not canonical_payload:
        raise ValueError("current Episode has no canonical character.finalize payload")
    cc = character_contract.load(ep) or {}
    cv = character_visual_contract.load(ep) or {}
    after = _source_fingerprint(ep)
    if before != after:
        raise RuntimeError("read-only prepare changed Episode authority fingerprint")
    capsule = {
        "schema_version": 1,
        "kind": "p1_character_finalize_shadow_probe",
        "prepared_at": now(),
        "source_episode": ep.relative_to(ROOT).as_posix(),
        "source_fingerprint_before": before,
        "source_fingerprint_after": after,
        "snapshot_id": snapshot["snapshot_id"],
        "task": task,
        "agent_instruction": {
            "role": "Character Finalize shadow producer",
            "candidate_only": True,
            "must_not_write_episode": True,
            "must_use_task_ids_exactly": True,
            "output_schema": {
                "schema_version": 1,
                "task_id": task["task_id"],
                "task_type": "CHARACTER_FINALIZE",
                "snapshot_id": task["snapshot_id"],
                "source_authority_sha256": task["input_contract"]["source_authority_sha256"],
                "generated_at": "ISO8601",
                "status": "COMPLETED",
                "payload": {
                    "character.finalize": {
                        "character": "object",
                        "identity": "object",
                        "pov": "object",
                        "appearance": "object",
                    }
                },
                "authority_scope": ["character.finalize"],
                "evidence": [],
                "verification": {"gate_pass": None},
                "model_execution": {
                    "independent_task": True,
                    "shadow": True,
                    "canonical_write": False,
                    "real_model_execution": True,
                    "wall_seconds": "provider-measured number",
                    "input_tokens": "provider-measured int",
                    "output_tokens": "provider-measured int",
                    "repeated_reads": "observed int",
                    "failure": False,
                    "timeout": False,
                    "provider": "provider id",
                    "model": "model id",
                    "telemetry_source": "provider receipt or host execution telemetry",
                },
            },
        },
        "authority_inputs": {
            "character_contract": cc,
            "character_visual_contract": cv,
            "runtime_request_preimage": (task.get("input_contract") or {}).get(
                "runtime_request_preimage"
            ),
        },
        "canonical_comparison_reference": {
        "telemetry_contract": {
            "required_for_p1_cutover": [
                "real_model_execution", "wall_seconds", "input_tokens", "output_tokens",
                "repeated_reads", "failure", "timeout", "provider", "model", "telemetry_source"
            ],
            "missing_values_must_not_be_estimated": True,
        },
            "payload_sha256": _canonical_sha(canonical_payload),
            "field_names": sorted(canonical_payload.keys()),
        },
    }
    capsule_path.parent.mkdir(parents=True, exist_ok=True)
    capsule_path.write_text(
        json.dumps(capsule, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return capsule


def validate(ep: Path, capsule_path: Path, candidate_path: Path, report_path: Path) -> dict:
    ep = ep.resolve()
    capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    task = capsule["task"]
    verifier_errors = preimage_task_contract.verify_candidate(candidate, task)
    gates = story_json.read_json(ep / "meta/story-gates.json", default={}) or {}
    canonical_payload = ((gates.get("character") or {}).get("finalize") or {})
    legacy = preimage_task_contract.candidate_template(
        task, {"character.finalize": canonical_payload}
    )
    comparison = agent_shadow_compare.compare_preimage_candidates(
        task, legacy, candidate
    )
    after = _source_fingerprint(ep)
    source_unchanged = (
        after == capsule.get("source_fingerprint_before")
        == capsule.get("source_fingerprint_after")
    )
    report = {
        "schema_version": 1,
        "kind": "p1_character_finalize_shadow_probe_result",
        "generated_at": now(),
        "source_episode": capsule["source_episode"],
        "snapshot_id": task["snapshot_id"],
        "candidate_path": candidate_path.relative_to(ROOT).as_posix(),
        "candidate_sha256": _canonical_sha(candidate),
        "verifier_errors": verifier_errors,
        "comparison": comparison,
        "source_authority_unchanged": source_unchanged,
        "source_fingerprint_after_validation": after,
        "production_cutover_allowed": False,
        "note": (
            "This probe measures real-authority shadow compatibility only. "
            "It is not a production cutover and does not mutate Episode authority."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "validate"):
        p = sub.add_parser(name)
        p.add_argument("episode_dir")
        p.add_argument("--capsule", default=str(DEFAULT_CAPSULE))
        if name == "validate":
            p.add_argument("--candidate", default=str(DEFAULT_CANDIDATE))
            p.add_argument("--report", default=str(DEFAULT_REPORT))
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    capsule = Path(args.capsule).resolve()
    if args.cmd == "prepare":
        row = prepare(ep, capsule)
        print(json.dumps({
            "capsule": capsule.relative_to(ROOT).as_posix(),
            "snapshot_id": row["snapshot_id"],
            "source_authority_unchanged": (
                row["source_fingerprint_before"] == row["source_fingerprint_after"]
            ),
        }, ensure_ascii=False, indent=2))
        return 0
    report = validate(
        ep,
        capsule,
        Path(args.candidate).resolve(),
        Path(args.report).resolve(),
    )
    return 0 if not report["verifier_errors"] and report["source_authority_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
