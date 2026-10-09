"""Fail-closed audit of actual image Attempt statuses without a Provider call."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/storyos_generation_evidence_audit.py"
spec = importlib.util.spec_from_file_location("image_evidence_audit_under_test", SCRIPT)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)


@pytest.mark.parametrize("status", ["OUTCOME_UNKNOWN", "DISPATCH_COMMITTED", "RESERVED", "MISSING"])
def test_unverified_provider_result_never_authorizes_retry(status, tmp_path):
    # Use a fixture path under the canonical episodes tree for traversal guard.
    ep = ROOT / "episodes" / "_system"
    q = {"items": [{"frame": 6, "status": "tech_failed",
                    "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT"}]}
    mock_attempt = None if status == "MISSING" else {"status": status, "provider": "opencodex"}
    with (
        patch.object(audit.scheduler_core, "load_queue", return_value=q),
        patch.object(audit.attempts, "frame_key", return_value="frame-06"),
        patch.object(audit.attempts, "load_asset_state",
                     return_value={"attempts_consumed": 1}) as get_state,
        patch.object(audit.attempts, "load_attempt", return_value=mock_attempt) as get_attempt,
        patch.object(audit.image_blocked_recovery, "inspect_item",
                     return_value={"auto_resolvable": False, "reason": "unsupported_non_regenerating_failure"}),
    ):
        result = audit.inspect(ep)
    assert result["readonly"] and result["image_generation_called"] is False
    assert result["attempt_authority_mutated"] is False
    assert result["unresolved_frames"] == [6]
    assert result["items"][0]["automatic_retry_permitted"] is False
    assert result["items"][0]["decision"] == "VERIFY_PROVIDER_TERMINAL_EVIDENCE"
    get_state.assert_called_once()
    get_attempt.assert_called_once()


def test_even_terminal_failed_status_is_not_an_unconditional_retry_permission():
    ep = ROOT / "episodes" / "_system"
    q = {"items": [{"frame": 24, "status": "tech_failed",
                    "technical_failure_code": "ASPECT_RATIO_MISMATCH"}]}
    with (
        patch.object(audit.scheduler_core, "load_queue", return_value=q),
        patch.object(audit.attempts, "frame_key", return_value="frame-24"),
        patch.object(audit.attempts, "load_asset_state",
                     return_value={"attempts_consumed": 1}),
        patch.object(audit.attempts, "load_attempt",
                     return_value={"status": "FAILED_AFTER_DISPATCH"}),
        patch.object(audit.image_blocked_recovery, "inspect_item",
                     return_value={"auto_resolvable": False, "reason": "crop_exception_exceeded"}),
    ):
        result = audit.inspect(ep)
    assert result["items"][0]["automatic_retry_permitted"] is False
    assert result["items"][0]["decision"] == "REQUIRE_INDEPENDENT_RETRY_ADMISSION"


def test_external_episode_path_rejected_before_access(tmp_path):
    with pytest.raises(ValueError):
        audit.inspect(tmp_path)


def test_non_failed_queue_items_are_not_reported():
    ep = ROOT / "episodes" / "_system"
    q = {"items": [{"frame": 1, "status": "generated"},
                   {"frame": 2, "status": "queued"}]}
    with patch.object(audit.scheduler_core, "load_queue", return_value=q):
        result = audit.inspect(ep)
    assert result["items"] == []
