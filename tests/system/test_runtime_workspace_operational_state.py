from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runner_state_store  # noqa: E402
import runtime_resume_token  # noqa: E402
import runtime_workspace  # noqa: E402
import workflow_step_protocol as proto  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    ep.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep


def test_resume_token_workspace_write_with_legacy_fallback(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = ep / runtime_resume_token.REL
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text('{"stage":"LEGACY"}', encoding="utf-8")
    assert runtime_resume_token.load(ep)["stage"] == "LEGACY"
    runtime_resume_token.save(ep, stage="IDEA_LOCKED", step="CREATIVE_STORY", attempt=1)
    assert runtime_resume_token.load(ep)["stage"] == "IDEA_LOCKED"
    assert runtime_workspace.workspace_path(ep, runtime_resume_token.REL).is_file()
    assert legacy.read_text(encoding="utf-8") == '{"stage":"LEGACY"}'


def test_runner_state_workspace_write_and_legacy_fallback(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = ep / runner_state_store.REL
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text('{"status":"YIELDED"}', encoding="utf-8")
    assert runner_state_store.load(ep)["status"] == "YIELDED"
    runner_state_store.save(ep, status="RUNNING")
    assert runner_state_store.load(ep)["status"] == "RUNNING"
    assert runtime_workspace.workspace_path(ep, runner_state_store.REL).is_file()


def test_dag_state_workspace_write_and_legacy_fallback(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = ep / proto.DAG_REL
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text('{"steps":{"old":{}},"history":[]}', encoding="utf-8")
    assert "old" in proto.load_state(ep)["steps"]
    result = proto.StepResult("new", "PASS", 1, "a", "b", 0.1)
    proto.save_result(ep, result)
    state = proto.load_state(ep)
    assert state["steps"]["new"]["status"] == "PASS"
    assert runtime_workspace.workspace_path(ep, proto.DAG_REL).is_file()
    assert "old" in state["steps"]
