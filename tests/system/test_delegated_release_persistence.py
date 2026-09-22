import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import delegated_release_persistence


def test_record_maps_ready_package(tmp_path, monkeypatch):
    monkeypatch.setattr(delegated_release_persistence.episode_identity, "storage_episode_id", lambda _ep: "EPU_X")
    payload = {"package": {"path": "x.zip", "sha256": "a" * 64}}
    row = delegated_release_persistence._record(tmp_path, payload, delegated_release_persistence.RELEASE_TYPE)
    assert row["episode_id"] == "EPU_X"
    assert row["status"] == "READY"
    assert row["snapshot_sha256"] == "a" * 64
