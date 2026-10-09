#!/usr/bin/env python3
"""Read-only provenance dossier for UNKNOWN image Generation Attempts.

Separates native/legacy *worker completion* from provider-level image success.
Nothing here authorizes retry, changes MySQL, promotes RAW, or calls a model.
Usage (via configured production launcher):
 python scripts/storyos_production_env.py scripts/storyos_generation_terminal_dossier.py --episode episodes/...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
SCRIPTS = ROOT / "scripts"
for entry in (ROOT, SYSTEM, SCRIPTS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import generation_attempt_authority as attempts
import image_blocked_recovery
import production_ledger
import provider_receipt_persistence
import scheduler_core
import storyos_generation_evidence_audit as audit


def _fingerprint(path: Path) -> dict:
    """Metadata + SHA only. Never leak a log or Provider payload in the report."""
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha256.update(chunk)
    return {
        "name": path.name,
        "sha256": sha256.hexdigest(),
        "bytes": path.stat().st_size,
    }


def _turn_completed(path: Path) -> bool:
    """Codex turn completion is observation, never proof of image success."""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.completed":
            return True
    return False


def inspect(ep: Path) -> dict:
    ep = Path(ep).resolve()
    ep.relative_to((ROOT / "episodes").resolve())
    audited = audit.inspect(ep)
    queue = scheduler_core.load_queue(ep)
    items = queue.get("items") or []
    ledger = production_ledger.load_authority(ep, default={}) or {}
    result = []
    for row in audited["items"]:
        frame = int(row["frame"])
        key = attempts.frame_key(ep, frame)
        consumed = int(row["attempts_consumed"])
        original = attempts.load_attempt(ep, key, consumed) if consumed else None
        original = original or {}
        generation_key = str(original.get("generation_key") or "")
        queue_items = [
            entry for entry in items
            if isinstance(entry, dict)
            and entry.get("status") == "tech_failed"
            and int(entry.get("frame") or 0) == frame
        ]
        evidence = []
        prefix = f"{frame:02d}-"
        directory = ep / "meta" / "image-workers"
        if directory.is_dir():
            for path in sorted(directory.iterdir()):
                if not path.is_file() or not path.name.startswith(prefix):
                    continue
                if not (path.name.endswith(".lifecycle.json")
                        or path.name.endswith(".jsonl")):
                    continue
                proof = _fingerprint(path)
                if path.name.endswith(".lifecycle.json"):
                    try:
                        lifecycle = json.loads(path.read_text(encoding="utf-8-sig"))
                    except ValueError:
                        lifecycle = None
                    proof.update({
                        "kind": "worker_lifecycle",
                        "state": (lifecycle or {}).get("state")
                                 if isinstance(lifecycle, dict) else None,
                        "generation_key_matches_attempt": bool(
                            generation_key and isinstance(lifecycle, dict)
                            and lifecycle.get("generation_key") == generation_key),
                    })
                else:
                    proof.update({
                        "kind": "worker_conversation",
                        "turn_completed": _turn_completed(path),
                    })
                evidence.append(proof)
        raw = ep / "media" / "raw"
        raw_proofs = sorted(
            (_fingerprint(path) for path in raw.glob(f"{frame:02d}-*")
             if path.is_file()), key=lambda proof: proof["name"]
        ) if raw.is_dir() else []
        # Provider receipts can survive even when the Generation Attempt has
        # no RESULT_REF. Inspect them separately, never promote an unbound
        # Provider receipt to terminal image authority.
        latest_ledger_attempt = image_blocked_recovery._latest_attempt(ledger, frame)
        receipt_path = (
            image_blocked_recovery._receipt_from_error(
                ep, queue_items[0], latest_ledger_attempt)
            if len(queue_items) == 1 else None
        )
        receipt_info = {"located": False, "source": None,
                        "frame_matches": False, "raw_sha256_matches": False,
                        "normalize_decision": None, "receipt_status": None,
                        "attempt_id_present": False, "request_id_present": False}
        if receipt_path is not None:
            loaded = provider_receipt_persistence.load_by_path(ep, receipt_path)
            payload = (loaded or {}).get("payload")
            if isinstance(payload, dict):
                expected_hash = str(payload.get("raw_sha256") or "").lower()
                receipt_info = {
                    "located": True,
                    "source": loaded.get("source") or "json",
                    "frame_matches": str(payload.get("frame") or "").zfill(2)
                                     == f"{frame:02d}",
                    "raw_sha256_matches": bool(
                        expected_hash and any(
                            proof["sha256"] == expected_hash
                            for proof in raw_proofs)),
                    "normalize_decision": str(
                        payload.get("normalize_decision") or "") or None,
                    "receipt_status": loaded.get("receipt_status"),
                    "attempt_id_present": bool(loaded.get("attempt_id")),
                    "request_id_present": bool(loaded.get("request_id")),
                    # These fields are diagnostic only, not terminal proof.
                    # RECORDED plus a matching RAW is still not an official
                    # Generation Attempt completion or retry admission.
                }
        row_result = {
            **row,
            "generation_key_present": bool(generation_key),
            "worker_evidence": evidence,
            "raw_evidence": raw_proofs,
            "provider_receipt_evidence": receipt_info,
            "provider_terminal_receipt_verified": False,
            "controller_turn_is_provider_terminal_receipt": False,
            "worker_terminal_is_provider_terminal_receipt": False,
            "verification_required": (
                "Bind an original provider terminal receipt to the same Episode, "
                "asset, generation key, attempt, image artifact hash, and outcome; "
                "never infer image success from Codex turn.completed, worker FAILED, "
                "or an unbound RAW candidate."
            ),
            "authority_mutation_permitted": False,
            "generation_retry_permitted": False,
            "technical_row_count": len(queue_items),
        }
        result.append(row_result)
    return {
        "schema_version": 1,
        "authority": "DIAGNOSTIC_ONLY",
        "readonly": True,
        "model_calls": 0,
        "generation_attempt_mutations": 0,
        "episode": ep.relative_to(ROOT).as_posix(),
        "unresolved_frames": [entry["frame"] for entry in result],
        "items": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    path = Path(args.episode)
    if not path.is_absolute():
        path = ROOT / path
    print(json.dumps(inspect(path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
