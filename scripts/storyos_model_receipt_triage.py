#!/usr/bin/env python3
"""Read-only diagnosis of observed FAILED/TIMEOUT model execution receipts.

Reports only whitelisted structural fields. Never prints prompts, error text,
model call payloads, authorization headers or any Episode content.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

REL = Path("meta/provider-receipts/model-executions")
INTERESTING = frozenset({"FAILED", "TIMEOUT"})


def inspect(episode: Path) -> dict:
    ep = Path(episode).resolve()
    if not ep.is_dir():
        raise ValueError("Episode directory does not exist")
    rows = []
    observed = 0
    malformed = 0
    for path in sorted((ep / REL).glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError, UnicodeError):
            malformed += 1
            continue
        if not isinstance(row, dict) or not row.get("call_id"):
            malformed += 1
            continue
        observed += 1
        status = str(row.get("status") or "UNKNOWN").upper()
        if status not in INTERESTING:
            continue
        raw = row.get("duration_ms")
        duration = (round(float(raw), 3) if isinstance(raw, (int, float))
                    and not isinstance(raw, bool) and math.isfinite(raw) and raw >= 0 else None)
        # A 900 second cluster is an observation, not proof of a policy cause.
        near_900 = bool(duration is not None and 899000 <= duration <= 901000)
        rows.append({
            "model_role": str(row.get("model_role") or "UNKNOWN"),
            "step": str(row.get("step") or "UNKNOWN"),
            "status": status,
            "duration_ms": duration,
            "near_900_seconds": near_900,
            "failure_class_present": bool(row.get("failure_class")),
            "error_code_present": bool(row.get("error_code")),
        })
    rows.sort(key=lambda r: (r["step"], r["status"], r["duration_ms"] or -1))
    counts = Counter(r["status"] for r in rows)
    return {
        "schema_version": 1,
        "evidence_only": True,
        "queries_mysql": False,
        "calls_model": False,
        "receipts_observed": observed,
        "malformed_receipts": malformed,
        "failure_count": len(rows),
        "failures_by_status": dict(sorted(counts.items())),
        "near_900_seconds_count": sum(r["near_900_seconds"] for r in rows),
        "error_classification_coverage": sum(r["failure_class_present"] or r["error_code_present"] for r in rows),
        "failure_rows": rows,
        "root_cause_determined": False,
        "caveat": "Observed timing does not identify timeout policy, provider outcome, or retry safety.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.episode_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
