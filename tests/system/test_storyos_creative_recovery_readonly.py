"""Read-only native Story outcome reuse diagnostics; no paid calls/DB writes."""
from __future__ import annotations
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import pytest

SYS = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))
SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
spec = importlib.util.spec_from_file_location(
    "storyos_creative_recovery_readonly", SCRIPTS / "storyos_creative_recovery_readonly.py"
)
assert spec and spec.loader
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


@pytest.fixture
def episode(tmp_path, monkeypatch):
    ep = tmp_path / "test-episode"
    (ep / "meta" / "provider-receipts").mkdir(parents=True)
    (ep / "docs").mkdir()
    monkeypatch.setattr(recovery.character_contract, "load",
                        lambda _: {"status": "DRAFT"})
    monkeypatch.setattr(recovery.character_contract, "authority_sha256",
                        lambda _: "a" * 64)
    (ep / "meta" / "provider-receipts" / "one.json").write_text(json.dumps({
        "step": "CREATIVE_STORY", "provider": "codex_subscription",
        "status": "SUCCESS"}), encoding="utf-8")
    return ep


def test_success_receipt_not_mistaken_for_story_lock(episode):
    result = recovery.inspect(episode)
    assert result["status"] == "MODEL_SUCCEEDED_BUT_STORY_REVIEW_MISSING"
    assert result["model_success_receipt_count"] == 1
    assert result["model_generation_required"] is None
    assert result["model_success_is_story_lock"] is False
    assert result["read_only"] is True
    assert result["sql_writes"] == 0


def write_review(ep, *, sha=None):
    story = ep / "docs" / "story.md"
    story.write_text("每一个主人公都有清楚的出行动机。" * 20, encoding="utf-8")
    rv = {
        "schema_version": 1, "expected_contract_sha256": "a" * 64,
        "story_path": "docs/story.md",
        "story_sha256": sha or hashlib.sha256(story.read_bytes()).hexdigest(),
        "no_anomaly_test": {
            "pass": True, "ordinary_day_plan": "早上开车去山里游玩，吃完午饭就回家",
            "review_reason": "每个人的现实出行动机都成立，即使无异常事件也可以正常完成这次旅行。"
        }
    }
    (ep / "meta" / "character-story-review.json").write_text(
        json.dumps(rv, ensure_ascii=False), encoding="utf-8")
    return story


def test_valid_review_is_only_candidate_not_story_gate_pass(episode):
    write_review(episode)
    result = recovery.inspect(episode)
    assert result["status"] == "REVIEW_EVIDENCE_PRESENT_CAN_ATTEMPT_CANONICAL_LOCK"
    assert result["model_generation_required"] is None
    assert not result["model_success_is_story_lock"]


def test_story_sha_drift_blocks_reuse(episode):
    story = write_review(episode)
    story.write_text("故事已经变成了另一版。" * 50, encoding="utf-8")
    result = recovery.inspect(episode)
    assert result["status"] == "REVIEW_STORY_SHA_DRIFT"


def test_lock_status_is_not_a_storyboard_lock(episode, monkeypatch):
    monkeypatch.setattr(recovery.character_contract, "load",
                        lambda _: {"status": "LOCKED"})
    result = recovery.inspect(episode)
    assert result["status"] == "CONTRACT_ALREADY_LOCKED_VERIFY_STORY_GATES"
    assert not result["model_success_is_story_lock"]


def test_wrong_contract_sha_blocks(episode):
    write_review(episode)
    f = episode / "meta" / "character-story-review.json"
    rv = json.loads(f.read_text(encoding="utf-8"))
    rv["expected_contract_sha256"] = "b" * 64
    f.write_text(json.dumps(rv), encoding="utf-8")
    assert recovery.inspect(episode)["status"] == "REVIEW_CONTRACT_SHA_STALE"
