from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import concept_ambition


def test_concept_ambition_not_required_for_user_locked_story(monkeypatch, tmp_path):
    monkeypatch.setattr(
        concept_ambition.runtime_request,
        "authority_for_episode",
        lambda _ep: {"story_input": {"mode": "locked_story", "allow_structure_rewrite": False}},
    )
    monkeypatch.setattr(concept_ambition, "episode_contract_version", lambda _ep: "2.6.1")
    assert concept_ambition.required(tmp_path) is False


def test_concept_ambition_remains_required_for_authored_story(monkeypatch, tmp_path):
    monkeypatch.setattr(
        concept_ambition.runtime_request,
        "authority_for_episode",
        lambda _ep: {"story_input": {"mode": "auto_create", "allow_structure_rewrite": True}},
    )
    monkeypatch.setattr(concept_ambition, "episode_contract_version", lambda _ep: "2.6.1")
    assert concept_ambition.required(tmp_path) is True


def test_rereview_plan_preserves_old_review_and_requires_new_attempt_on_sha_drift():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True)
        candidates = ep / concept_ambition.CANDIDATES_REL
        candidates.write_text('{"schema_version":1,"candidates":[]}', encoding="utf-8")
        review = ep / concept_ambition.REVIEW_REL
        review.write_text('{"candidates_sha256":"old-sha","critic_provenance":{"attempt":1}}', encoding="utf-8")
        plan = concept_ambition.re_review_plan(ep)
        assert plan["required"] is True
        assert plan["reason"] == "CANDIDATES_SHA_DRIFT"
        assert plan["preserve_existing_review"] is True
        assert plan["action"] == "RUN_CONCEPT_AMBITION_CRITIC"
        assert plan["next_attempt"] == 2


def test_rereview_plan_is_noop_when_review_matches_current_candidates():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True)
        candidates = ep / concept_ambition.CANDIDATES_REL
        candidates.write_text('{"schema_version":1,"candidates":[]}', encoding="utf-8")
        sha = concept_ambition.sha256_file(candidates)
        review = ep / concept_ambition.REVIEW_REL
        review.write_text('{"candidates_sha256":"' + sha + '"}', encoding="utf-8")
        plan = concept_ambition.re_review_plan(ep)
        assert plan["required"] is False
        assert plan["reason"] == "CURRENT_REVIEW_VALID"
        assert plan["action"] == "NONE"


def test_concept_required_locked_story(monkeypatch, tmp_path):
    import runtime_request
    monkeypatch.setattr(concept_ambition, "episode_contract_version", lambda _ep: "2.6.1")
    monkeypatch.setattr(runtime_request, "authority_for_episode", lambda _ep: {
        "story_input": {
            "mode": "locked_story", "allow_structure_rewrite": False
        }
    })
    assert concept_ambition.required(tmp_path) is False


def test_concept_required_authored_story(monkeypatch, tmp_path):
    import runtime_request
    monkeypatch.setattr(concept_ambition, "episode_contract_version", lambda _ep: "2.6.1")
    monkeypatch.setattr(runtime_request, "authority_for_episode", lambda _ep: {
        "story_input": {
            "mode": "auto_create", "allow_structure_rewrite": True
        }
    })
    assert concept_ambition.required(tmp_path) is True


def test_concept_required_fails_closed_when_request_unavailable(monkeypatch, tmp_path):
    import runtime_request
    monkeypatch.setattr(concept_ambition, "episode_contract_version", lambda _ep: "2.6.1")
    def unavailable(_ep):
        raise RuntimeError("request unavailable")
    monkeypatch.setattr(runtime_request, "authority_for_episode", unavailable)
    assert concept_ambition.required(tmp_path) is True
