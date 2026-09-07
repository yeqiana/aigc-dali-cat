#!/usr/bin/env python3
"""Production ledger CLI facade (Story OS B4 split).

Domain implementations moved to production_ledger_core (shared library),
production_ledger_run (runtime commands) and production_ledger_manage
(management commands). This facade keeps parser/main and re-exports the full
public surface so existing importers and CLI callers are unaffected.
"""
from __future__ import annotations

from production_ledger_core import *  # noqa: F401,F403  (full public library)
from production_ledger_run import (cmd_authorize_repair, cmd_begin,
    cmd_restore_evidence_gap_review, cmd_review, cmd_success, cmd_tech_fail)
from production_ledger_manage import (cmd_accept_user_exception_candidate,
    cmd_audit, cmd_authorize_authority_refresh, cmd_authorize_user_exception_repair,
    cmd_authorize_user_locked_repair, cmd_authorize_user_passed_repair,
    cmd_batch_begin, cmd_batch_end, cmd_init, cmd_lock, cmd_promote, cmd_show)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Story OS V1.2 Production Engine ledger")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="initialize per-frame ledger; default canvas is 4:5 / 1080x1350")
    s.add_argument("episode_dir")
    s.add_argument("--frame-count", type=int)
    s.add_argument("--aspect-ratio", help="4:5 or 9:16; omitted => manifest, then default 4:5")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("begin", help="record generation preflight and request fingerprint")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--kind", choices=["original", "repair"], default="original")
    s.add_argument("--prompt")
    s.add_argument("--prompt-file")
    s.add_argument("--capture-id", required=True)
    s.add_argument("--model", default="default")
    s.add_argument("--quality", choices=["high"], default=DEFAULT_IMAGE_QUALITY)
    s.add_argument("--reference", action="append", help="PATH::ROLE::KIND, KIND=identity|prop|location|capture_style")
    s.add_argument("--notes", default="")
    s.add_argument("--batch-id", help="V2.4 Batch Runtime derived execution id")
    s.add_argument("--runtime-transaction-id", help="queue/ledger crash-recovery correlation id")
    s.add_argument("--allow-long-prompt", action="store_true")
    s.set_defaults(func=cmd_begin)

    s = sub.add_parser("success", help="record a generated candidate; dimensions must exactly match canvas")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--path", required=True)
    s.add_argument("--provider-receipt", help="provider RAW dimension receipt JSON")
    s.set_defaults(func=cmd_success)

    s = sub.add_parser("tech-fail", help="record network/timeout/no-candidate failure without consuming content repair")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--code", required=True)
    s.add_argument("--message", required=True)
    s.set_defaults(func=cmd_tech_fail)

    s = sub.add_parser("review", help="content review for ready candidate")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--decision", choices=["pass", "repair", "needs_user"], required=True)
    s.add_argument("--notes", default="")
    s.set_defaults(func=cmd_review)

    s = sub.add_parser("authorize-repair", help="explicitly authorize the single content repair round")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--note", required=True)
    s.add_argument("--delegated-auto", action="store_true", help="continuous-execution agent approval; does not claim direct user review")
    s.set_defaults(func=cmd_authorize_repair)

    s = sub.add_parser("authorize-user-locked-repair", help="reopen a locked frame for its first ordinary repair with direct user scope approval")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_authorize_user_locked_repair)

    s = sub.add_parser("authorize-user-passed-repair", help="reopen a PASSED pre-lock frame after a direct-user authority change")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_authorize_user_passed_repair)

    s = sub.add_parser("authorize-authority-refresh", help="reopen a ready/passed frame after direct-user authority or Frame Contract drift without consuming content repair budget")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_authorize_authority_refresh)

    s = sub.add_parser("authorize-user-exception-repair", help="record one direct-user exception after the ordinary repair hard-fails")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_authorize_user_exception_repair)

    s = sub.add_parser("accept-user-exception-candidate", help="accept an existing NEEDS_USER exception candidate with direct user approval")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--approval-text", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_accept_user_exception_candidate)

    s = sub.add_parser("restore-evidence-gap-review", help="restore a candidate incorrectly failed solely by an unavailable-input review")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_restore_evidence_gap_review)

    s = sub.add_parser("promote", help="copy current passed candidate into production/approved without overwriting source")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.set_defaults(func=cmd_promote)

    s = sub.add_parser("lock", help="lock approved asset by SHA-256")
    s.add_argument("episode_dir")
    s.add_argument("--frame", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_lock)

    s = sub.add_parser("batch-begin", help="open an auditable generation batch")
    s.add_argument("episode_dir")
    s.add_argument("--frames", action="append", required=True, help="e.g. 01-03 or 01,03,05")
    s.add_argument("--max-successes", type=int, default=3)
    s.add_argument("--note", default="")
    s.set_defaults(func=cmd_batch_begin)

    s = sub.add_parser("batch-end", help="close a generation batch")
    s.add_argument("episode_dir")
    s.add_argument("--batch-id", required=True)
    s.add_argument("--summary", default="")
    s.set_defaults(func=cmd_batch_end)

    s = sub.add_parser("audit", help="audit ledger invariants and asset hashes")
    s.add_argument("episode_dir")
    s.add_argument("--require-passed", action="store_true")
    s.set_defaults(func=cmd_audit)

    s = sub.add_parser("show")
    s.add_argument("episode_dir")
    s.add_argument("--frame")
    s.set_defaults(func=cmd_show)
    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
