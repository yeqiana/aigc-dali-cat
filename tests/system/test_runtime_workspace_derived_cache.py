from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import prompt_package  # noqa: E402
import runtime_workspace  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    ep.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep


def test_prompt_package_reads_legacy_then_writes_workspace(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    prompt = tmp_path / "01.txt"
    prompt.write_text("same scene", encoding="utf-8")
    rel = prompt_package.REL / "01.json"
    legacy = ep / rel
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text('{"scene_prompt_sha256":"legacy","frame_contract_sha256":"old"}', encoding="utf-8")
    monkeypatch.setattr(prompt_package.frame_contract, "compile_frame", lambda *_args, **_kwargs: {
        "contract_sha256": "new", "storyboard_frame": {}, "prompt_contract": "contract"
    })
    monkeypatch.setattr(prompt_package.image_model_policy, "for_episode", lambda _ep: {"model": "test"})

    data = prompt_package.compile_frame(ep, 1, prompt, write=True)
    target = runtime_workspace.workspace_path(ep, rel)
    assert data["frame_contract_sha256"] == "new"
    assert target.is_file()
    assert legacy.is_file()
    assert runtime_workspace.source_kind(ep, rel) == "runtime_workspace"


def test_frame_contract_externalization_is_not_partial():
    # Frame Contract caches also feed DAG evidence, final snapshot and repair
    # mutation contracts.  Keep their writer on the legacy boundary until those
    # consumers migrate in one atomic change set; prompt packages are independent.
    assert prompt_package.REL.as_posix() == "meta/runtime/prompt-packages"
