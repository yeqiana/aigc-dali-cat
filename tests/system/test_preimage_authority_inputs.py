from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import preimage_authority_snapshot as snapshot  # noqa: E402
import preimage_task_contract as tasks  # noqa: E402
import runtime_dag  # noqa: E402


def test_environment_task_embeds_story_review_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tasks.review_record_persistence,
        "load_latest",
        lambda *_args, **_kwargs: {"summary": {"passed": True}},
    )
    monkeypatch.setattr(
        tasks.runtime_request,
        "authority_for_episode",
        lambda _ep: {"topic": {"title": "x"}},
    )
    snap = {"snapshot_id": "s" * 24, "authority_sha256": {}}
    task = tasks.task_contract(tmp_path, "ENVIRONMENT_PREPARE", snap)
    assert "meta/story-semantic-review.json" not in task["required_read"]
    assert task["input_contract"]["authority_inputs"][
        "meta/story-semantic-review.json"
    ]["summary"]["passed"] is True


def test_character_task_embeds_contract_owners(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks.character_contract, "load", lambda _ep: {"status": "LOCKED"})
    monkeypatch.setattr(
        tasks.character_visual_contract,
        "load",
        lambda _ep: {"status": "LOCKED"},
    )
    monkeypatch.setattr(
        tasks.runtime_request,
        "authority_for_episode",
        lambda _ep: {"topic": {"title": "x"}},
    )
    snap = {"snapshot_id": "s" * 24, "authority_sha256": {}}
    task = tasks.task_contract(tmp_path, "CHARACTER_FINALIZE", snap)
    assert "meta/character-contract.json" not in task["required_read"]
    assert "meta/character-visual-contract.json" not in task["required_read"]
    assert task["input_contract"]["authority_inputs"][
        "meta/character-contract.json"
    ]["status"] == "LOCKED"


def test_snapshot_hashes_migrated_authorities(monkeypatch, tmp_path):
    monkeypatch.setattr(
        snapshot.character_contract,
        "authority_sha256",
        lambda _ep: "a" * 64,
    )
    monkeypatch.setattr(
        snapshot.character_visual_contract,
        "authority_sha256",
        lambda _ep: "b" * 64,
    )
    monkeypatch.setattr(
        snapshot.review_record_persistence,
        "authority_sha256",
        lambda *_args, **_kwargs: "c" * 64,
    )
    monkeypatch.setattr(
        snapshot.runtime_request,
        "authority_for_episode",
        lambda _ep: {},
    )
    values = snapshot._common(tmp_path, gates={})
    assert values["character_contract"] == "a" * 64
    assert values["character_visual_contract"] == "b" * 64
    assert values["story_semantic_review"] == "c" * 64


def test_runtime_dag_authority_hash_does_not_need_files(monkeypatch, tmp_path):
    monkeypatch.setitem(
        runtime_dag.AUTHORITY_HASHERS,
        "meta/story-semantic-review.json",
        lambda _ep: "d" * 64,
    )
    first = runtime_dag._evidence_input_hash(
        tmp_path, ["meta/story-semantic-review.json"]
    )
    second = runtime_dag._evidence_input_hash(
        tmp_path, ["meta/story-semantic-review.json"]
    )
    assert first == second
    assert not (tmp_path / "meta/story-semantic-review.json").exists()
