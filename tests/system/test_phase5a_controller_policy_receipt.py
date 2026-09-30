from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_subscription_image as backend


def test_controller_argv_and_provider_receipt_bind_episode_policy(tmp_path, monkeypatch):
    policy = {
        "model": "gpt-6-luna",
        "reasoning_effort": "high",
        "profile": "image_controller",
        "model_policy_sha256": "a" * 64,
    }
    monkeypatch.setattr(backend.model_policy, "validate_bound_policy", lambda _ep: [])
    monkeypatch.setattr(
        backend.model_policy,
        "resolve",
        lambda role, episode=None: policy if role == "image.controller" and episode else {},
    )
    argv = backend.controller_args(tmp_path)
    assert argv[:2] == ["-m", "gpt-6-luna"]
    assert 'model_reasoning_effort="high"' in argv

    receipt = backend.provider_receipt_model_bindings(
        tmp_path, "gpt-image-2.5-flare", "high"
    )
    assert receipt == {
        "controller_model": "gpt-6-luna",
        "controller_effort": "high",
        "controller_profile": "image_controller",
        "controller_policy_sha256": "a" * 64,
        "controller_model_source": "EPISODE_BOUND_RUNTIME_POLICY",
        "payload_model": "gpt-image-2.5-flare",
        "payload_quality": "high",
        "payload_model_source": "EXPLICIT_RUNTIME_BINDING",
        "payload_provider_attestation": False,
    }
