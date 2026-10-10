"""Hermetic Character Contract reviewed Story Lock regressions (no DB writes)."""
from __future__ import annotations
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import character_contract


@pytest.fixture
def case(tmp_path, monkeypatch):
    ep = tmp_path / "episodes" / "00_独立篇" / "06_测试作品"
    (ep / "docs").mkdir(parents=True)
    (ep / "meta").mkdir()
    initial = {
        "schema_version": 1, "status": "DRAFT", "created_at": "test",
        "selection_seed": 42, "world_identity": None,
        "cast": {"size": 1, "type": "single_female", "members": [
            {"id": "P01", "gender": "female", "age": 23, "clothing_anchor": "普通衣着"}]},
        "era": {"bucket": "modern_2020s"},
        "role_policy": {"career_function": "arrival_only", "solves_anomaly_professionally": False},
        "entry": {"type": "travel"},
        "no_anomaly_test": {"pass": True, "ordinary_day_plan": "正常出游拍照与回家",
                            "rechecked_against_final_story": False},
    }
    state = [deepcopy(initial)]
    saves = []
    monkeypatch.setattr(character_contract, "load", lambda _: deepcopy(state[0]))
    def save(_, candidate, *, expected_sha256=None):
        assert expected_sha256 is not None
        state[0] = deepcopy(candidate)
        saves.append(deepcopy(candidate))
        return candidate
    monkeypatch.setattr(character_contract, "save", save)
    monkeypatch.setattr(character_contract.world_identity_contract, "required", lambda _: False)
    # This focused suite checks the reviewed-write boundary, not unrelated pool
    # scoring: those validations are separately covered in Character tests.
    monkeypatch.setattr(character_contract, "validate", lambda _, require_locked=False, candidate=None:
                        [] if (candidate if candidate is not None else state[0]).get("status") == "LOCKED"
                        else ["unlocked"])
    story = ep / "docs" / "story.md"
    story.write_text("山里的朋友们依照普通旅行计划出发。午饭、拍照、休息后准备返程。" * 10, encoding="utf-8")
    review = {
        "schema_version": 1,
        "expected_contract_sha256": character_contract.authority_sha256(ep),
        "story_path": "docs/story.md",
        "story_sha256": hashlib.sha256(story.read_bytes()).hexdigest(),
        "no_anomaly_test": {
            "pass": True,
            "ordinary_day_plan": "原定旅程为中午吃饭、拍照、晚间返回原来住处",
            "review_reason": "主角与朋友以现实旅行动机抵达，普通旅程的交通、吃饭和拍照均不依赖任何异常。"
        },
    }
    record = ep / "meta" / "character-story-review.json"
    record.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    return ep, story, record, review, state, saves


def test_reviewed_lock_then_idempotent_resume(case):
    ep, _, record, _, state, saves = case
    done = character_contract.reviewed_story_lock(ep, record)
    assert done["committed"] is True and done["status"] == "LOCKED"
    assert len(saves) == 1
    assert state[0]["no_anomaly_test"]["rechecked_against_final_story"] is True
    assert state[0]["final_story_review"]["source"] == "scoped_story_worker_attestation"
    again = character_contract.reviewed_story_lock(ep, record)
    assert again["status"] == "ALREADY_LOCKED" and again["committed"] is False
    assert len(saves) == 1


@pytest.mark.parametrize("fault", ["contract_sha", "story_sha", "review_pass", "review_reason",
                                    "traversal", "proposal_origin", "blank_day"])
def test_missing_or_forged_evidence_never_commits(case, fault):
    ep, _, record, review, _, saves = case
    if fault == "contract_sha":
        review["expected_contract_sha256"] = "f" * 64
    elif fault == "story_sha":
        review["story_sha256"] = "0" * 64
    elif fault == "review_pass":
        review["no_anomaly_test"]["pass"] = False
    elif fault == "review_reason":
        review["no_anomaly_test"]["review_reason"] = ""
    elif fault == "blank_day":
        review["no_anomaly_test"]["ordinary_day_plan"] = ""
    elif fault == "traversal":
        review["story_path"] = "../../other.md"
    elif fault == "proposal_origin":
        review["proposed_contract"] = {"schema_version": 2}
    record.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        character_contract.reviewed_story_lock(ep, record)
    assert saves == []


def test_later_story_edits_invalidate_review(case):
    ep, story, record, _, _, saves = case
    story.write_text("另一份有明显内容漂移的最终故事。" * 30, encoding="utf-8")
    with pytest.raises(ValueError, match="FINAL_STORY_SHA"):
        character_contract.reviewed_story_lock(ep, record)
    assert saves == []


def test_missing_review_file_never_commits(case):
    ep, _, record, _, _, saves = case
    record.unlink()
    with pytest.raises(ValueError, match="CHARACTER_REVIEW_PATH_INVALID"):
        character_contract.reviewed_story_lock(ep, record)
    assert saves == []
