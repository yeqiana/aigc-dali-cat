from __future__ import annotations

import copy
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_validation_input as prep


def _attempt():
    return {
        "attempts_consumed": 0,
        "remaining_attempts": 2,
        "active_attempt_index": None,
    }


def test_scene_prompt_stays_inside_formal_generation_budget():
    assert len(prep.SCENE_PROMPT) <= 260
    assert len(prep.SCENE_PROMPT.encode("utf-8")) <= 900


def test_source_descriptor_is_stable_and_non_promotable(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    profile = tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")
    with mock.patch.object(
        prep.visual_profile_registry, "registry_entry",
        return_value={"id": "M00", "path": "profile.json"},
    ):
        a = prep.fixture_source_descriptor(tmp_path / "ep")
        b = prep.fixture_source_descriptor(tmp_path / "ep")
    assert a == b
    assert a["tool_version"] == "2.1.0"
    assert a["body_frame_count"] == 1
    assert a["promotable"] is False
    assert a["release_eligible"] is False
    assert a["stage_authority"] is False
    assert len(a["source_sha256"]) == 64


def test_prepare_uses_existing_compilers_queue_and_consumes_no_attempt(tmp_path, monkeypatch):
    ep = tmp_path / ".codex_tmp" / "phase5a" / "phase5a-validation-e3-test"
    (ep / "meta").mkdir(parents=True)
    profile = tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(
        prep.canary, "validate_workspace",
        lambda *_a, **_k: (ep, {"workspace_class": "TEST_ONLY"}),
    )
    monkeypatch.setattr(
        prep.canary, "claim_global_canary",
        lambda *_a, **_k: {"validation_epoch": 3, "resumed": True},
    )
    monkeypatch.setattr(
        prep.visual_profile_registry, "registry_entry",
        lambda *_a, **_k: {"id": "M00", "path": "profile.json"},
    )
    request = {
        "mode": "image_continue",
        "story_input": {"mode": "locked_story"},
        "provenance": {"original_request": prep.RUNTIME_REQUEST_TEXT},
    }
    monkeypatch.setattr(prep.runtime_request, "effective_for_episode", lambda _ep: request)
    monkeypatch.setattr(
        prep.canary, "bind_and_freeze",
        lambda *_a, **_k: {
            "runtime_request_id": "request-1",
            "policy_version": "p1",
            "policy_sha256": "p" * 64,
        },
    )
    monkeypatch.setattr(
        prep.model_policy, "resolve",
        lambda *_a, **_k: {"model": "gpt-image-2.5-flare", "quality": "high"},
    )
    monkeypatch.setattr(
        prep.frame_contract, "compile_frame",
        lambda *_a, **_k: {"contract_sha256": "c" * 64},
    )
    package = {
        "package_sha256": "q" * 64,
        "scene_prompt_sha256": "s" * 64,
        "frame_contract_sha256": "c" * 64,
    }
    monkeypatch.setattr(
        prep.prompt_package_persistence, "load_latest",
        lambda *_a, **_k: package,
    )
    queue = {
        "items": [{
            "id": "queue-1", "frame": 1, "kind": "original",
            "status": "queued",
            "prompt_package": {
                "package_sha256": "q" * 64,
                "frame_contract_sha256": "c" * 64,
            },
        }]
    }
    import_calls = []
    monkeypatch.setattr(
        prep.image_scheduler, "import_batch",
        lambda *_a, **_k: import_calls.append(True) or {"added": [1], "skipped": []},
    )
    monkeypatch.setattr(prep.scheduler_core, "load_queue", lambda _ep: copy.deepcopy(queue))
    monkeypatch.setattr(
        prep.logical_asset_identity, "frame_asset_key",
        lambda *_a, **_k: "_external/test/frame-01",
    )
    monkeypatch.setattr(
        prep.generation_attempt_authority, "load_asset_state",
        lambda *_a, **_k: _attempt(),
    )

    row = prep.prepare(ep, canary_id="phase5a-validation-e3-test")
    assert import_calls == [True]
    assert row["queue_item_id"] == "queue-1"
    assert row["attempts_consumed"] == 0
    assert row["remaining_attempts"] == 2
    assert row["active_attempt_index"] is None
    assert row["provider_calls"] == 0
    assert row["model_calls"] == 0



def test_prepare_recovers_missing_prompt_package_without_generation_attempt(tmp_path, monkeypatch):
    ep = tmp_path / ".codex_tmp" / "phase5a" / "phase5a-validation-e3-test"
    (ep / "meta").mkdir(parents=True)
    profile = tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(prep.canary, "validate_workspace", lambda *_a, **_k: (ep, {}))
    monkeypatch.setattr(prep.canary, "claim_global_canary", lambda *_a, **_k: {"validation_epoch": 3})
    monkeypatch.setattr(prep.visual_profile_registry, "registry_entry", lambda *_a, **_k: {"path": "profile.json"})
    request = {
        "mode": "image_continue",
        "story_input": {"mode": "locked_story"},
        "provenance": {"original_request": prep.RUNTIME_REQUEST_TEXT},
    }
    monkeypatch.setattr(prep.runtime_request, "effective_for_episode", lambda _ep: request)
    monkeypatch.setattr(prep.canary, "bind_and_freeze", lambda *_a, **_k: {
        "runtime_request_id": "request-1", "policy_sha256": "p" * 64,
    })
    monkeypatch.setattr(prep.model_policy, "resolve", lambda *_a, **_k: {
        "model": "gpt-image-2.5-flare", "quality": "high",
    })
    monkeypatch.setattr(prep.frame_contract, "compile_frame", lambda *_a, **_k: {
        "contract_sha256": "c" * 64,
    })
    monkeypatch.setattr(prep.image_scheduler, "import_batch", lambda *_a, **_k: {"added": [], "skipped": [1]})
    queue = {"items": [{
        "id": "queue-1", "frame": 1, "kind": "original", "status": "queued",
        "prompt_package": {
            "package_sha256": "q" * 64,
            "frame_contract_sha256": "c" * 64,
        },
    }]}
    monkeypatch.setattr(prep.scheduler_core, "load_queue", lambda _ep: copy.deepcopy(queue))
    package = {
        "package_sha256": "q" * 64,
        "scene_prompt_sha256": "s" * 64,
        "frame_contract_sha256": "c" * 64,
    }
    loads = iter([None, package, package])
    monkeypatch.setattr(prep.prompt_package_persistence, "load_latest", lambda *_a, **_k: next(loads))
    compile_calls = []
    monkeypatch.setattr(
        prep.prompt_package, "compile_frame",
        lambda *_a, **_k: compile_calls.append(True) or package,
    )
    monkeypatch.setattr(prep.logical_asset_identity, "frame_asset_key", lambda *_a, **_k: "_external/test/frame-01")
    monkeypatch.setattr(prep.generation_attempt_authority, "load_asset_state", lambda *_a, **_k: _attempt())

    row = prep.prepare(ep, canary_id="phase5a-validation-e3-test")

    assert compile_calls == [True]
    assert row["attempts_consumed"] == 0
    assert row["remaining_attempts"] == 2
    assert row["provider_calls"] == 0
    assert row["model_calls"] == 0


def test_prepare_readmits_stale_zero_attempt_queue_projection(tmp_path, monkeypatch):
    ep = tmp_path / ".codex_tmp" / "phase5a" / "phase5a-validation-e3-test"
    (ep / "meta").mkdir(parents=True)
    profile = tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(prep.canary, "validate_workspace", lambda *_a, **_k: (ep, {}))
    monkeypatch.setattr(prep.canary, "claim_global_canary", lambda *_a, **_k: {"validation_epoch": 3})
    monkeypatch.setattr(prep.visual_profile_registry, "registry_entry", lambda *_a, **_k: {"path": "profile.json"})
    request = {
        "mode": "image_continue",
        "story_input": {"mode": "locked_story"},
        "provenance": {"original_request": prep.RUNTIME_REQUEST_TEXT},
    }
    monkeypatch.setattr(prep.runtime_request, "effective_for_episode", lambda _ep: request)
    monkeypatch.setattr(prep.canary, "bind_and_freeze", lambda *_a, **_k: {
        "runtime_request_id": "request-1",
        "policy_sha256": "p" * 64,
        "payload": {"model": "gpt-image-2.5-flare", "quality": "high", "strict_model": False},
    })
    monkeypatch.setattr(prep.model_policy, "resolve", lambda *_a, **_k: {
        "model": "gpt-image-2.5-flare", "quality": "high", "strict_model": False,
    })
    monkeypatch.setattr(prep.frame_contract, "compile_frame", lambda *_a, **_k: {
        "contract_sha256": "n" * 64,
    })
    monkeypatch.setattr(prep.image_scheduler, "import_batch", lambda *_a, **_k: {"added": [], "skipped": [1]})
    old_queue = {"items": [{
        "id": "old-queue", "frame": 1, "kind": "original", "scope": "batch",
        "status": "external_blocked",
        "prompt_package": {"package_sha256": "o" * 64, "frame_contract_sha256": "o" * 64},
    }]}
    mixed_queue = {"items": [
        copy.deepcopy(old_queue["items"][0]),
        {
            "id": "new-queue", "frame": 1, "kind": "original", "scope": "batch",
            "status": "queued",
            "prompt_package": {"package_sha256": "q" * 64, "frame_contract_sha256": "n" * 64},
        },
    ]}
    final_queue = {"items": [
        {**copy.deepcopy(old_queue["items"][0]), "status": "superseded"},
        copy.deepcopy(mixed_queue["items"][1]),
    ]}
    queues = iter([copy.deepcopy(old_queue), mixed_queue, final_queue])
    monkeypatch.setattr(prep.scheduler_core, "load_queue", lambda _ep: next(queues))
    monkeypatch.setattr(prep.scheduler_core, "save_queue", lambda *_a, **_k: None)
    class _Lock:
        def __enter__(self): return self
        def __exit__(self, *_a): return False
    monkeypatch.setattr(prep.scheduler_core, "queue_transaction", lambda *_a, **_k: _Lock())
    monkeypatch.setattr(prep.scheduler_core, "now", lambda: "2026-10-02T20:00:00+08:00")
    package = {
        "package_sha256": "q" * 64,
        "scene_prompt_sha256": "s" * 64,
        "frame_contract_sha256": "n" * 64,
    }
    monkeypatch.setattr(prep.prompt_package_persistence, "load_latest", lambda *_a, **_k: package)
    monkeypatch.setattr(prep.logical_asset_identity, "frame_asset_key", lambda *_a, **_k: "_external/test/frame-01")
    monkeypatch.setattr(prep.generation_attempt_authority, "load_asset_state", lambda *_a, **_k: _attempt())
    monkeypatch.setattr(prep.image_scheduler, "contract_references", lambda *_a, **_k: [])
    monkeypatch.setattr(prep.image_scheduler, "directive_dependency", lambda *_a, **_k: [])
    readmissions = []
    monkeypatch.setattr(prep.image_scheduler, "add_item", lambda *_a, **kwargs: readmissions.append(kwargs) or mixed_queue["items"][1])

    row = prep.prepare(ep, canary_id="phase5a-validation-e3-test")

    assert len(readmissions) == 1
    assert readmissions[0]["replace"] is True
    assert readmissions[0]["model"] == "gpt-image-2.5-flare"
    assert row["queue_item_id"] == "new-queue"
    assert row["queue_status"] == "queued"
    assert row["attempts_consumed"] == 0
    assert row["remaining_attempts"] == 2

def test_prepare_fails_closed_if_attempt_was_consumed(tmp_path, monkeypatch):
    ep = tmp_path / ".codex_tmp" / "phase5a" / "phase5a-validation-e3-test"
    (ep / "meta").mkdir(parents=True)
    profile = tmp_path / "profile.json"
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(prep.canary, "validate_workspace", lambda *_a, **_k: (ep, {}))
    monkeypatch.setattr(prep.canary, "claim_global_canary", lambda *_a, **_k: {"validation_epoch": 3})
    monkeypatch.setattr(prep.visual_profile_registry, "registry_entry", lambda *_a, **_k: {"path": "profile.json"})
    request = {
        "mode": "image_continue",
        "story_input": {"mode": "locked_story"},
        "provenance": {"original_request": prep.RUNTIME_REQUEST_TEXT},
    }
    monkeypatch.setattr(prep.runtime_request, "effective_for_episode", lambda _ep: request)
    monkeypatch.setattr(prep.canary, "bind_and_freeze", lambda *_a, **_k: {
        "runtime_request_id": "request-1", "policy_sha256": "p" * 64,
    })
    monkeypatch.setattr(prep.model_policy, "resolve", lambda *_a, **_k: {
        "model": "gpt-image-2.5-flare", "quality": "high",
    })
    monkeypatch.setattr(prep.frame_contract, "compile_frame", lambda *_a, **_k: {
        "contract_sha256": "c" * 64,
    })
    monkeypatch.setattr(prep.image_scheduler, "import_batch", lambda *_a, **_k: {})
    monkeypatch.setattr(prep.scheduler_core, "load_queue", lambda _ep: {
        "items": [{
            "id": "queue-1", "frame": 1, "kind": "original", "status": "queued",
            "prompt_package": {
                "package_sha256": "q" * 64,
                "frame_contract_sha256": "c" * 64,
            },
        }]
    })
    monkeypatch.setattr(prep.prompt_package_persistence, "load_latest", lambda *_a, **_k: {
        "package_sha256": "q" * 64,
        "scene_prompt_sha256": "s" * 64,
        "frame_contract_sha256": "c" * 64,
    })
    monkeypatch.setattr(prep.logical_asset_identity, "frame_asset_key", lambda *_a, **_k: "_external/test/frame-01")
    monkeypatch.setattr(prep.generation_attempt_authority, "load_asset_state", lambda *_a, **_k: {
        "attempts_consumed": 1, "remaining_attempts": 1, "active_attempt_index": None,
    })
    try:
        prep.prepare(ep, canary_id="phase5a-validation-e3-test")
    except prep.ValidationInputError as exc:
        assert "CONSUMED_ATTEMPT" in str(exc)
    else:
        raise AssertionError("consumed Attempt must fail closed")
