from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_workspace  # noqa: E402
import runtime_workspace_migration  # noqa: E402


def _write(ep: Path, rel: str, data: dict) -> None:
    path = ep / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _configure(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "ep"
    ep.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / ".storyos/runtime/episodes")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep


def test_plan_migrates_only_operational_and_derived(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/episode-state.json", {"current_state": "IDEA_LOCKED"})
    _write(ep, "meta/provider-receipts/01-1.json", {"receipt": True})
    _write(ep, "meta/runtime/next-action.json", {"action": "x"})
    _write(ep, "meta/runtime-checkpoint.json", {"last_completed": "LEGACY"})
    _write(ep, "meta/runtime/contracts/frames/01.json", {"derived": True})
    plan = runtime_workspace_migration.build_plan(ep)
    by_path = {row["path"]: row for row in plan["items"]}

    assert by_path["meta/runtime/next-action.json"]["action"] == "COPY_VERIFY_THEN_SWITCH_READ"
    assert by_path["meta/runtime-checkpoint.json"]["action"] == "COPY_VERIFY_THEN_SWITCH_READ"
    assert by_path["meta/runtime/contracts/frames/01.json"]["action"] == "COPY_VERIFY_THEN_SWITCH_READ"
    assert by_path["meta/episode-state.json"]["action"] == "KEEP_EPISODE"
    assert by_path["meta/provider-receipts/01-1.json"]["action"] == "KEEP_EPISODE"
    assert runtime_workspace_migration.validate_plan(plan) == []


def test_plan_is_dry_run_and_does_not_touch_files(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/runtime/next-action.json", {"value": 1})
    before = (ep / "meta/runtime/next-action.json").read_bytes()
    plan = runtime_workspace_migration.build_plan(ep)
    assert plan["safety"]["moves_performed"] == 0
    assert plan["safety"]["deletes_performed"] == 0
    assert (ep / "meta/runtime/next-action.json").read_bytes() == before
    assert not runtime_workspace.runtime_root().exists()


def test_repo_default_runtime_root_is_git_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/.storyos/runtime/" in ignore
    assert runtime_workspace.DEFAULT_ROOT == ROOT / ".storyos" / "runtime" / "episodes"


def test_validator_rejects_formal_evidence_migration():
    plan = {"items": [{
        "path": "meta/provider-receipts/01.json",
        "category": "FORMAL_EVIDENCE",
        "action": "COPY_VERIFY_THEN_SWITCH_READ",
        "target": "somewhere",
        "delete_source": False,
    }]}
    errors = runtime_workspace_migration.validate_plan(plan)
    assert errors == ["PROTECTED_ASSET_MIGRATION_PROPOSED:meta/provider-receipts/01.json"]


def test_explicit_copy_verifies_and_preserves_legacy(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/runtime/next-action.json", {"value": 7})
    source = ep / "meta/runtime/next-action.json"
    plan = runtime_workspace_migration.build_plan(ep)
    report = runtime_workspace_migration.execute_copy(ep, plan)
    target = runtime_workspace.workspace_path(ep, "meta/runtime/next-action.json")
    assert report["status"] == "PASS"
    assert report["copied"] == 1 and report["verified"] == 1
    assert source.is_file() and target.is_file()
    assert source.read_bytes() == target.read_bytes()
    assert runtime_workspace.source_kind(ep, "meta/runtime/next-action.json") == "runtime_workspace"


def test_copy_rerun_is_idempotent_reuse(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/runtime/next-action.json", {"value": 8})
    plan = runtime_workspace_migration.build_plan(ep)
    first = runtime_workspace_migration.execute_copy(ep, plan)
    second = runtime_workspace_migration.execute_copy(ep, plan)
    assert first["copied"] == 1
    assert second["copied"] == 0 and second["reused_verified"] == 1
    assert second["status"] == "PASS"


def test_copy_fails_closed_on_target_conflict(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/runtime/next-action.json", {"value": 9})
    plan = runtime_workspace_migration.build_plan(ep)
    target = runtime_workspace.workspace_path(ep, "meta/runtime/next-action.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"conflict":true}', encoding="utf-8")
    before = target.read_bytes()
    report = runtime_workspace_migration.execute_copy(ep, plan)
    assert report["status"] == "BLOCKED"
    assert report["copied"] == 0
    assert report["errors"] == ["TARGET_CONFLICT:meta/runtime/next-action.json"]
    assert target.read_bytes() == before


def test_copy_fails_closed_when_source_changed_after_plan(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/runtime/next-action.json", {"value": 10})
    plan = runtime_workspace_migration.build_plan(ep)
    _write(ep, "meta/runtime/next-action.json", {"value": 11})
    report = runtime_workspace_migration.execute_copy(ep, plan)
    assert report["status"] == "BLOCKED"
    assert report["errors"] == ["SOURCE_CHANGED_SINCE_PLAN:meta/runtime/next-action.json"]
    assert not runtime_workspace.workspace_path(ep, "meta/runtime/next-action.json").exists()


def test_execute_copy_migrates_ready_frame_cache_but_defers_queue(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    _write(ep, "meta/production-queue.json", {"items": []})
    _write(ep, "meta/runtime/contracts/frames/01.json", {"derived": True})
    plan = runtime_workspace_migration.build_plan(ep)
    actions = {row["path"]: row["action"] for row in plan["items"]}
    assert actions["meta/production-queue.json"] == "DEFER_CONSUMER_MIGRATION"
    assert actions["meta/runtime/contracts/frames/01.json"] == "COPY_VERIFY_THEN_SWITCH_READ"
    report = runtime_workspace_migration.execute_copy(ep, plan)
    assert report["status"] == "PASS"
    assert report["copied"] == 1 and report["verified"] == 1
    assert runtime_workspace.workspace_path(ep, "meta/runtime/contracts/frames/01.json").is_file()
    assert not runtime_workspace.workspace_path(ep, "meta/production-queue.json").exists()
