from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_discovery  # noqa: E402


def _configure(monkeypatch, tmp_path, mode: str, namespaces: list[str]):
    episodes = tmp_path / "episodes"
    episodes.mkdir()
    monkeypatch.setattr(episode_discovery, "EPISODES", episodes)
    monkeypatch.setattr(
        episode_discovery.episode_state_persistence,
        "authority_mode",
        lambda: mode,
    )
    monkeypatch.setattr(
        episode_discovery.episode_state_persistence,
        "list_episode_namespaces",
        lambda: list(namespaces),
    )
    return episodes


def test_mysql_discovers_episode_from_namespace_without_state_file(monkeypatch, tmp_path):
    episodes = _configure(monkeypatch, tmp_path, "mysql", ["series/ep01"])
    ep = episodes / "series" / "ep01"
    ep.mkdir(parents=True)

    roots = episode_discovery.iter_episode_roots()

    assert roots == [ep.resolve()]
    assert not (ep / episode_discovery.STATE_REL).exists()


def test_mysql_ignores_stale_state_file_not_registered_in_database(monkeypatch, tmp_path):
    episodes = _configure(monkeypatch, tmp_path, "mysql", [])
    stale = episodes / "series" / "stale"
    (stale / "meta").mkdir(parents=True)
    (stale / episode_discovery.STATE_REL).write_text("{}", encoding="utf-8")

    assert episode_discovery.iter_episode_roots() == []


def test_dual_unions_legacy_file_and_mysql_namespace(monkeypatch, tmp_path):
    episodes = _configure(monkeypatch, tmp_path, "dual", ["series/mysql"])
    legacy = episodes / "series" / "legacy"
    mysql = episodes / "series" / "mysql"
    (legacy / "meta").mkdir(parents=True)
    mysql.mkdir(parents=True)
    (legacy / episode_discovery.STATE_REL).write_text("{}", encoding="utf-8")

    assert episode_discovery.iter_episode_roots() == [
        legacy.resolve(),
        mysql.resolve(),
    ]


def test_json_mode_preserves_file_discovery(monkeypatch, tmp_path):
    episodes = _configure(monkeypatch, tmp_path, "json", ["series/ignored"])
    ep = episodes / "series" / "json"
    (ep / "meta").mkdir(parents=True)
    (ep / episode_discovery.STATE_REL).write_text("{}", encoding="utf-8")

    assert episode_discovery.iter_episode_roots() == [ep.resolve()]
