from __future__ import annotations

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "episodes/_system"))
import inflight_codex_task
import model_policy_persistence
import runtime_dag


@pytest.fixture
def inflight_identity():
    return {
        "source_sha256": "source-a",
        "model_role": "story.authoring",
        "effective_model": "gpt-6-luna",
        "reasoning_effort": "high",
        "model_policy_sha256": "policy-a",
        "runtime_request_sha": "request-a",
        "evidence_sha256": "evidence-a",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_sha256", "source-b"),
        ("model_role", "release"),
        ("effective_model", "gpt-6-luna-v2"),
        ("reasoning_effort", "medium"),
        ("model_policy_sha256", "policy-b"),
        ("runtime_request_sha", "request-b"),
        ("evidence_sha256", "evidence-b"),
    ],
)
def test_inflight_fingerprint_is_bound_to_model_policy_identity(inflight_identity, field, value):
    baseline = inflight_codex_task.fingerprint(step="CREATIVE_STORY", prompt="same", **inflight_identity)
    changed = inflight_codex_task.fingerprint(
        step="CREATIVE_STORY", prompt="same", **{**inflight_identity, field: value}
    )
    assert baseline != changed


def test_runtime_step_hash_binds_request_evidence_policy_and_resolved_role(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_dag, "_evidence_input_hash", lambda ep, paths: "evidence-a")
    monkeypatch.setattr(runtime_dag.runtime_request, "authority_for_episode", lambda ep: {"request": "a"})
    monkeypatch.setattr(runtime_dag.runtime_request, "authority_sha256", lambda request: "request-a")
    identity = {
        "model_policy_sha256": "policy-a",
        "resolved_role": "story.authoring",
        "effective_model": "gpt-6-luna",
        "reasoning_effort": "high",
    }
    monkeypatch.setattr(runtime_dag, "_model_identity", lambda ep, role: {**identity, "resolved_role": role})

    baseline = runtime_dag._step_input_hash(tmp_path, [], resolved_role="story.authoring")
    assert baseline != runtime_dag._step_input_hash(tmp_path, [], resolved_role="release")

    monkeypatch.setattr(runtime_dag.runtime_request, "authority_sha256", lambda request: "request-b")
    assert baseline != runtime_dag._step_input_hash(tmp_path, [], resolved_role="story.authoring")

    monkeypatch.setattr(runtime_dag.runtime_request, "authority_sha256", lambda request: "request-a")
    monkeypatch.setattr(runtime_dag, "_evidence_input_hash", lambda ep, paths: "evidence-b")
    assert baseline != runtime_dag._step_input_hash(tmp_path, [], resolved_role="story.authoring")

    monkeypatch.setattr(runtime_dag, "_evidence_input_hash", lambda ep, paths: "evidence-a")
    monkeypatch.setattr(runtime_dag, "_model_identity", lambda ep, role: {**identity, "model_policy_sha256": "policy-b", "resolved_role": role})
    assert baseline != runtime_dag._step_input_hash(tmp_path, [], resolved_role="story.authoring")


