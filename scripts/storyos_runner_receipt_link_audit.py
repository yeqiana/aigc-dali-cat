#!/usr/bin/env python3
"""Read-only reconciliation of failed model receipts with durable Runner results.

Never prints request IDs, payloads, logs, errors, user identity or credentials.
A matching durable result NEVER authorizes retry or promotes Review Authority.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REL = Path("meta/provider-receipts/model-executions")
_SAFE_LABEL = re.compile(r"^[a-zA-Z0-9_.-]{1,80}$")


def _safe_label(value: object) -> str:
    text = str(value or "")
    return text if _SAFE_LABEL.fullmatch(text) else "UNKNOWN"


def inspect(episode: Path, *, read_durable=None) -> dict:
    ep = Path(episode).resolve()
    if not ep.is_dir():
        raise ValueError("Episode directory does not exist")
    if read_durable is None:
        system = str(Path(__file__).resolve().parents[1] / "episodes" / "_system")
        if system not in sys.path:
            sys.path.insert(0, system)
        import codex_user_runner
        read_durable = codex_user_runner.read_task_result
    rows = []
    malformed = 0
    counts = Counter()
    for path in sorted((ep / REL).glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, ValueError):
            malformed += 1
            continue
        if not isinstance(row, dict):
            malformed += 1
            continue
        status = str(row.get("status") or "").upper()
        if status not in {"FAILED", "TIMEOUT"}:
            continue
        request_id = row.get("runner_request_id")
        if not request_id:
            state = "RUNNER_ID_ABSENT"
        else:
            try:
                durable = read_durable(str(request_id))
            except Exception:
                durable = {}
            if not isinstance(durable, dict) or not durable:
                state = "DURABLE_NOT_RESOLVED"
            elif str(durable.get("request_id") or "") != str(request_id):
                state = "DURABLE_ID_MISMATCH"
            elif durable.get("returncode") == 0:
                state = "DURABLE_ZERO_RC_NEEDS_AUTHORITY_VERIFY"
            elif isinstance(durable.get("returncode"), int):
                state = "DURABLE_NONZERO_RC"
            else:
                state = "DURABLE_INCOMPLETE"
        counts[state] += 1
        rows.append({
            "role": _safe_label(row.get("model_role")),
            "step": _safe_label(row.get("step")),
            "status": status,
            "runner_link_state": state,
        })
    return {
        "schema_version": 1,
        "diagnostic_only": True,
        "production_authority_changed": False,
        "model_calls": 0,
        "malformed_receipts": malformed,
        "failed_or_timed_out_receipts": len(rows),
        "link_state_counts": dict(sorted(counts.items())),
        "rows": rows,
        "automatic_retry_allowed": False,
        "durable_success_promoted_to_review": False,
        "limitations": [
            "no runner request ID does not prove absence of Runner evidence",
            "returncode zero does not prove candidate SHA, Stage or Review Authority",
            "request IDs, credentials and task outputs are deliberately suppressed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.episode_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
