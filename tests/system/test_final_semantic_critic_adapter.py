from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import Mock

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
AGENTS = SYSTEM / "agents"
SCRIPTS = ROOT / "scripts"
for path in (SYSTEM, AGENTS, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import final_semantic_critic_adapter as critic
import frame_semantic_review
import product_review_adapter
import p3_final_semantic_critic_real_shadow_smoke as smoke


def _freeze_fixture(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    ep = repo / "episodes" / "fixture-episode"
    (ep / "meta").mkdir(parents=True)
    story = ep / "story.md"
    storyboard = ep / "storyboard.md"
    gates = ep / "meta" / "story-gates.json"
    image = ep / "frame.png"
    schema = repo / "critic_decision.schema.json"
    for path, data in ((story, "frozen story"), (storyboard, "frozen board"),
                       (gates, json.dumps({"visual": {"references": {"items": []}}})),
                       (schema, "{}")):
        path.write_text(data, encoding="utf-8")
    Image.new("RGB", (2, 2), (10, 20, 30)).save(image, format="PNG")
    monkeypatch.setattr(critic, "ROOT", repo)
    monkeypatch.setattr(critic, "DECISION_SCHEMA", schema)
    rubric_paths = []
    for source in critic.RUBRIC_PATHS:
        local = repo / source.name
        local.write_text("fixture rubric", encoding="utf-8")
        rubric_paths.append(local)
    monkeypatch.setattr(critic, "RUBRIC_PATHS", tuple(rubric_paths))
    monkeypatch.setattr(frame_semantic_review, "episode_files", lambda _ep: (story, storyboard))
    monkeypatch.setattr(frame_semantic_review, "reviewable_frame_records", lambda _ep, require_files: [{
        "frame": "01", "path": image, "path_rel": "episodes/fixture-episode/frame.png",
        "sha256": critic.sha256_file(image), "source_kind": "candidate", "ledger_status": "ORIGINAL_READY",
    }])
    monkeypatch.setattr(frame_semantic_review, "reviewable_phase4_binding_errors", lambda *_args: [])
    monkeypatch.setattr(frame_semantic_review, "episode_contract_version", lambda _ep: "2.4.0")
    monkeypatch.setattr(frame_semantic_review, "directing_v3_required", lambda _ep: False)
    monkeypatch.setattr(frame_semantic_review, "checks_for_version", lambda *_args: ["character_identity", "temporal_continuity"])
    monkeypatch.setattr(frame_semantic_review, "review_source_bindings", lambda *_args: {"contexts": {"story": "a" * 64}})
    monkeypatch.setattr(frame_semantic_review, "phase3_context_hashes", lambda *_args: {"environment_frame_sha256": "b" * 64})
    monkeypatch.setattr(frame_semantic_review.phase4_contract, "compile_frame", lambda *_args, **_kwargs: {
        "contract_sha256": "c" * 64, "character_identity": {"id": "P01"},
    })
    monkeypatch.setattr(frame_semantic_review, "stable_visual_contract", lambda _ep: {"references": {"items": []}})
    monkeypatch.setattr(frame_semantic_review, "__file__", str(story))
    return repo, ep


def test_frozen_capsule_binds_entire_frame_set_and_applicability(monkeypatch, tmp_path):
    _repo, ep = _freeze_fixture(monkeypatch, tmp_path)
    capsule = critic.build_frozen_review_capsule(ep)
    assert critic.verify_capsule_integrity(capsule) is capsule
    assert capsule["frame_set"][0]["frame"] == "01"
    assert capsule["frame_set"][0]["frame_contract_sha256"] == "c" * 64
    assert capsule["applicability"]["character_identity"]["applicable"] is True
    assert capsule["applicability"]["shot_scale_fidelity"]["applicable"] is False
    assert capsule["authority_policy"]["production_ledger_write"] is False
    assert capsule["allowed_tools"] == []


def test_capsule_tampering_is_rejected(monkeypatch, tmp_path):
    _repo, ep = _freeze_fixture(monkeypatch, tmp_path)
    capsule = critic.build_frozen_review_capsule(ep)
    capsule["frame_set"].clear()
    try:
        critic.verify_capsule_integrity(capsule)
    except critic.FinalSemanticCriticError:
        pass
    else:
        raise AssertionError("tampered capsule should fail closed")


def test_decision_contract_reuses_shared_schema_and_rejects_runtime_fields():
    valid = {"decision": "REPAIR", "issue_codes": ["IDENTITY_DRIFT"], "severity": "HIGH",
             "repair_scope": ["frame:01"], "evidence": ["frame 01 contradicts locked identity"]}
    assert critic.validate_decision(valid) == valid
    invalid = {**valid, "gate_pass": True}
    try:
        critic.validate_decision(invalid)
    except critic.FinalSemanticCriticError:
        pass
    else:
        raise AssertionError("runtime authority metadata must not enter decision payload")


def test_prompt_is_capsule_bound_and_forbids_repository_tools(monkeypatch, tmp_path):
    _repo, ep = _freeze_fixture(monkeypatch, tmp_path)
    capsule = critic.build_frozen_review_capsule(ep)
    prompt = critic.build_prompt(capsule)
    assert capsule["capsule_sha256"] in prompt
    assert "Do not browse" in prompt
    assert "Allowed tools: none" in prompt
    assert "StoryOS Gate PASS" in prompt


def test_shadow_disabled_does_not_prepare_request(monkeypatch, tmp_path):
    monkeypatch.setattr(critic, "adapter_config", lambda: {"shadow_enabled": False, "production_enabled": False})
    monkeypatch.setattr(critic, "build_frozen_review_capsule", Mock(side_effect=AssertionError("must not freeze")))
    assert critic.prepare_shadow_request(tmp_path) is None


def test_shadow_preparation_uses_separate_decision_only_request(monkeypatch, tmp_path):
    repo, ep = _freeze_fixture(monkeypatch, tmp_path)
    capsule = {"schema_version": 1, "kind": "fixture", "frame_set": [{"frame": "01"}],
               "frame_set_sha256": "a" * 64, "source_sha256": "b" * 64,
               "obligation_sha256": "c" * 64, "decision_schema_sha256": "d" * 64,
               "required_checks": ["character_identity"],
               "source_files": [{"path": "critic_decision.schema.json", "sha256": critic.sha256_file(critic.DECISION_SCHEMA)}],
               "source_bindings": {"frames": {"01": {"asset_sha256": "e" * 64}}}}
    capsule["capsule_sha256"] = critic.digest(capsule)
    monkeypatch.setattr(critic, "adapter_config", lambda: {"shadow_enabled": True, "production_enabled": False})
    monkeypatch.setattr(critic, "build_frozen_review_capsule", lambda _ep: capsule)
    monkeypatch.setattr(critic, "final_critic_visual_attachment_plan", lambda *_a, **_k: {
        "text_sources": [], "visual_attachment_files": [], "preflight_status": "PASS",
    })
    request_file = ep / "request.json"
    request_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(product_review_adapter, "request_path", lambda *_a, **_k: request_file)

    def prepare(_ep, **kwargs):
        assert kwargs["kind"] == "final-semantic-critic-shadow"
        assert kwargs["host_execution"] == "codex_user_runner_shadow"
        assert kwargs["request_metadata"]["shadow_only"] is True
        assert kwargs["request_metadata"]["allowed_tools"] == []
        return {"request_id": "final-shadow-a1", "status": "AWAITING",
                "candidate_path": "episodes/fixture-episode/meta/runtime/agent-shadow/final-semantic-critic/attempt-1-decision.json",
                "request_metadata": kwargs["request_metadata"], "request_fingerprint": "fixture-fingerprint"}

    monkeypatch.setattr(product_review_adapter, "prepare", prepare)
    result = critic.prepare_shadow_request(ep)
    assert result["request_id"] == "final-shadow-a1"
    assert result["request_snapshot_sha256"]
    assert (ep / "meta/runtime/agent-shadow/final-semantic-critic/attempt-1-request-snapshot.json").is_file()


def test_shadow_and_production_enabled_fail_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(critic, "adapter_config", lambda: {"shadow_enabled": True, "production_enabled": True})
    try:
        critic.prepare_shadow_request(tmp_path)
    except critic.FinalSemanticCriticError as exc:
        assert "cannot both" in str(exc)
    else:
        raise AssertionError("conflicting flags must fail closed")


def test_comparison_records_disagreement_without_ground_truth():
    result = critic._comparison({"decision": "PASS", "issue_codes": []},
                                {"decision": "REPAIR", "issue_codes": ["TEMPORAL_CONTRADICTION"]})
    assert result["decision_disagreement"] is True
    assert result["issue_disagreement"] is True
    assert result["ground_truth_available"] is False


def test_real_smoke_reports_story_and_storyboard_source_mismatch_together(monkeypatch, tmp_path):
    _repo, ep = _freeze_fixture(monkeypatch, tmp_path)
    review = {
        "story_sha256": "a" * 64,
        "storyboard_sha256": "b" * 64,
        "visual_contract_sha256": frame_semantic_review.sha256_json(
            frame_semantic_review.stable_visual_contract(ep)
        ),
    }
    result = smoke.canonical_source_validation(review, ep)
    assert result == {"story_match": False, "storyboard_match": False, "visual_contract_match": True}


def test_canonical_shadow_schedule_failure_is_non_blocking(monkeypatch, capsys):
    monkeypatch.setattr(critic, "schedule_shadow_best_effort", Mock(side_effect=RuntimeError("test failure")))
    result = frame_semantic_review._prepare_final_semantic_shadow_best_effort(Path("unused"), 1)
    assert result is None
    assert "Shadow wiring unavailable" in capsys.readouterr().out


def test_deterministic_fixture_cases_use_existing_issue_taxonomy():
    path = ROOT / "tests/fixtures/p3_final_semantic_critic/cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    allowed = frame_semantic_review.ISSUE_CODES | frame_semantic_review.GLOBAL_CLOSURE_ISSUE_CODES
    assert payload["fixture_only"] is True
    assert len(payload["cases"]) >= 7
    for case in payload["cases"]:
        assert set(case["reference_issue_codes"]).issubset(allowed)
