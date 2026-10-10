"""Isolated SQL/physical-session contracts for durable Episode number claims."""
from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform.repository.mysql.mysql_episode_repository import MySqlEpisodeRepository
from platform.repository.mysql.mysql_connection import MySqlConnection


class FakeDb:
    def __init__(self):
        self.rows = []
        self.statements = []

    def query_all(self, sql, params):
        self.statements.append(("query", sql, params))
        assert "FOR UPDATE" in sql
        return list(self.rows)

    def execute(self, sql, params):
        self.statements.append(("execute", sql, params))
        assert "INSERT INTO TB_EPISODE" in sql
        assert "'ABANDONED'" in sql
        assert "ON DUPLICATE KEY" not in sql
        return 1


def record():
    return dict(
        episode_id="EPU_test_01", business_episode_id="00-07",
        episode_namespace="00_独立篇/07_新剧", series_id="00_独立篇",
        title="新剧"
    )


def test_claim_is_insert_not_upsert_and_row_is_abandoned():
    db = FakeDb()
    MySqlEpisodeRepository(db).reserve_standalone_number(record())
    assert [kind for kind, *_ in db.statements] == ["query", "execute"]
    assert db.statements[1][2][1] == "00-07"


def test_business_collision_fails_before_insert():
    db = FakeDb()
    db.rows.append({"EPISODE_ID": "another owner"})
    with pytest.raises(RuntimeError, match="ALREADY_CLAIMED"):
        MySqlEpisodeRepository(db).reserve_standalone_number(record())
    assert [kind for kind, *_ in db.statements] == ["query"]


class FakeCursor:
    def __init__(self, physical):
        self.physical = physical

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params):
        self.physical.sql.append(sql)

    def fetchone(self):
        return (self.physical.results.pop(0),)


class FakePhysical:
    def __init__(self, results=(1, 1)):
        self.results = list(results)
        self.sql = []
        self.ping_reconnect = None

    def ping(self, reconnect):
        self.ping_reconnect = reconnect

    def cursor(self):
        return FakeCursor(self)


def session(physical):
    db = MySqlConnection.__new__(MySqlConnection)
    db._local = threading.local()

    @contextmanager
    def borrowed():
        yield physical

    db._borrow = borrowed
    return db


def test_advisory_lock_keeps_one_session_until_release():
    physical = FakePhysical()
    db = session(physical)
    with db.advisory_lock("storyos:epnum:abc", timeout_seconds=15):
        assert physical.sql == ["SELECT GET_LOCK(%s, %s) AS ACQUIRED"]
    assert physical.sql == [
        "SELECT GET_LOCK(%s, %s) AS ACQUIRED", "SELECT RELEASE_LOCK(%s) AS RELEASED"
    ]
    assert physical.ping_reconnect is True


def test_lock_failure_fails_closed_without_release():
    physical = FakePhysical((0,))
    with pytest.raises(RuntimeError, match="LOCK_UNAVAILABLE"):
        with session(physical).advisory_lock("storyos:epnum:abc"):
            pytest.fail("must not enter")
    assert physical.sql == ["SELECT GET_LOCK(%s, %s) AS ACQUIRED"]


def test_exception_still_releases_lock():
    physical = FakePhysical()
    with pytest.raises(ValueError, match="bootstrap"):
        with session(physical).advisory_lock("storyos:epnum:abc"):
            raise ValueError("bootstrap")
    assert physical.sql[-1] == "SELECT RELEASE_LOCK(%s) AS RELEASED"


def test_lost_mysql_session_fails_closed_on_release():
    physical = FakePhysical((1, 0))
    with pytest.raises(RuntimeError, match="LOCK_LOST"):
        with session(physical).advisory_lock("storyos:epnum:abc"):
            pass


def test_storage_claim_pk_same_across_different_episode_paths():
    import episode_state_persistence as persistence
    first = persistence.standalone_claim_storage_id("00_独立篇", "00-08")
    second = persistence.standalone_claim_storage_id("00_独立篇", "00-08")
    assert first == second
    assert first.startswith("EPU_") and len(first) == 44
    assert first != persistence.standalone_claim_storage_id("00_独立篇", "00-09")


def test_initial_mysql_state_reuses_claim_pk(tmp_path, monkeypatch):
    import story_creator
    import episode_state_persistence as persistence
    episode = tmp_path / "episodes" / "00_独立篇" / "09_新剧"
    claim_id = persistence.standalone_claim_storage_id("00_独立篇", "00-09")
    seen = {}
    monkeypatch.setattr(story_creator.episode_state, "initial_documents",
                        lambda **kwargs: ({"episode_id": kwargs["episode_id"]},
                                          {"artifacts": {}}, {}))
    monkeypatch.setattr(persistence, "load_with_source", lambda ep: (None, "missing"))
    monkeypatch.setattr(persistence, "save_initial",
                        lambda ep, data, **kwargs: seen.update(data))
    monkeypatch.setattr(story_creator.world_identity_contract,
                        "ensure_visual_profile_override", lambda *a, **k: False)
    story_creator.ensure_episode_core_documents(
        tmp_path, episode, "新剧", reserved_storage_id=claim_id
    )
    assert seen["episode_id"] == "00-09"
    assert seen["storage_episode_id"] == claim_id


def test_duplicate_business_id_is_rejected_by_storage_primary_key_even_without_lock():
    """Mimic simultaneous lost sessions: both SELECTs saw no rows, INSERT PK decides."""
    import episode_state_persistence as persistence
    db = FakeDb()
    seen_primary_keys = set()
    def insert(sql, params):
        pk = params[0]
        if pk in seen_primary_keys:
            raise RuntimeError("MySQL duplicate primary key")
        seen_primary_keys.add(pk)
        return 1
    db.execute = insert
    first = record()
    first["episode_id"] = persistence.standalone_claim_storage_id("00_独立篇", "00-07")
    second = dict(first, episode_namespace="00_独立篇/07_另一个作品")
    MySqlEpisodeRepository(db).reserve_standalone_number(first)
    with pytest.raises(RuntimeError, match="duplicate primary key"):
        MySqlEpisodeRepository(db).reserve_standalone_number(second)
    assert len(seen_primary_keys) == 1
