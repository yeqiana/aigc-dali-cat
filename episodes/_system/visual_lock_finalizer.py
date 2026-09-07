#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 Visual Lock Finalizer.

Collects existing Visual Lock evidence and produces a final verification report.
This module does not create new visual approvals; it only aggregates evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


REPORT = Path("meta/visual-lock-final-report.json")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build(ep: Path):
    baseline = read_json(ep / "meta/visual-lock-baseline-review.json")
    plan = read_json(ep / "meta/visual-lock-plan.json")
    gates = read_json(ep / "meta/story-gates.json")
    calibration = ((gates.get("visual") or {}).get("calibration") or {}).get("items") or []
    calibration_by_frame = {int(x.get("frame")): x for x in calibration if x.get("frame") is not None}

    roles = [
        item.get("role")
        for item in plan.get("items", [])
    ]

    required = {
        "ordinary_baseline",
        "worst_capture_condition",
        "first_major_anomaly",
        "high_impact_admission",
    }

    checks = {
        "baseline_review": baseline.get("decision") == "PASS",
        "four_admission_roles": required.issubset(set(roles)),
        "visual_lock_plan_exists": True,
    }

    passed = all(checks.values())

    report = {
        "schema_version": 1,
        "runtime": "Story OS V2.7",
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(),
        "stage": "VISUAL_LOCK_FINAL_VERIFY",
        "episode": ep.name,
        "decision": "PASS" if passed else "FAIL",
        "checks": checks,
        "frames": [
            {
                "frame": item.get("frame"),
                "role": item.get("role"),
                "asset_path": calibration_by_frame.get(int(item.get("frame")), {}).get("asset_path"),
                "sha256": calibration_by_frame.get(int(item.get("frame")), {}).get("sha256"),
                "contract_sha256": item.get("contract_sha256"),
                "frame_contract_sha256": calibration_by_frame.get(int(item.get("frame")), {}).get("frame_contract_sha256"),
            }
            for item in plan.get("items", [])
        ],
        "next_stage": "VISUAL_CALIBRATED" if passed else None,
    }

    write_json(ep / REPORT, report)
    return report


def verify(ep: Path):
    p = ep / REPORT
    if not p.exists():
        return ["visual-lock-final-report missing"]
    data = read_json(p)
    errors = []
    if data.get("decision") != "PASS":
        errors.append("final visual lock decision is not PASS")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("episode")
    args = parser.parse_args()
    ep = Path(args.episode).resolve()
    if args.command == "build":
        print(json.dumps(build(ep), ensure_ascii=False, indent=2))
    else:
        errors = verify(ep)
        print("PASS" if not errors else "\n".join(errors))


if __name__ == "__main__":
    main()
