from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import story_review


def _setup(monkeypatch, ep, *, passed=True):
    ep.mkdir(parents=True,exist_ok=True)
    story=ep/"story.md"
    board=ep/"storyboard.md"
    story.write_text("real story",encoding="utf-8")
    board.write_text("frame 01",encoding="utf-8")
    monkeypatch.setattr(story_review,"story_paths",lambda _ep:(story,board))
    source_story=story_review.sha256_file(story)
    source_board=story_review.sha256_file(board)
    monkeypatch.setattr(story_review,"load_review",lambda _ep:{
        "summary":{"passed":passed},
        "story_sha256":source_story,
        "storyboard_sha256":source_board,
        "critic_provenance":{"attempt":5,"review_scope":"LOCKED_DOCUMENTARY_SYMBOLIC_REMEDIATION"},
    })
    monkeypatch.setattr(story_review,"review_authority_sha256",lambda _ep:"a"*64)
    gates={"reviews":{"story":"pending"}}
    monkeypatch.setattr(story_review,"read_json",lambda _path:gates)
    saved=[]
    monkeypatch.setattr(story_review,"write_json",lambda p,d:saved.append((p,d)))
    return gates,saved


def test_review_gate_refuses_failed_critic(monkeypatch,tmp_path):
    gates,saved=_setup(monkeypatch,tmp_path,passed=False)
    monkeypatch.setattr(story_review,"verify",lambda _ep:["summary.passed must be true"])
    with pytest.raises(ValueError,match="invalid Story Critic"):
        story_review.project_verified_story_gate(tmp_path)
    assert gates["reviews"]["story"]=="pending"
    assert saved==[]


def test_review_gate_accepts_bound_real_pass_only(monkeypatch,tmp_path):
    gates,saved=_setup(monkeypatch,tmp_path)
    monkeypatch.setattr(story_review,"verify",lambda _ep:[])
    result=story_review.project_verified_story_gate(tmp_path)
    assert result["authority_sha256"]=="a"*64
    assert result["attempt"]==5
    assert gates["reviews"]["story"]=="passed"
    assert len(saved)==1
    # Idempotent with the same exact authority.
    assert story_review.project_verified_story_gate(tmp_path)==result
    assert len(saved)==1


def test_review_gate_refuses_existing_unbound_pass(monkeypatch,tmp_path):
    gates,saved=_setup(monkeypatch,tmp_path)
    gates["reviews"]["story"]="passed"
    monkeypatch.setattr(story_review,"verify",lambda _ep:[])
    with pytest.raises(ValueError,match="binding drift"):
        story_review.project_verified_story_gate(tmp_path)
    assert saved==[]
