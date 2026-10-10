"""Isolated, zero-SQL Episode business-number allocation concurrency tests."""
from __future__ import annotations

import concurrent.futures
import sys
import threading
from contextlib import contextmanager, nullcontext
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_creator
import episode_state_persistence


class FakeMySql:
    """One shared fake MySQL lock and durable row store (never the production DB)."""

    def __init__(self, old="00_独立篇/05_五十亩山地之后"):
        self.rows = [{"episode_namespace": old, "business_episode_id": "00-05"}]
        self.mutex = threading.Lock()
        self.claims = []
        self.transaction_count = 0
        self.fail_lock = False

    @contextmanager
    def advisory_lock(self, name, *, timeout_seconds):
        if self.fail_lock:
            raise RuntimeError("EPISODE_ID_ALLOCATION_LOCK_UNAVAILABLE")
        assert name.startswith("storyos:epnum:")
        assert timeout_seconds == 15
        with self.mutex:
            yield

    @contextmanager
    def transaction(self):
        self.transaction_count += 1
        yield

    def list_namespaces(self):
        return [r["episode_namespace"] for r in self.rows]

    def reserve_standalone_number(self, record):
        assert record["business_episode_id"] not in {
            r["business_episode_id"] for r in self.rows
        }, "duplicate business number"
        self.rows.append(dict(record))
        self.claims.append(dict(record))


@pytest.fixture
def fake_authority(monkeypatch):
    db = FakeMySql()
    monkeypatch.setattr(episode_state_persistence, "_mode", lambda: "mysql")
    monkeypatch.setattr(episode_state_persistence, "episode_namespace",
                        lambda ep: "00_独立篇/" + Path(ep).name)
    monkeypatch.setattr(episode_state_persistence, "_repositories",
                        lambda: (db, db, None))
    monkeypatch.setattr(
        story_creator,
        "_create_episode_impl",
        lambda root, title, visual_profile=None, **kwargs:
            kwargs["_episode_override"],
    )
    return db


def test_two_concurrent_creators_reserve_distinct_numbers(tmp_path, fake_authority):
    barrier = threading.Barrier(2)

    def create(title):
        barrier.wait(timeout=4)
        return story_creator.create_episode(tmp_path, title)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as workers:
        paths = list(workers.map(create, ["第一部", "第二部"]))
    numbers = {story_creator._canonical_identity_for_path(tmp_path, ep, ep.name)[0]
               for ep in paths}
    assert numbers == {"00-06", "00-07"}
    assert len(fake_authority.claims) == 2
    assert fake_authority.transaction_count == 2
    assert {r["episode_namespace"] for r in fake_authority.claims} == {
        "00_独立篇/06_第一部", "00_独立篇/07_第二部",
    } or {r["episode_namespace"] for r in fake_authority.claims} == {
        "00_独立篇/06_第二部", "00_独立篇/07_第一部",
    }
    assert not any(p.exists() for p in paths)


def test_failed_bootstrap_does_not_recycle_claim(tmp_path, fake_authority, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("simulated process crash after claim")
    monkeypatch.setattr(story_creator, "_create_episode_impl", broken)
    with pytest.raises(RuntimeError, match="simulated"):
        story_creator.create_episode(tmp_path, "首部")
    assert fake_authority.claims[0]["business_episode_id"] == "00-06"
    monkeypatch.setattr(story_creator, "_create_episode_impl",
                        lambda root, title, visual_profile=None, **kwargs:
                            kwargs["_episode_override"])
    next_path = story_creator.create_episode(tmp_path, "另一部")
    assert next_path.name.startswith("07_")
    assert fake_authority.claims[1]["business_episode_id"] == "00-07"


def test_mysql_lock_unavailable_fails_before_files(tmp_path, fake_authority):
    fake_authority.fail_lock = True
    with pytest.raises(RuntimeError, match="LOCK_UNAVAILABLE"):
        story_creator.create_episode(tmp_path, "停止创建")
    assert fake_authority.claims == []


def test_mysql_failure_fails_closed_in_dual_mode(tmp_path, fake_authority, monkeypatch):
    monkeypatch.setattr(episode_state_persistence, "_mode", lambda: "dual")
    fake_authority.fail_lock = True
    with pytest.raises(RuntimeError, match="LOCK_UNAVAILABLE"):
        story_creator.create_episode(tmp_path, "双写必须拒绝回退")


def test_json_mode_never_claims_mysql(tmp_path, fake_authority, monkeypatch):
    monkeypatch.setattr(episode_state_persistence, "_mode", lambda: "json")
    monkeypatch.setattr(
        story_creator, "_create_episode_impl",
        lambda root, title, visual_profile=None, **kwargs:
            story_creator.resolve_episode_path(root, title),
    )
    path = story_creator.create_episode(tmp_path, "纯JSON兼容")
    assert path.name == "01_纯JSON兼容"
    assert fake_authority.claims == []


def test_existing_episode_does_not_reserve_another_number(tmp_path, fake_authority):
    ep = tmp_path / "episodes" / "00_独立篇" / "06_继续中的作品"
    ep.mkdir(parents=True)
    found = story_creator.create_episode(tmp_path, "继续中的作品")
    assert found == ep
    assert fake_authority.claims == []
