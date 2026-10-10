"""A retired Episode cannot donate its business ID to another paid run."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_creator


def _root(tmp_path):
    parent = tmp_path / "episodes" / "00_独立篇"
    parent.mkdir(parents=True)
    (parent / "04_未交的答卷").mkdir()
    return parent


def test_mysql_retired_namespace_reserves_missing_05(tmp_path, monkeypatch):
    parent = _root(tmp_path)
    monkeypatch.setattr(story_creator.episode_state_persistence, "authority_mode", lambda: "mysql")
    monkeypatch.setattr(story_creator.episode_state_persistence, "list_episode_namespaces",
                        lambda: ["00_独立篇/05_五十亩山地之后", "00_独立篇/04_未交的答卷"])
    new = story_creator.resolve_episode_path(tmp_path, "五十亩山地之后")
    assert new == parent / "06_五十亩山地之后"
    assert not new.exists()  # read-only path resolution, no creation


def test_mysql_missing_authority_fails_closed(tmp_path, monkeypatch):
    _root(tmp_path)
    monkeypatch.setattr(story_creator.episode_state_persistence, "authority_mode", lambda: "mysql")
    def unavailable():
        raise ConnectionError("no authoritative episode IDs")
    monkeypatch.setattr(story_creator.episode_state_persistence, "list_episode_namespaces", unavailable)
    with pytest.raises(ConnectionError):
        story_creator.resolve_episode_path(tmp_path, "五十亩山地之后")


def test_existing_episode_is_stable_even_if_historical_05_exists(tmp_path, monkeypatch):
    parent = _root(tmp_path)
    existing = parent / "06_五十亩山地之后"
    existing.mkdir()
    monkeypatch.setattr(story_creator.episode_state_persistence, "authority_mode", lambda: "mysql")
    monkeypatch.setattr(story_creator.episode_state_persistence, "list_episode_namespaces",
                        lambda: ["00_独立篇/05_五十亩山地之后"])
    assert story_creator.resolve_episode_path(tmp_path, "五十亩山地之后") == existing


def test_json_mode_does_not_require_mysql(tmp_path, monkeypatch):
    parent = _root(tmp_path)
    monkeypatch.setattr(story_creator.episode_state_persistence, "authority_mode", lambda: "json")
    monkeypatch.setattr(story_creator.episode_state_persistence, "list_episode_namespaces",
                        lambda: (_ for _ in ()).throw(AssertionError("MySQL must not be read")))
    assert story_creator.resolve_episode_path(tmp_path, "另一部作品") == parent / "05_另一部作品"
