from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_scout_persistence as persistence


def test_json_mode_loads_legacy(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    path = ep / persistence.REL / "03.json"
    path.parent.mkdir(parents=True)
    persistence.story_json.write_json(path, {"frame": "03", "decision": "DEFER_TO_FINAL"})
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "json"})
    assert persistence.load(ep, 3)["decision"] == "DEFER_TO_FINAL"


def test_mysql_mode_loads_without_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence.storage_config, "mysql_connection_kwargs", lambda *_a, **_k: {})
    monkeypatch.setattr(persistence.episode_identity, "storage_episode_id", lambda _ep: "EPU_test")
    import platform.repository.mysql.mysql_connection as mc
    import platform.repository.mysql.mysql_frame_review_repository as fr

    class C:
        def __init__(self, **_k): pass
        def close(self): pass

    monkeypatch.setattr(mc, "MySqlConnection", C)
    monkeypatch.setattr(
        fr.MySqlFrameReviewRepository,
        "get_current",
        lambda self, *_a, **_k: {"payload": {"frame": "03", "decision": "DEFER_TO_FINAL"}},
    )
    assert persistence.load(ep, 3)["frame"] == "03"


def test_mysql_mode_save_does_not_materialize_json(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence, "persist", lambda _ep, _payload: {"mode": "mysql", "mysql_written": True})
    result = persistence.save(ep, {"frame": "03", "decision": "DEFER_TO_FINAL"})
    assert result["mysql_written"] is True
    assert not (ep / persistence.REL / "03.json").exists()
