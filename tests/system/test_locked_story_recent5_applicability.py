from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT/"episodes"/"_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0,str(SYSTEM))
import release_preflight_recent5 as recent5


def test_user_supplied_non_rewrite_story_does_not_need_creative_recent5(monkeypatch,tmp_path):
    monkeypatch.setattr(recent5.runtime_request,"authority_for_episode",lambda _ep:{
        "story_input":{"mode":"locked_story","allow_structure_rewrite":False},
    })
    monkeypatch.setattr(recent5,"guard_required",lambda _ep:True)
    assert recent5._user_supplied_locked_story_recent5_inapplicable(tmp_path)
    assert recent5.verify_recent5_evidence(tmp_path)==[]
    assert not (tmp_path/"meta/recent5-review.json").exists()


def test_authoring_stories_keep_recent5_evidence_guard(monkeypatch,tmp_path):
    monkeypatch.setattr(recent5.runtime_request,"authority_for_episode",lambda _ep:{
        "story_input":{"mode":"auto_create","allow_structure_rewrite":True},
    })
    monkeypatch.setattr(recent5,"guard_required",lambda _ep:True)
    assert not recent5._user_supplied_locked_story_recent5_inapplicable(tmp_path)
    assert "meta/recent5-review.json missing" in recent5.verify_recent5_evidence(tmp_path)[0]


def test_locked_story_opted_in_rewrite_keeps_recent5_guard(monkeypatch,tmp_path):
    monkeypatch.setattr(recent5.runtime_request,"authority_for_episode",lambda _ep:{
        "story_input":{"mode":"locked_story","allow_structure_rewrite":True},
    })
    monkeypatch.setattr(recent5,"guard_required",lambda _ep:True)
    assert not recent5._user_supplied_locked_story_recent5_inapplicable(tmp_path)
    assert recent5.verify_recent5_evidence(tmp_path)
