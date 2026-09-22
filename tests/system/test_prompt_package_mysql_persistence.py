from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import prompt_package_persistence as persistence  # noqa: E402


def test_json_mode_loads_legacy_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    rel = persistence.REL / "03.json"
    path = ep / rel
    path.parent.mkdir(parents=True)
    persistence.story_json.write_json(path, {"frame": "03", "package_sha256": "a" * 64})
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "json"})
    monkeypatch.setattr(persistence.runtime_workspace, "resolve_read_path", lambda _ep, _rel: path)
    assert persistence.load_latest(ep, 3)["frame"] == "03"


def test_mysql_mode_prefers_repository_without_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence.storage_config, "mysql_connection_kwargs", lambda *_a, **_k: {})
    monkeypatch.setattr(persistence.episode_identity, "storage_episode_id", lambda _ep: "EPU_test")

    import platform.repository.mysql.mysql_connection as mysql_connection
    import platform.repository.mysql.mysql_prompt_package_repository as prompt_repo

    class FakeConnection:
        def __init__(self, **_kwargs): pass
        def close(self): pass

    monkeypatch.setattr(mysql_connection, "MySqlConnection", FakeConnection)
    monkeypatch.setattr(
        prompt_repo.MySqlPromptPackageRepository,
        "get_latest",
        lambda self, episode_id, frame_no, package_type="IMAGE": {
            "payload": {"frame": "03", "package_sha256": "b" * 64}
        },
    )
    assert persistence.load_latest(ep, 3)["package_sha256"] == "b" * 64
