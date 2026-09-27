from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
AGENTS = SYSTEM / "agents"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(AGENTS) not in sys.path:
    sys.path.insert(0, str(AGENTS))

import story_semantic_critic_adapter as adapter


def valid_decision(decision="ACCEPT_CANDIDATE"):
    return {
        "decision": decision,
        "issue_codes": [] if decision == "ACCEPT_CANDIDATE" else ["CAUSAL_CHAIN_BROKEN"],
        "severity": "LOW" if decision == "ACCEPT_CANDIDATE" else "HIGH",
        "repair_scope": [],
        "evidence": ["source-bound fixture evidence"],
    }


def test_decision_schema_and_wire_validation_are_strict():
    schema = json.loads((SYSTEM / "agents" / "critic_decision.schema.json").read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["properties"]["decision"]["enum"] == [
        "ACCEPT_CANDIDATE", "REPAIR", "NEEDS_USER", "BLOCK"
    ]
    assert adapter.validate_decision(valid_decision())["decision"] == "ACCEPT_CANDIDATE"
    for payload in (
        {**valid_decision(), "gate_pass": True},
        {**valid_decision(), "input_tokens": 99},
        {**valid_decision(), "decision": "PASS"},
        {**valid_decision(), "decision": "REPAIR", "issue_codes": []},
    ):
        try:
            adapter.validate_decision(payload)
        except adapter.CriticDecisionError:
            pass
        else:
            raise AssertionError(f"invalid decision accepted: {payload}")


def test_existing_review_comparison_is_advisory_and_never_gate_authority():
    review = {"decision": "PASS", "summary": {"passed": True}, "issue_codes": []}
    comparison = adapter.compare_with_existing_review(valid_decision(), review)
    assert comparison == {
        "shadow_decision": "ACCEPT_CANDIDATE",
        "existing_review_decision": "ACCEPT_CANDIDATE",
        "decision_equivalent": True,
        "decision_disagreement": False,
        "existing_issue_codes": [],
        "critic_issue_codes": [],
        "issue_intersection": [],
        "critic_extra_issues": [],
        "critic_missing_issues": [],
        "existing_accept": True,
        "critic_accept": True,
        "issue_disagreement": False,
        "shadow_is_advisory": True,
        "gate_pass": False,
        "authority_write": False,
        "episode_transition": False,
    }
    assert adapter.decision_from_existing_review({"decision": "FAIL", "summary": {"passed": False}, "issue_codes": ["X"]}) == "REPAIR"
    assert adapter.decision_from_existing_review({"decision": "PASS"}) == "BLOCK"


def test_existing_canonical_payload_uses_passed_summary_when_row_decision_is_not_projected():
    assert adapter.decision_from_existing_review({
        "summary": {"passed": True}, "issue_codes": [],
    }) == "ACCEPT_CANDIDATE"
    assert adapter.decision_from_existing_review({
        "summary": {"passed": False}, "issue_codes": ["CAUSAL_CHAIN"],
    }) == "REPAIR"


def test_issue_comparison_reports_only_deterministic_disagreement_not_ground_truth():
    review = {"decision": "FAIL", "summary": {"passed": False}, "issue_codes": ["CAUSE", "CONTINUITY"]}
    critic = {**valid_decision("REPAIR"), "issue_codes": ["CAUSE", "NEW_ISSUE"]}
    comparison = adapter.compare_with_existing_review(critic, review)
    assert comparison["decision_disagreement"] is False
    assert comparison["decision_equivalent"] is True
    assert comparison["issue_intersection"] == ["CAUSE"]
    assert comparison["critic_extra_issues"] == ["NEW_ISSUE"]
    assert comparison["critic_missing_issues"] == ["CONTINUITY"]
    assert comparison["existing_accept"] is False
    assert comparison["critic_accept"] is False
    assert "false_accept" not in comparison and "false_reject" not in comparison
    disagreement = adapter.compare_with_existing_review(
        {**valid_decision("NEEDS_USER"), "issue_codes": ["CAUSE"]}, review
    )
    assert disagreement["decision_disagreement"] is True


def test_bounded_reflection_caps_one_repair_and_two_reviews():
    first = adapter.bounded_reflection_step("REPAIR", critic_attempt=1, auto_repairs_used=0)
    assert first["action"] == "PROPOSE_ONE_TARGETED_REPAIR"
    assert first["repair_invoked"] is False
    assert first["max_review_attempts"] == 2 and first["max_auto_repairs"] == 1
    assert adapter.bounded_reflection_step("REPAIR", critic_attempt=2, auto_repairs_used=1)["action"] == "NEEDS_USER"
    assert adapter.bounded_reflection_step("ACCEPT_CANDIDATE", critic_attempt=1, auto_repairs_used=0)["gate_pass"] is False
    for attempt, repairs in ((0, 0), (3, 0), (1, 2)):
        try:
            adapter.bounded_reflection_step("REPAIR", critic_attempt=attempt, auto_repairs_used=repairs)
        except adapter.CriticDecisionError:
            pass
        else:
            raise AssertionError("reflection bounds were not enforced")


def test_shadow_request_reuses_product_review_and_is_candidate_only(monkeypatch, tmp_path):
    story = tmp_path / "story.md"
    board = tmp_path / "storyboard.md"
    story.write_text("frozen story", encoding="utf-8")
    board.write_text("frozen storyboard", encoding="utf-8")
    monkeypatch.setattr(adapter, "adapter_config", lambda: {
        "shadow_enabled": True,
        "production_enabled": False,
        "legacy_fallback_on_technical": True,
    })
    prepare = Mock(return_value={"request_id": "fixture-request"})
    monkeypatch.setattr(adapter.product_review_adapter, "prepare", prepare)
    result = adapter.prepare_shadow_request(
        tmp_path / "episode",
        attempt=1,
        prompt="decision only",
        story_path=story,
        storyboard_path=board,
        rubric_paths=[],
    )
    assert result["shadow_only"] is True
    assert result["candidate_authority"] == "runtime_evidence_only"
    assert result["critic_invoked"] is False
    args = prepare.call_args.kwargs
    assert args["kind"] == "story-semantic-critic-shadow"
    assert args["host_execution"] == "codex_user_runner_shadow"
    assert args["request_metadata"]["shadow_only"] is True
    assert args["request_metadata"]["candidate_authority"] == "runtime_evidence_only"
    assert args["source_paths"] == [story, board]
    assert args["candidate_path"].as_posix().endswith(
        "meta/runtime/agent-shadow/story-semantic-critic/attempt-1-decision.json"
    )
    assert "production" not in result


def test_shadow_flag_off_disables_request_and_production_mode_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(adapter, "adapter_config", lambda: {"shadow_enabled": False, "production_enabled": False})
    assert adapter.prepare_shadow_request(tmp_path, attempt=1, prompt="x", story_path=tmp_path, storyboard_path=tmp_path) is None
    monkeypatch.setattr(adapter, "adapter_config", lambda: {"shadow_enabled": True, "production_enabled": True})
    try:
        adapter.prepare_shadow_request(tmp_path, attempt=1, prompt="x", story_path=tmp_path, storyboard_path=tmp_path)
    except adapter.CriticDecisionError:
        pass
    else:
        raise AssertionError("shadow/production overlap must fail closed")


def test_shadow_finalize_uses_existing_frozen_review_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setattr(adapter, "adapter_config", lambda: {"shadow_enabled": True, "production_enabled": False})
    finalize = Mock(return_value=(valid_decision(), {"runtime": "WORK_ISOLATED", "attempt": 1}))
    monkeypatch.setattr(adapter.product_review_adapter, "finalize_candidate", finalize)
    result = adapter.finalize_shadow_candidate(tmp_path / "episode", attempt=1)
    assert result["decision"]["decision"] == "ACCEPT_CANDIDATE"
    assert result["critic_invoked"] is None
    assert result["telemetry_complete"] is False
    assert result["model_execution"]["input_tokens"] is None
    assert result["reflection_round"] == 1
    assert result["repair_invoked"] is False
    assert result["authority_write"] is False
    assert result["gate_pass"] is False
    assert finalize.call_args.kwargs["kind"] == adapter.REQUEST_KIND
    assert finalize.call_args.kwargs["candidate_path"].as_posix().endswith(
        "meta/runtime/agent-shadow/story-semantic-critic/attempt-1-decision.json"
    )


def test_critic_telemetry_uses_completed_usage_and_runner_receipt_only():
    rows = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
        {"type": "turn.completed", "usage": {
            "input_tokens": 111, "cached_input_tokens": 31,
            "output_tokens": 27, "reasoning_output_tokens": 9,
        }},
    ]
    runner = SimpleNamespace(
        output="\n".join(json.dumps(row) for row in rows),
        remote={"elapsed_seconds": 4.25, "timed_out": False},
        returncode=0,
    )
    telemetry = adapter.execution_telemetry(
        runner, provider="codex_cli_subscription", model="gpt-5.6-luna",
        authority_capsule_read_once=True,
    )
    assert telemetry["complete"] is True
    assert telemetry["wall_seconds"] == 4.25
    assert telemetry["input_tokens"] == 111
    assert telemetry["cached_input_tokens"] == 31
    assert telemetry["output_tokens"] == 27
    assert telemetry["reasoning_output_tokens"] == 9
    assert telemetry["repeated_reads"] == 0
    incomplete = adapter.execution_telemetry(
        SimpleNamespace(output=json.dumps({"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 1}}),
                        remote={}, returncode=1),
        provider="", model="",
    )
    assert incomplete["complete"] is False
    assert incomplete["wall_seconds"] is None
    assert incomplete["cached_input_tokens"] is None
    assert incomplete["failure"] is True


def test_missing_user_runner_receipt_fails_telemetry_closed():
    result = SimpleNamespace(
        output=json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": 1, "cached_input_tokens": 0,
            "output_tokens": 1, "reasoning_output_tokens": 0,
        }}),
        returncode=0,
    )
    telemetry = adapter.execution_telemetry(result, provider="codex_user_runner", model="gpt-6-luna")
    assert telemetry["real_model_execution"] is True
    assert telemetry["wall_seconds"] is None
    assert telemetry["complete"] is False


def test_decision_prompt_is_frozen_decision_only_and_schema_bound():
    prompt = adapter.build_decision_prompt(
        attempt=2, story_text="FROZEN STORY", storyboard_text="FROZEN BOARD",
        rubric_text="FROZEN RUBRIC",
    )
    assert "FROZEN STORY" in prompt and "FROZEN BOARD" in prompt
    assert "Do not search the repository, call tools" in prompt
    assert "Return exactly one decision object" in prompt
    assert "Gate PASS" in prompt


def test_fixture_shadow_smoke_has_no_model_or_mutation_claims():
    report = adapter.fixture_shadow_smoke()
    assert report["status"] == "PASS"
    assert report["critic_invoked"] is False
    assert report["repair_invoked"] is False
    assert report["authority_write"] is False
    assert report["gate_pass"] is False
    assert report["decision_equivalent"] is True
