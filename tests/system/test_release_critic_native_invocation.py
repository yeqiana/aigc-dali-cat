"""Release Critic native Codex command is episode scoped without paid execution."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))
import release_preflight_review as review


def test_native_release_exec_receives_scoped_cwd_and_absolute_inputs(monkeypatch, tmp_path):
    ep = tmp_path / "episodes" / "fixture"
    (ep / "meta").mkdir(parents=True)
    monkeypatch.setattr(review, "ROOT", tmp_path)
    monkeypatch.setattr(review, "ep_path", lambda raw: ep)
    monkeypatch.setattr(review, "release_hashes", lambda episode: {
        "cover": {"path": "episodes/fixture/cover.png", "sha256": "a" * 64}})
    monkeypatch.setattr(review, "load_manifest", lambda episode: {
        "publication": {"actual_title": "T", "description": "D", "topics": []}})
    monkeypatch.setattr(review.runtime_router, "detect", lambda: ("CODEX", "fixture"))
    monkeypatch.setattr(review, "resolve_codex", lambda raw: Path("codex"))
    monkeypatch.setattr(review, "prefix", lambda codex: ["codex"])
    monkeypatch.setattr(review.codex_critic_runner, "default_sandbox", lambda: "workspace-write")
    observed = []

    def no_model(*args, **kwargs):
        observed.append((args, kwargs))
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(review.codex_user_runner, "run_model_codex", no_model)
    with pytest.raises(RuntimeError, match="release critic failed rc=1"):
        review.cmd_run_release_critic(
            argparse.Namespace(episode_dir=str(ep), codex=None, timeout=30))
    assert len(observed) == 1
    args, kwargs = observed[0]
    command = args[0]
    assert command[command.index("-C") + 1] == str(ep)
    assert command[-1] == "-"
    assert "--ephemeral" in command
    assert kwargs["task_type"] == "review"
    assert kwargs["input"].find((tmp_path / "episodes/fixture/cover.png").as_posix()) >= 0
    assert str((ep / review.RELEASE_CANDIDATE_REL).resolve().as_posix()) in kwargs["input"]


def test_host_review_still_uses_host_adapter_not_codex(monkeypatch, tmp_path):
    ep = tmp_path / "episodes" / "fixture"
    (ep / "meta").mkdir(parents=True)
    monkeypatch.setattr(review, "ROOT", tmp_path)
    monkeypatch.setattr(review, "ep_path", lambda raw: ep)
    monkeypatch.setattr(review, "release_hashes", lambda episode: {
        "cover": {"path": "episodes/fixture/cover.png", "sha256": "a" * 64}})
    monkeypatch.setattr(review, "load_manifest", lambda episode: {
        "publication": {"actual_title": "T", "description": "D", "topics": []}})
    monkeypatch.setattr(review.runtime_router, "detect", lambda: ("WORK", "fixture"))
    monkeypatch.setattr(review.product_review_adapter, "prepare", lambda *a, **kw: {
        "prompt": kw["prompt"], "sources": [str(p) for p in kw["source_paths"]]})
    monkeypatch.setattr(review.codex_user_runner, "run_model_codex",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("model called")))
    code = review.cmd_run_release_critic(
        argparse.Namespace(episode_dir=str(ep), codex=None, timeout=30))
    assert code == review.product_review_adapter.HOST_ACTION_REQUIRED_RC
