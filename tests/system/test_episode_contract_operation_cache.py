from __future__ import annotations

import contextvars
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_contract_persistence as contracts  # noqa: E402
import story_json  # noqa: E402


class FakeConnection:
    pass


class CountingRepository:
    def __init__(self, payload):
        self.payload = payload
        self.reads = 0

    def get_latest(self, _episode_id, _contract_type):
        self.reads += 1
        time.sleep(0.02)
        return {"payload": self.payload, "sha256": "not-used-for-inline-payload"}


def _prepare_mysql(monkeypatch, repo):
    monkeypatch.setattr(
        contracts.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        contracts.storage_config,
        "mysql_connection_kwargs",
        lambda _overrides=None: {"host": "db", "database": "storyos"},
    )
    monkeypatch.setattr(
        contracts.episode_identity, "storage_episode_id", lambda _ep: "EPU_TEST"
    )
    monkeypatch.setattr(contracts, "_repository", lambda: (FakeConnection(), repo))


def test_operation_cache_reads_mysql_once_and_returns_deep_copies(monkeypatch, tmp_path):
    repo = CountingRepository({"nested": {"value": 7}})
    _prepare_mysql(monkeypatch, repo)

    with contracts.operation_scope():
        first = contracts.load_latest(tmp_path, "WORLD_IDENTITY")
        first["nested"]["value"] = 99
        second = contracts.load_latest(tmp_path, "WORLD_IDENTITY")

    assert repo.reads == 1
    assert second == {"nested": {"value": 7}}


def test_explicit_invalidate_reloads_authoritative_mysql_value(monkeypatch, tmp_path):
    repo = CountingRepository({"revision": 1})
    _prepare_mysql(monkeypatch, repo)

    with contracts.operation_scope():
        assert contracts.load_latest(tmp_path, "WORLD_IDENTITY") == {"revision": 1}
        repo.payload = {"revision": 2}
        contracts.invalidate(tmp_path, "WORLD_IDENTITY")
        assert contracts.load_latest(tmp_path, "WORLD_IDENTITY") == {"revision": 2}

    assert repo.reads == 2


def test_parallel_first_reads_share_one_mysql_request(monkeypatch, tmp_path):
    repo = CountingRepository({"revision": 1})
    _prepare_mysql(monkeypatch, repo)

    with contracts.operation_scope():
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [
                pool.submit(
                    contextvars.copy_context().run,
                    contracts.load_latest,
                    tmp_path,
                    "WORLD_IDENTITY",
                )
                for _ in range(6)
            ]
            results = [future.result() for future in futures]

    assert results == [{"revision": 1}] * 6
    assert repo.reads == 1


def test_dual_file_fallback_is_not_cached(monkeypatch, tmp_path):
    path = tmp_path / "legacy.json"
    story_json.write_json(path, {"revision": 1})
    monkeypatch.setattr(
        contracts.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "dual"},
    )
    monkeypatch.setattr(
        contracts.storage_config,
        "mysql_connection_kwargs",
        lambda _overrides=None: {"host": "db", "database": "storyos"},
    )
    monkeypatch.setattr(
        contracts,
        "_repository",
        lambda: (_ for _ in ()).throw(ConnectionError("temporary outage")),
    )

    with contracts.operation_scope():
        assert contracts.load_latest(
            tmp_path, "WORLD_IDENTITY", legacy_path=path
        ) == {"revision": 1}
        story_json.write_json(path, {"revision": 2})
        assert contracts.load_latest(
            tmp_path, "WORLD_IDENTITY", legacy_path=path
        ) == {"revision": 2}
