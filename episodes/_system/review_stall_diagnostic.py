"""Read-only Final Semantic recovery diagnosis; never grants Review Authority.

A candidate file, including one that says 'passed', is *not* proof of a
completed model turn or committed Review. This tool never dispatches a model,
consumes an Attempt, modifies a queue, or writes an Episode file.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def diagnose(ep: Path, attempt: int = 1) -> dict:
    if not isinstance(attempt, int) or attempt < 1 or attempt > 3:
        raise ValueError("REVIEW_ATTEMPT_OUT_OF_BOUNDS")
    root = Path(ep).resolve()
    candidate = root / "meta/.frame-semantic-review.candidate.json"
    pending = root / "meta" / f"frame-semantic-pending-attempt-{attempt}.json"
    log = root / "meta" / f"frame-semantic-critic-attempt-{attempt}.jsonl"
    receipts_dir = root / "meta/provider-receipts/model-executions"
    commits_dir = root / "meta/runtime/review-commits"
    # Presence/size only: no candidate 'pass' bit becomes authoritative.
    receipts = 0
    if receipts_dir.is_dir():
        for path in receipts_dir.glob("*.json"):
            try:
                receipt = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            if isinstance(receipt, dict) and receipt.get("model_role") == "vision.final":
                receipts += 1
    commits = sum(1 for _ in commits_dir.glob("*.json")) if commits_dir.is_dir() else 0
    log_bytes = log.stat().st_size if log.is_file() else 0
    if commits:
        code = "FINAL_SEMANTIC_COMMIT_REQUIRES_AUTHORITY_VERIFICATION"
        action = "VERIFY_CANONICAL_REVIEW_COMMIT"
    elif candidate.is_file() and receipts == 0:
        code = "FINAL_SEMANTIC_CANDIDATE_UNVERIFIED"
        action = "INSPECT_DURABLE_CRITIC_RESULT_BEFORE_RETRY"
    elif pending.is_file() and receipts == 0:
        code = "FINAL_SEMANTIC_PENDING_NO_MODEL_RECEIPT"
        action = "VERIFY_CRITIC_PROCESS_AND_DURABLE_RESULT"
    elif receipts:
        code = "FINAL_SEMANTIC_EXECUTION_RECEIPT_REQUIRES_REVIEW_COMMIT"
        action = "VERIFY_CANONICAL_REVIEW_COMMIT"
    else:
        code = "FINAL_SEMANTIC_NO_REVIEW_EVIDENCE"
        action = "CHECK_REVIEW_QUEUE_ADMISSION"
    return {"status": "UNVERIFIED", "code": code, "recovery_action": action,
            "attempt": attempt, "candidate_present": candidate.is_file(),
            "pending_present": pending.is_file(), "critic_log_bytes": log_bytes,
            "vision_final_receipt_count": receipts, "review_commit_manifest_count": commits,
            "review_authority_granted": False, "model_dispatch_performed": False}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir", type=Path)
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(diagnose(args.episode_dir, args.attempt), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
