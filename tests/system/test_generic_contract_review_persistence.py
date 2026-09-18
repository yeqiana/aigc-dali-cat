from __future__ import annotations

from contextlib import nullcontext
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_contract_persistence as contracts  # noqa: E402
import review_record_persistence as reviews  # noqa: E402


class FakeConnection:
    def close(self):
        pass


class FakeContractRepo:
    def __init__(self, row=None):
        self.row = row
        self.saved = []

    def save_version(self, record):
        self.saved.append(dict(record))
        return {
            "contract_id": "EC_1",
            "episode_id": record["episode_id"],
            "contract_type": record["contract_type"],
            "version_no": 1,
            "sha256": record["sha256"],
        }

    def get_latest(self, _episode_id, _contract_type):
        return self.row


class FakeReviewRepo:
    def __init__(self, row=None):
        self.row = row
        self.saved = []

    def get_latest(self, _episode_id, _review_type):
        return self.row

    def upsert(self, record):
        self.saved.append(dict(record))
        return {
            "review_id": "RV_1",
            "episode_id": record["episode_id"],
            "review_type": record["review_type"],
            "attempt_no": record["attempt_no"],
        }


def test_mysql_contract_missing_ignores_stale_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    stale = ep / "meta/world-identity.json"
    stale.parent.mkdir(parents=True)
    stale.write_text('{"stale":true}', encoding="utf-8")
    monkeypatch.setattr(
        contracts.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        contracts.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        contracts,
        "_repository",
        lambda: (FakeConnection(), FakeContractRepo(None)),
    )

    assert contracts.load_latest(
        ep, "WORLD_IDENTITY", legacy_path=stale
    ) is None


def test_mysql_contract_failure_propagates(monkeypatch, tmp_path):
    monkeypatch.setattr(
        contracts.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        contracts,
        "_repository",
        lambda: (_ for _ in ()).throw(RuntimeError("mysql down")),
    )
    with pytest.raises(RuntimeError, match="mysql down"):
        contracts.load_latest(tmp_path, "WORLD_IDENTITY")


def test_review_attempt_increments_only_when_content_changes(monkeypatch, tmp_path):
    repo = FakeReviewRepo(None)
    monkeypatch.setattr(
        reviews.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "dual"},
    )
    monkeypatch.setattr(
        reviews.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(reviews, "_repository", lambda: (FakeConnection(), repo))

    first = reviews.persist(
        tmp_path, "STORY_SEMANTIC", {"decision": "PASS"},
        decision="PASS",
    )
    assert first["attempt_no"] == 1

    repo.row = {
        "attempt_no": 1,
        "payload": {"decision": "PASS"},
    }
    same = reviews.persist(
        tmp_path, "STORY_SEMANTIC", {"decision": "PASS"},
        decision="PASS",
    )
    assert same["attempt_no"] == 1

    changed = reviews.persist(
        tmp_path, "STORY_SEMANTIC", {"decision": "WARNING"},
        decision="WARNING",
    )
    assert changed["attempt_no"] == 2


def test_mysql_review_missing_ignores_stale_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    stale = ep / "meta/story-semantic-review.json"
    stale.parent.mkdir(parents=True)
    stale.write_text('{"decision":"STALE"}', encoding="utf-8")
    monkeypatch.setattr(
        reviews.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        reviews.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        reviews,
        "_repository",
        lambda: (FakeConnection(), FakeReviewRepo(None)),
    )

    assert reviews.load_latest(
        ep, "STORY_SEMANTIC", legacy_path=stale
    ) is None
