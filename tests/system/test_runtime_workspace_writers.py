from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import effective_config  # noqa: E402
import execution_capsule  # noqa: E402
import runtime_workspace  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    (ep / "meta").mkdir(parents=True)
    (ep / "meta/episode-state.json").write_text('{"current_state":"IDEA_LOCKED"}', encoding="utf-8")
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep


def test_effective_config_writes_only_runtime_workspace(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    monkeypatch.setattr(effective_config.runtime_portability, "assert_episode_directory", lambda _: None)
    effective_config.write(ep)
    assert runtime_workspace.workspace_path(ep, effective_config.REL).is_file()
    assert not (ep / effective_config.REL).exists()


def test_execution_capsule_uses_runtime_workspace_writer(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    step = next(iter(execution_capsule.STEP_EVIDENCE))
    execution_capsule.compile_capsule(ep, step, write=True)
    expected = runtime_workspace.workspace_path(ep, execution_capsule.REL / f"{step.lower()}.json")
    assert expected.is_file()
    assert not (ep / execution_capsule.REL / f"{step.lower()}.json").exists()