def test_episode_model_policy_freeze_is_immutable_and_uses_contract_store(monkeypatch, tmp_path):
    records = {}

    def load_latest(ep, contract_type, *, legacy_path=None):
        assert contract_type == "MODEL_POLICY"
        return records.get(str(ep))

    def save(ep, contract_type, legacy_rel, payload, **kwargs):
        assert contract_type == "MODEL_POLICY"
        records[str(ep)] = dict(payload)
        return {"mode": "mysql", "mysql_written": True}

    monkeypatch.setattr(model_policy_persistence.episode_contract_persistence, "load_latest", load_latest)
    monkeypatch.setattr(model_policy_persistence.episode_contract_persistence, "save", save)
    monkeypatch.setattr(
        model_policy_persistence.runtime_workspace,
        "write_json",
        lambda *args, **kwargs: pytest.fail("mysql freeze must not write a local projection"),
    )

    payload = {
        "schema_version": 1,
        "policy_version": "lean-v1",
        "bound_at": "2026-09-30T00:00:00+08:00",
        "profiles": {"authoring": {"model": "gpt-6-luna", "reasoning_effort": "high"}},
        "role_aliases": {"story.authoring": "authoring"},
        "fallback_candidates": {"authoring": []},
        "policy_sha256": "",
    }
    import hashlib
    import json
    core = {key: payload[key] for key in ("policy_version", "profiles", "role_aliases")}
    payload["policy_sha256"] = hashlib.sha256(
        json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    first = model_policy_persistence.freeze(tmp_path, payload)
    second = model_policy_persistence.freeze(tmp_path, payload)
    assert first["created"] is True
    assert second["created"] is False
    assert second["policy_sha256"] == payload["policy_sha256"]
    assert records[str(tmp_path.resolve())] == payload
    assert not (tmp_path / model_policy_persistence.REL).exists()
    assert model_policy_persistence.load(tmp_path) == payload

    changed = {**payload, "profiles": {"authoring": {"model": "different"}}}
    changed_core = {key: changed[key] for key in ("policy_version", "profiles", "role_aliases")}
    changed["policy_sha256"] = hashlib.sha256(
        json.dumps(changed_core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="already frozen"):
        model_policy_persistence.freeze(tmp_path, changed)


def test_local_projection_is_neither_required_nor_authoritative(monkeypatch, tmp_path):
    projection = tmp_path / model_policy_persistence.REL
    projection.parent.mkdir(parents=True)
    projection.write_text("{malformed local projection", encoding="utf-8")

    monkeypatch.setattr(
        model_policy_persistence.episode_contract_persistence,
        "load_latest",
        lambda ep, contract_type, *, legacy_path=None: None,
    )
    assert model_policy_persistence.load(tmp_path) is None

    authoritative = {
        "policy_version": "lean-v1",
        "profiles": {"authoring": {"model": "gpt-6-luna", "reasoning_effort": "high"}},
        "role_aliases": {"story.authoring": "authoring"},
    }
    import hashlib
    import json
    authoritative["policy_sha256"] = hashlib.sha256(
        json.dumps(authoritative, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    monkeypatch.setattr(
        model_policy_persistence.episode_contract_persistence,
        "load_latest",
        lambda ep, contract_type, *, legacy_path=None: authoritative,
    )
    assert model_policy_persistence.load(tmp_path) == authoritative


def test_runtime_request_bound_policy_freezes_before_scheduler_dispatch(monkeypatch, tmp_path):
    import model_policy

    calls = []
    monkeypatch.setattr(runtime_dag.runtime_request, "authority_for_episode", lambda ep: {"request_id": "bound"})
    monkeypatch.setattr(model_policy, "freeze_for_episode", lambda ep: calls.append(("freeze", ep)))
    monkeypatch.setattr(model_policy, "validate_bound_policy", lambda ep: calls.append(("validate", ep)) or [])
    assert runtime_dag._freeze_model_policy_before_dispatch(tmp_path) == []
    assert [name for name, _ in calls] == ["freeze", "validate"]

    calls.clear()
    monkeypatch.setattr(runtime_dag.runtime_request, "authority_for_episode", lambda ep: None)
    assert runtime_dag._freeze_model_policy_before_dispatch(tmp_path) == [
        "Runtime Request is not bound; Model Policy cannot be frozen before dispatch"
    ]
    assert calls == []

    monkeypatch.setattr(runtime_dag.runtime_request, "authority_for_episode", lambda ep: {"request_id": "bound"})
    monkeypatch.setattr(model_policy, "validate_bound_policy", lambda ep: ["episode model policy SHA differs from expected policy"])
    assert runtime_dag._freeze_model_policy_before_dispatch(tmp_path) == [
        "episode model policy SHA differs from expected policy"
    ]
