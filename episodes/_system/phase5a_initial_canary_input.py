#!/usr/bin/env python3
"""Prepare the *already claimed* initial, non-promotable Phase5A image canary.

Never creates another claim, Episode stage, image Attempt, generation result or
Release PASS. Uses the existing deterministic fixture / canonical compilers.
Unlike phase5a_validation_input.py this is only for the first global claim,
which legitimately does not have a validation_epoch.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import frame_contract
import generation_attempt_authority
import image_scheduler
import logical_asset_identity
import phase5a_collaborative_canary as canary
import phase5a_validation_input as fixture
import prompt_package
import prompt_package_persistence
import scheduler_core
import storage_config
import storyos_config
from platform.repository.mysql.schema_v2 import DATABASE_NAME

INITIAL_CLAIM_ID = "native-image-proof-20261008"


class InitialCanaryPreparationError(RuntimeError):
    pass


def prepare(episode_dir: str | Path, *, canary_id: str) -> dict:
    ep, marker = canary.validate_workspace(episode_dir, canary_id)
    if canary_id != INITIAL_CLAIM_ID:
        raise InitialCanaryPreparationError("INITIAL_CANARY_ID_NOT_ALLOWLISTED")
    if (ep / "meta/episode-state.json").exists():
        raise InitialCanaryPreparationError("INITIAL_CANARY_STAGE_AUTHORITY_FORBIDDEN")
    cfg = storyos_config.load_config()
    if storyos_config.validate(cfg) or storyos_config.get_path(cfg, "production.mode") != "COLLABORATIVE":
        raise InitialCanaryPreparationError("INITIAL_CANARY_CONFIG_INVALID")
    mysql = storage_config.mysql_connection_kwargs()
    if (str(mysql.get("host")) not in {"127.0.0.1", "localhost"}
            or int(mysql.get("port") or 0) != 3306
            or str(mysql.get("database")) != DATABASE_NAME):
        raise InitialCanaryPreparationError("INITIAL_CANARY_TEST_DB_REQUIRED")

    # Require the pre-existing, exact initial claim; never reserve a new ID.
    # Its marker exists, but only the actual global claim can authorize setup.
    claim = canary.claim_global_canary(ep, canary_id, allow_validation_epoch=False)
    if (claim.get("canary_id") != canary_id or claim.get("resumed") is not True
            or claim.get("replacement") is not False or claim.get("validation_epoch")):
        raise InitialCanaryPreparationError("INITIAL_CANARY_GLOBAL_CLAIM_INVALID")

    key = logical_asset_identity.frame_asset_key(ep, 1)
    asset = generation_attempt_authority.load_asset_state(ep, key)
    if (int(asset.get("attempts_consumed") or 0) != 0
            or int(asset.get("remaining_attempts") or 0) != 2
            or asset.get("active_attempt_index") is not None):
        raise InitialCanaryPreparationError("INITIAL_CANARY_ATTEMPT_NOT_FRESH")
    queue = scheduler_core.load_queue(ep)
    active = [x for x in queue.get("items") or [] if x.get("status") != "superseded"]
    if active or queue.get("review_work_items"):
        raise InitialCanaryPreparationError("INITIAL_CANARY_QUEUE_NOT_EMPTY")

    docs = fixture._ensure_fixture_files(ep)
    frozen = fixture._ensure_runtime_request_and_policy(ep)
    contract = frame_contract.compile_frame(ep, 1, write_cache=True)
    image_scheduler.import_batch(ep, docs["prompt_path"].parent)
    pkg = prompt_package_persistence.load_latest(ep, 1)
    if not isinstance(pkg, dict):
        prompt_package.compile_frame(ep, 1, docs["prompt_path"], write=True)
        pkg = prompt_package_persistence.load_latest(ep, 1)
    if not isinstance(pkg, dict):
        raise InitialCanaryPreparationError("INITIAL_CANARY_PROMPT_PACKAGE_MISSING")

    queue = scheduler_core.load_queue(ep)
    active = [x for x in queue.get("items") or [] if x.get("status") != "superseded"]
    if len(active) == 0:
        payload = frozen["payload"]
        image_scheduler.add_item(
            ep, frame=1, kind="original", prompt_file=docs["prompt_path"],
            scope="batch", references=image_scheduler.contract_references(ep, 1, scope="batch"),
            capture_id="batch-01", model=str(payload["model"]),
            quality=str(payload["quality"]), strict_model=bool(payload.get("strict_model")),
            depends_on=image_scheduler.directive_dependency(ep, 1), replace=True,
        )
    # The canonical Canary verifier, not this helper, grants READY.
    proof = canary._preflight(ep, canary_id)
    if proof["frame_contract_sha256"] != contract["contract_sha256"]:
        raise InitialCanaryPreparationError("INITIAL_CANARY_FRAME_CONTRACT_DRIFT")
    if proof["prompt_package_sha256"] != pkg["package_sha256"]:
        raise InitialCanaryPreparationError("INITIAL_CANARY_PROMPT_DRIFT")
    if proof["attempts_consumed"] != 0 or proof["remaining_attempts"] != 2:
        raise InitialCanaryPreparationError("INITIAL_CANARY_ATTEMPT_DRIFT")
    result = {
        "schema_version": 1,
        "status": "READY",
        "class": "TEST_ONLY",
        "canary_id": canary_id,
        "frame": 1,
        "source_sha256": docs["descriptor"]["source_sha256"],
        "frame_contract_sha256": contract["contract_sha256"],
        "prompt_package_sha256": pkg["package_sha256"],
        "queue_item_id": proof["queue_item_id"],
        "attempts_consumed": 0,
        "provider_calls": 0,
        "release_eligible": False,
        "stage_authority": False,
    }
    evidence = ep / "meta/phase5a-initial-preparation.json"
    if evidence.is_file():
        if json.loads(evidence.read_text(encoding="utf-8-sig")) != result:
            raise InitialCanaryPreparationError("INITIAL_CANARY_PREPARATION_DRIFT")
    else:
        evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    parser.add_argument("--canary-id", required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.episode_dir, canary_id=args.canary_id)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
