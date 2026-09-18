from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_identity  # noqa: E402
import story_json  # noqa: E402


def _episode(root: Path, series: str, leaf: str, episode_id: str) -> Path:
    ep = root / series / leaf
    (ep / "meta").mkdir(parents=True)
    story_json.write_json(
        ep / "meta/episode-state.json",
        {"episode_id": episode_id, "series": series, "title": leaf},
    )
    return ep


def test_same_business_id_in_different_namespaces_does_not_collide(monkeypatch, tmp_path):
    episodes_root = tmp_path / "episodes"
    monkeypatch.setattr(episode_identity.runtime_workspace, "EPISODES_ROOT", episodes_root)
    a = _episode(episodes_root, "series-a", "01-a", "10-01")
    b = _episode(episodes_root, "series-b", "01-b", "10-01")
    assert episode_identity.business_episode_id(a) == episode_identity.business_episode_id(b)
    assert episode_identity.storage_episode_id(a) != episode_identity.storage_episode_id(b)
    assert episode_identity.storage_episode_id(a).startswith("EPU_")


def test_explicit_storage_episode_id_is_stable_override(tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    story_json.write_json(
        ep / "meta/episode-state.json",
        {"episode_id": "legacy-01", "storage_episode_id": "EPU_EXPLICIT"},
    )
    assert episode_identity.storage_episode_id(ep) == "EPU_EXPLICIT"


def test_identity_record_keeps_business_metadata(tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    story_json.write_json(
        ep / "meta/episode-state.json",
        {"episode_id": "11-01", "series": "series-x", "title": "Title X"},
    )
    row = episode_identity.identity_record(ep)
    assert row["business_episode_id"] == "11-01"
    assert row["series"] == "series-x"
    assert row["title"] == "Title X"
