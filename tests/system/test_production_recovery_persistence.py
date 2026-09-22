from __future__ import annotations

from contextlib import nullcontext
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_recovery_persistence as persistence  # noqa: E402


class FakeConnection:
    def transaction(self):
        return nullcontext(self)

    def close(self):
        pass


class FakeRepository:
    def __init__(self):
        self.rows = {}

    def get(self, transaction_id):
        document = self.rows.get(str(transaction_id))
        return None if document is None else {"document": dict(document)}

    def upsert(self, episode_id, transaction_id, document):
        self.rows[str(transaction_id)] = dict(document)
        return {
            "episode_id": str(episode_id),
            "transaction_id": str(transaction_id),
            "sha256": "a" * 64,
            "byte_size": 1,
        }


def test_mysql_update_merges_transaction_without_resetting_created_at(monkeypatch, tmp_path):
    repo = FakeRepository()
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        persistence,
        "_repository",
        lambda: (FakeConnection(), repo),
    )

    first = persistence.update_transaction(
        tmp_path,
        "tx-1",
        "BEGIN_PREPARED",
        details={"item_id": "item-1", "frame": 2},
    )
    created_at = repo.rows["tx-1"]["created_at"]
    second = persistence.update_transaction(
        tmp_path,
        "tx-1",
        "COMMITTED",
        details={"recovery": "ledger_ready_replayed"},
    )

    assert first["mysql_written"] is True
    assert second["mysql_written"] is True
    assert repo.rows["tx-1"]["created_at"] == created_at
    assert repo.rows["tx-1"]["phase"] == "COMMITTED"
    assert repo.rows["tx-1"]["item_id"] == "item-1"
    assert repo.rows["tx-1"]["recovery"] == "ledger_ready_replayed"


def test_json_mode_is_mysql_noop(monkeypatch, tmp_path):
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "json"},
    )
    result = persistence.update_transaction(tmp_path, "tx-1", "BEGIN_PREPARED")
    assert result == {"mode": "json", "mysql_written": False}


def test_mysql_update_rejects_transaction_owned_by_another_episode(
    monkeypatch, tmp_path
):
    class ForeignRepository(FakeRepository):
        def get(self, transaction_id):
            return {
                "episode_id": "EPU_OTHER",
                "document": {"transaction_id": str(transaction_id), "phase": "PENDING"},
            }

    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        persistence,
        "_repository",
        lambda: (FakeConnection(), ForeignRepository()),
    )

    import pytest

    with pytest.raises(ValueError, match="another episode"):
        persistence.update_transaction(tmp_path, "tx-shared", "COMMITTED")
