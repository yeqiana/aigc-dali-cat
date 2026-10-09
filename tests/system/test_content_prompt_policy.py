from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import content_prompt_policy as policy
import production_prompt_materializer


def test_partner_common_policy_is_storyos_derived_only():
    cfg = policy.load_policy()
    assert cfg["authority"] == "derived_prompt_transport_only"
    assert cfg["continuity"]["max_execution_references"] == 2
    assert cfg["continuity"]["preferred_reference_order"][:3] == [
        "character_identity", "first_frame_anchor", "previous_frame"
    ]


def test_scene_prompt_adopts_text_and_safety_rules_without_replacing_frame_contract():
    contract = {
        "frame": "02",
        "storyboard_frame": {"text": "2. **门口**：孩子避开击打瞬间，保护者挡在前面。"},
    }
    text = policy.build_scene_prompt(contract)
    assert "保护者上前阻止的瞬间" in text
    assert "Frame Contract" in text
    assert "文字留给后期叠字" in text
    assert not policy.lint_scene_prompt(text)
    assert len(text) <= 250
    assert len(text.encode("utf-8")) <= 860


def test_linter_fails_active_risk_but_ignores_negative_instruction():
    issues = policy.lint_scene_prompt("画面表现喷血和开放伤口")
    assert {row["code"] for row in issues} == {"CONTENT_SAFETY_RISK"}
    assert policy.lint_scene_prompt("禁止喷血，不出现开放伤口") == []


def test_production_materializer_uses_common_policy():
    contract = {"frame": "03", "storyboard_frame": {"text": "3. **客厅**：人物安静坐下。"}}
    text = production_prompt_materializer.prompt_for_contract(contract, use_common_policy=True)
    assert "Frame Contract" in text
    assert "人物姓名标签" in text
    assert "后期叠字" in text


def test_missing_locked_scene_fails_closed_even_with_partner_policy():
    contract = {"frame": "06", "storyboard_frame": {"text": ""}}
    import pytest
    with pytest.raises(ValueError, match="no localized scene"):
        production_prompt_materializer.prompt_for_contract(contract, use_common_policy=True)
    with pytest.raises(ValueError, match="no localized scene"):
        policy.build_scene_prompt(contract)


def test_common_policy_respects_explicit_locked_table_beat():
    contract = {"frame": "07", "storyboard_frame": {"text": ""}}
    prompt = production_prompt_materializer.prompt_for_contract(
        contract, exact_scene="主角从楼梯转角抬头", use_common_policy=True)
    assert "主角从楼梯转角抬头" in prompt
    assert len(prompt) <= 250 and len(prompt.encode("utf-8")) <= 860
