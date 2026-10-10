"""Native Release Critic receives bounded absolute sources; host paths stay relative."""
from __future__ import annotations

import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))
import release_preflight_review as review


def test_host_uses_relative_paths_native_uses_absolute(monkeypatch, tmp_path):
    monkeypatch.setattr(review, "ROOT", tmp_path)
    episode = tmp_path / "episodes" / "demo"
    candidate = episode / "meta" / "release-critic-candidate.json"
    monkeypatch.setattr(review, "load_manifest", lambda ep: {
        "publication": {"actual_title": "Title", "description": "Description", "topics": ["fiction"]}
    })
    rows = {"cover": {"path": "episodes/demo/media/cover.png", "sha256": "a" * 64}}
    host = review.release_critic_prompt(episode, candidate, rows)
    native = review.release_critic_prompt(episode, candidate, rows, native_codex=True)
    assert "cover: episodes/demo/media/cover.png" in host
    assert "Write ONLY valid JSON to episodes/demo/meta/release-critic-candidate.json" in host
    assert (tmp_path / "episodes/demo/media/cover.png").as_posix() in native
    assert candidate.as_posix() in native
    assert "do not explore the repository" in native
    assert "Read these release rules and evidence only:" in native
    assert "do not explore the repository" in host
