"""Native Story Semantic critic uses a fresh authenticated runner home."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_critic_runner
import story_review


def test_shared_critic_runner_forwards_isolated_home(tmp_path, monkeypatch):
    calls = []

    def runner(cmd, **kwargs):
        calls.append((cmd, kwargs))
        kwargs["stdout"].write('{"type":"turn.completed"}\n')
        return SimpleNamespace(returncode=0, remote={"transport_route": "native_codex"})

    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "run_model_codex", runner)
    monkeypatch.setattr(codex_critic_runner, "build_command", lambda **kw: ["codex", "exec"])
    log = tmp_path / "critic.jsonl"
    result = codex_critic_runner.launch(
        "review prompt", codex=Path("codex"), root=tmp_path,
        timeout=30, log_path=log, codex_home_mode="isolated",
    )
    assert result.returncode == 0
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs["codex_home_mode"] == "isolated"
    assert kwargs["task_type"] == "critic"
    assert json.loads(log.read_text(encoding="utf-8"))["type"] == "turn.completed"


def test_shared_critic_runner_default_remains_inherit(tmp_path, monkeypatch):
    calls = []

    def runner(cmd, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(returncode=1, remote={})

    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "run_model_codex", runner)
    monkeypatch.setattr(codex_critic_runner, "build_command", lambda **kw: ["codex", "exec"])
    result = codex_critic_runner.launch(
        "review prompt", codex=Path("codex"), root=tmp_path, timeout=30,
    )
    assert result.returncode == 1
    assert calls[0]["codex_home_mode"] == "inherit"


@pytest.mark.parametrize("returncode", [0, 1])
def test_story_semantic_critic_isolated_and_fail_closed(tmp_path, monkeypatch, returncode):
    ep = tmp_path / "episode"
    (ep / "docs").mkdir(parents=True)
    (ep / "meta").mkdir()
    (ep / "docs/story.md").write_text("real source story", encoding="utf-8")
    (ep / "docs/storyboard.md").write_text("real source storyboard", encoding="utf-8")
    files = (ep / "docs/story.md", ep / "docs/storyboard.md")
    launches = []
    monkeypatch.setattr(story_review, "ROOT", tmp_path)
    monkeypatch.setattr(story_review, "story_paths", lambda _ep: files)
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: False)
    monkeypatch.setattr(story_review, "critic_prompt", lambda *args: "review prompt")
    monkeypatch.setattr(story_review.runtime_router, "detect", lambda: ("CODEX", "test"))
    monkeypatch.setattr(story_review, "resolve_codex", lambda raw: Path("codex"))
    monkeypatch.setattr(story_review, "read_json", lambda path: {})
    monkeypatch.setattr(story_review.runtime_provenance, "build_critic_provenance",
                        lambda *args, **kwargs: {"runtime": "CODEX_ISOLATED", "attempt": 1})
    finalized = []
    monkeypatch.setattr(story_review, "_finalize_review", lambda *args, **kw: (
        finalized.append((args, kw)) or 0
    ))

    def fake_launch(prompt, **kwargs):
        launches.append(kwargs)
        if returncode == 0:
            candidate = kwargs["output_path"]
            candidate.write_text('{"summary":{"passed":true}}', encoding="utf-8")
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(story_review.codex_critic_runner, "launch", fake_launch)
    if returncode:
        with pytest.raises(RuntimeError, match="isolated story critic failed"):
            story_review.run_critic(ep, attempt=1, codex_raw="codex")
        assert not finalized
    else:
        assert story_review.run_critic(ep, attempt=1, codex_raw="codex") == 0
        assert len(finalized) == 1
    assert len(launches) == 1
    assert launches[0]["codex_home_mode"] == "isolated"
    assert launches[0]["sandbox"] == "workspace-write"
