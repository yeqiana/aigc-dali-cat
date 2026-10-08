from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / 'episodes' / '_system'
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_review


def _prompt():
    ep = ROOT / 'episodes' / 'synthetic_locked_story_review'
    return story_review.critic_prompt(
        ep, ep / 'docs/story.md', ep / 'docs/storyboard.md',
        ep / 'meta/.story-semantic-review.candidate.json', 1,
    )


def test_locked_documentary_critic_uses_realistic_rubric_without_abnormal_response(monkeypatch):
    monkeypatch.setattr(story_review.runtime_request, 'authority_for_episode', lambda _ep: {
        'story_input': {'mode': 'locked_story', 'allow_structure_rewrite': False},
    })
    monkeypatch.setattr(story_review.propagation_core_gate, 'anomaly_applicable', lambda _ep: False)
    prompt = _prompt()
    assert 'LOCKED NON-ANOMALOUS DOCUMENTARY HARD RULES' in prompt
    assert 'Check real chronology and age arithmetic' in prompt
    assert 'Do not rewrite any user-locked scene' in prompt
    assert 'ONE core anomaly rule' not in prompt
    assert '"propagation_core": {' not in prompt
    assert '"blind_retell": {' in prompt
    assert '"hard_checks": {' in prompt
    assert 'issue_codes' in prompt
    assert 'summary.passed=false' in prompt


@pytest.mark.parametrize('case_data,anomaly_applicable', [
    ({'story_input': {'mode': 'auto_create', 'allow_structure_rewrite': True}}, False),
    ({'story_input': {'mode': 'locked_story', 'allow_structure_rewrite': False}}, True),
])
def test_other_genres_keep_original_anomaly_rubric(monkeypatch, case_data, anomaly_applicable):
    monkeypatch.setattr(story_review.runtime_request, 'authority_for_episode', lambda _ep: case_data)
    monkeypatch.setattr(story_review.propagation_core_gate, 'anomaly_applicable', lambda _ep: anomaly_applicable)
    prompt = _prompt()
    assert 'LOCKED NON-ANOMALOUS DOCUMENTARY HARD RULES' not in prompt
    assert 'ONE core anomaly rule' in prompt
    assert '"propagation_core": {' in prompt
