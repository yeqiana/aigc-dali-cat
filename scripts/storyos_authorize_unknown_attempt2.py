#!/usr/bin/env python3
"""Record explicit, auditable authorization for one image Attempt 2.

Invoke only through scripts/storyos_production_env.py. This command writes one
new recovery authorization row; it never changes old Attempt/Receipt state and
never starts Scheduler or Provider work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import generation_unknown_recovery


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode")
    parser.add_argument("logical_asset_key")
    parser.add_argument("--authorized-by", required=True)
    parser.add_argument("--risk-assessment", required=True)
    parser.add_argument("--evidence-json", required=True, type=Path)
    parser.add_argument("--authorization-id")
    parser.add_argument("--authorize-attempt-2", action="store_true", required=True)
    parser.add_argument("--acknowledge-possible-duplicate-charge", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        evidence = json.loads(args.evidence_json.read_text(encoding="utf-8"))
        result = generation_unknown_recovery.authorize_attempt_two(
            args.episode, args.logical_asset_key,
            authorized_by=args.authorized_by, risk_assessment=args.risk_assessment,
            evidence=evidence,
            acknowledge_possible_duplicate_charge=args.acknowledge_possible_duplicate_charge,
            authorization_id=args.authorization_id)
    except Exception as exc:
        code = str(exc) if isinstance(exc, (ValueError, generation_unknown_recovery.UnknownRecoveryDenied)) else "AUTHORITY_WRITE_FAILED"
        print(f"UNKNOWN_RECOVERY_AUTHORIZATION_BLOCKED:{code}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
