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

    def unique_owner_by_namespace(self, namespace):
        rows = [row for row in self.rows if row["episode_namespace"] == namespace]
        if len(rows) > 1:
            raise RuntimeError("EPISODE_NAMESPACE_AMBIGUOUS_AUTHORITY")
        return rows[0] if rows else None

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
    fake_authority.rows.append({
        "episode_namespace": "00_独立篇/06_继续中的作品",
        "business_episode_id": "00-06",
        "episode_id": "EPU_EXISTING_ORIGINAL_CLAIM",
        "title": "继续中的作品",
    })
    observed = {}
    def resume(root, title, visual_profile=None, **kwargs):
        observed.update(kwargs)
        return kwargs["_episode_override"]
    from pytest import MonkeyPatch
    # fake_authority already installs the creator stub; wrap to inspect UID.
    with MonkeyPatch.context() as patch:
        patch.setattr(story_creator, "_create_episode_impl", resume)
        found = story_creator.create_episode(tmp_path, "继续中的作品")
    assert found == ep
    assert observed["_reserved_storage_id"] == "EPU_EXISTING_ORIGINAL_CLAIM"
    assert fake_authority.claims == []


def test_existing_partial_dir_without_mysql_owner_fails_closed(tmp_path, fake_authority):
    path = tmp_path / "episodes" / "00_独立篇" / "06_孤立目录"
    path.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="AUTHORITY_MISSING"):
        story_creator.create_episode(tmp_path, "孤立目录")
    assert fake_authority.claims == []


def test_existing_namespace_different_business_owner_fails_closed(tmp_path, fake_authority):
    path = tmp_path / "episodes" / "00_独立篇" / "06_冲突作品"
    path.mkdir(parents=True)
    fake_authority.rows.append({
        "episode_namespace": "00_独立篇/06_冲突作品",
        "business_episode_id": "00-09",
        "episode_id": "EPU_WRONG",
        "title": "冲突作品",
    })
    with pytest.raises(RuntimeError, match="IDENTITY_CONFLICT"):
        story_creator.create_episode(tmp_path, "冲突作品")
