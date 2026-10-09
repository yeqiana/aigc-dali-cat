from __future__ import annotations

import sys
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_blocked_recovery


@pytest.mark.parametrize("code", sorted(image_blocked_recovery.NATIVE_IMAGE_CAPABILITY_CODES))
def test_native_capability_block_requires_real_attestation_without_attempt(tmp_path, code):
    result = image_blocked_recovery.inspect_item(tmp_path, {
        "frame": 1, "id": "item-01", "technical_failure_code": code,
    })
    assert result["auto_resolvable"] is False
    assert result["code"] == code
    assert result["recovery_action"] == "VERIFY_NATIVE_CODEX_IMAGE_CAPABILITY"
    assert "Phase5A" in result["recovery_hint"]
    assert result["reason"] == "native_codex_session_image_tool_attestation_missing"


def test_other_failure_stays_blocked_without_fake_recovery(tmp_path):
    result = image_blocked_recovery.inspect_item(tmp_path, {
        "frame": 1, "id": "item-02", "technical_failure_code": "OTHER_PROVIDER_FAILURE",
    })
    assert result["auto_resolvable"] is False
    assert result["reason"] == "unsupported_non_regenerating_failure"
    assert "recovery_action" not in result
