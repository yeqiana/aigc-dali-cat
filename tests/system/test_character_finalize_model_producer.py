from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from agents import character_finalize_model_producer as producer


def _task():
    return {
        "task_id": "t1",
        "task_type": "CHARACTER_FINALIZE",
        "snapshot_id": "snap",
        "authority_scope": ["character.finalize"],
        "input_contract": {
            "source_authority_sha256": {},
            "authority_inputs": {
                "meta/character-contract.json": {
                    "cast": {"members": [
                        {"id": "P01", "name": "玄奘"},
                        {"id": "P02", "name": "悟空"},
                    ]},
                    "pov": {"character_id": "P01", "first_person": True},
                },
                "meta/character-visual-contract.json": {
                    "members": {
                        "P01": {"story_identity_anchor": "86版唐僧锁定锚点"},
                        "P02": {"story_identity_anchor": "86版悟空锁定锚点"},
                    }
                },
            },
        },
    }


def test_shadow_prompt_embeds_exact_frozen_obligations():
    prompt = producer._prompt(_task(), {}, "agent_shadow")
    assert "86版唐僧锁定锚点" in prompt
    assert "86版悟空锁定锚点" in prompt
    assert "without rewriting 86版 as 1986版" in prompt
    assert "bounded Character Finalize Agent shadow producer" in prompt


def test_legacy_and_shadow_prompts_are_distinct():
    task = _task()
    legacy = producer._prompt(task, {}, "legacy_control")
    shadow = producer._prompt(task, {}, "agent_shadow")
    assert legacy != shadow
    assert "TARGET: produce only the CHARACTER_FINALIZE Candidate" in legacy
    assert "bounded Character Finalize Agent shadow producer" in shadow