from __future__ import annotations

import subprocess
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_asset_policy as policy


def _ignored(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def test_runtime_request_staging_copies_are_ignored():
    assert _ignored("runtime/requests/example.json")


def test_bound_episode_runtime_request_remains_trackable_authority():
    assert not _ignored("episodes/example/meta/runtime-request.json")


def test_provider_receipts_are_not_broadly_ignored():
    assert not _ignored("episodes/example/meta/provider-receipts/01.json")


def test_episode_runtime_tree_is_not_broadly_ignored():
    assert not _ignored("episodes/example/meta/runtime/runtime-evidence-contract.json")


def test_lifecycle_policy_keeps_authority_and_evidence_tracked():
    assert policy.classify("episodes/demo/meta/runtime-request.json").category == policy.AUTHORITY
    assert policy.classify("episodes/demo/meta/runtime-request.json").git_disposition == policy.TRACK
    receipt = policy.classify("episodes/demo/meta/provider-receipts/01-1.json")
    assert receipt.category == policy.FORMAL_EVIDENCE
    assert receipt.git_disposition == policy.TRACK


def test_lifecycle_policy_marks_only_proven_derived_outputs_as_migration_candidates():
    contract = policy.classify("episodes/demo/meta/runtime/contracts/frames/01.json")
    prompt = policy.classify("episodes/demo/meta/runtime/prompt-packages/01.json")
    assert contract.category == policy.DERIVED_CACHE
    assert prompt.category == policy.DERIVED_CACHE
    assert contract.git_disposition == policy.MIGRATION_CANDIDATE
    assert prompt.git_disposition == policy.MIGRATION_CANDIDATE
    # Classification does not silently change Git behavior before a storage migration exists.
    assert not _ignored("episodes/demo/meta/runtime/contracts/frames/01.json")


def test_operational_state_is_preserved_until_a_real_storage_migration_exists():
    for path in (
        "episodes/demo/meta/production-queue.json",
        "episodes/demo/meta/runtime-checkpoint.json",
        "episodes/demo/meta/runtime/next-action.json",
    ):
        row = policy.classify(path)
        assert row.category == policy.OPERATIONAL_STATE
        assert row.git_disposition == policy.PRESERVE_UNTIL_ARCHIVED
        assert row.may_delete_automatically is False


def test_only_prebind_request_staging_is_currently_safe_local_only():
    row = policy.classify("runtime/requests/example.json")
    assert row.category == policy.LOCAL_STAGING
    assert row.git_disposition == policy.LOCAL_ONLY
    assert row.may_delete_automatically is True
