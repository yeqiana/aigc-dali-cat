#!/usr/bin/env python3
"""Read-only Final Semantic Runner-result locator; never authorizes model retry.

Use through the configured StoryOS environment:
python scripts/storyos_production_env.py scripts/storyos_review_execution_evidence_audit.py --episode <path>
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_user_runner
import review_queue
import scheduler_core


def audit(episode: Path) -> dict:
    episode = Path(episode).resolve()
    legal = (ROOT / "episodes").resolve()
    test_only = (ROOT / ".codex_tmp" / "phase5a").resolve()
    if not (episode.is_relative_to(legal) or episode.is_relative_to(test_only)):
        raise ValueError("REVIEW_EVIDENCE_EPISODE_SCOPE_INVALID")
    if not episode.is_dir():
        raise FileNotFoundError(episode)
    queue = scheduler_core.load_queue(episode)
    records = []
    for row in queue.get(review_queue.QUEUE_KEY) or []:
        if not isinstance(row, dict) or row.get("review_kind") != review_queue.FINAL_SEMANTIC:
            continue
        request_id = str(row.get("runner_request_id") or "").strip()
        verdict = "LEGACY_NO_PREDISPATCH_RUNNER_ID"
        result_present = False
        turn_completed = False
        result_rc = None
        if request_id:
            try:
                durable = codex_user_runner.read_task_result(request_id)
            except (OSError, ValueError, TypeError):
                durable = {}
                verdict = "RUNNER_RESULT_READ_FAILED"
            else:
                verdict = "NO_DURABLE_RUNNER_RESULT"
            if durable:
                result_present = True
                if str(durable.get("request_id") or "") != request_id:
                    verdict = "RUNNER_RESULT_ID_MISMATCH"
                else:
                    try:
                        result_rc = int(durable["returncode"])
                        output = base64.b64decode(
                            str(durable.get("output_base64") or ""), validate=True
                        ).decode("utf-8-sig", errors="replace")
                        events = []
                        for line in output.splitlines():
                            try:
                                event = json.loads(line)
                            except (TypeError, ValueError):
                                continue
                            if isinstance(event, dict):
                                events.append(event)
                        turn_completed = any(
                            event.get("type") == "turn.completed" for event in events
                        )
                        if result_rc == 0 and turn_completed:
                            # ONLY a potential adoption candidate. The real
                            # Review Authority still checks all source hashes,
                            # policy identity and signed/committed receipts.
                            verdict = "RUNNER_TERMINAL_CANDIDATE_REQUIRE_OFFICIAL_RECONCILIATION"
                        else:
                            verdict = "RUNNER_TERMINAL_NOT_VERIFIED"
                    except (KeyError, TypeError, ValueError, OverflowError):
                        verdict = "RUNNER_RESULT_INVALID"
        records.append({
            "frame": row.get("frame"),
            "queue_status": row.get("status"),
            "review_kind": review_queue.FINAL_SEMANTIC,
            "predispatch_runner_id_present": bool(request_id),
            "runner_request_id": request_id or None,
            "durable_runner_result_present": result_present,
            "runner_returncode": result_rc,
            "turn_completed": turn_completed,
            "official_queue_receipt_present": isinstance(row.get("receipt"), dict),
            "evidence_verdict": verdict,
            "automatic_retry_permitted": False,
            "review_outcome_promoted": False,
        })
    return {
        "schema_version": 1,
        "read_only": True,
        "generation_called": False,
        "critic_called": False,
        "review_authority_mutated": False,
        "final_semantic": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    episode = Path(args.episode)
    if not episode.is_absolute():
        episode = ROOT / episode
    print(json.dumps(audit(episode), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
