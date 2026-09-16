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
    _write(ep, "meta/runtime/contracts/frames/01.json", {"derived": True})
    plan = runtime_workspace_migration.build_plan(ep)
    by_path = {row["path"]: row for row in plan["items"]}

    assert by_path["meta/runtime/next-action.json"]["action"] == "COPY_VERIFY_THEN_SWITCH_READ"
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
