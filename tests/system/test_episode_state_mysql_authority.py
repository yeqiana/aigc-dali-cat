from __future__ import annotations

from contextlib import nullcontext
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_state_persistence as persistence  # noqa: E402


class FakeConnection:
    def transaction(self):
        return nullcontext(self)

    def close(self):
        pass


class FakeEpisodes:
    def __init__(self, row=None):
        self.row = row
        self.saved = []
        self.dispositions = []

    def get_by_namespace(self, _namespace):
        return self.row

    def upsert(self, record):
        self.saved.append(dict(record))

    def update_disposition(self, episode_id, target, *, expected="ACTIVE"):
        self.dispositions.append((episode_id, target, expected))


class FakeStates:
    def __init__(self, state=None, history=None):
        self.state = state
        self.rows = list(history or [])
        self.initialized = []
        self.transitions = []

    def get(self, _episode_id):
        return self.state

    def history(self, _episode_id):
        return list(self.rows)

    def initialize(self, episode_id, current_state, history, *, source):
        self.initialized.append((episode_id, current_state, list(history), source))
        self.state = {
            "episode_id": episode_id,
            "current_state": current_state,
            "state_version": len(history),
            "source": source,
            "update_time": history[-1].get("at"),
        }
        self.rows = [
            {
                "from_state": history[index - 1]["state"] if index else None,
                "to_state": item["state"],
                "state_version": index + 1,
                "source": source,
                "reason": item.get("note") or "",
                "create_time": item.get("at"),
            }
            for index, item in enumerate(history)
        ]
        return self.state

    def transition(
        self,
        episode_id,
        *,
        expected_state,
        expected_version,
        target_state,
        source,
        reason,
        at,
    ):
        self.transitions.append(
            (episode_id, expected_state, expected_version, target_state, source, reason, at)
        )
        self.state = {
            "episode_id": episode_id,
            "current_state": target_state,
            "state_version": expected_version + 1,
            "source": source,
            "update_time": at,
        }
        return self.state


def _mysql_row():
    return {
        "episode_id": "EPU_mysql",
        "business_episode_id": "biz-01",
        "episode_namespace": "series/ep",
        "series_id": "series",
        "title": "MySQL Episode",
        "tool_version": "3",
        "disposition": "ACTIVE",
        "update_time": "2026-09-18T00:00:00+00:00",
    }


def _mysql_state():
    return {
        "episode_id": "EPU_mysql",
        "current_state": "STORYBOARD_LOCKED",
        "state_version": 2,
        "source": "runtime",
        "update_time": "2026-09-18T00:10:00+00:00",
    }


def _mysql_history():
    return [
        {
            "from_state": None,
            "to_state": "IDEA_LOCKED",
            "state_version": 1,
            "source": "init",
            "reason": "init",
            "create_time": "2026-09-18T00:00:00+00:00",
        },
        {
            "from_state": "IDEA_LOCKED",
            "to_state": "STORYBOARD_LOCKED",
            "state_version": 2,
            "source": "runtime",
            "reason": "story gate",
            "create_time": "2026-09-18T00:10:00+00:00",
        },
    ]


def _wire(monkeypatch, episodes, states):
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(persistence, "episode_namespace", lambda _ep: "series/ep")
    monkeypatch.setattr(
        persistence,
        "_repositories",
        lambda: (FakeConnection(), episodes, states),
    )


def test_mysql_authority_wins_over_stale_episode_state_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    stale = ep / persistence.REL
    stale.parent.mkdir(parents=True)
    stale.write_text(
        '{"current_state":"IDEA_LOCKED","episode_id":"stale"}',
        encoding="utf-8",
    )
    episodes = FakeEpisodes(_mysql_row())
    states = FakeStates(_mysql_state(), _mysql_history())
    _wire(monkeypatch, episodes, states)

    data = persistence.load(ep)

    assert data["current_state"] == "STORYBOARD_LOCKED"
    assert data["episode_id"] == "biz-01"
    assert data["storage_episode_id"] == "EPU_mysql"
    assert data["history"][-1]["mode"] == "advance"


def test_mysql_failure_does_not_fall_back_to_episode_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    stale = ep / persistence.REL
    stale.parent.mkdir(parents=True)
    stale.write_text('{"current_state":"IDEA_LOCKED"}', encoding="utf-8")
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence,
        "_repositories",
        lambda: (_ for _ in ()).throw(RuntimeError("mysql unavailable")),
    )

    with pytest.raises(RuntimeError, match="mysql unavailable"):
        persistence.load(ep)


def test_mysql_save_initial_does_not_materialize_compatibility_json(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    episodes = FakeEpisodes(None)
    states = FakeStates(None, [])
    _wire(monkeypatch, episodes, states)
    data = {
        "schema_version": 1,
        "tool_version": "3",
        "episode_id": "biz-01",
        "series": "series",
        "title": "MySQL Episode",
        "current_state": "IDEA_LOCKED",
        "disposition": "ACTIVE",
        "updated_at": "2026-09-18T00:00:00+00:00",
        "history": [
            {
                "state": "IDEA_LOCKED",
                "at": "2026-09-18T00:00:00+00:00",
                "note": "init",
            }
        ],
    }

    persistence.save_initial(ep, data)

    assert not (ep / persistence.REL).exists()
    assert episodes.saved
    assert states.initialized
    assert states.initialized[0][1] == "IDEA_LOCKED"


def test_materialize_export_uses_mysql_authority_without_restoring_legacy(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    episodes = FakeEpisodes(_mysql_row())
    states = FakeStates(_mysql_state(), _mysql_history())
    _wire(monkeypatch, episodes, states)
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(persistence.runtime_workspace, "runtime_root", lambda: runtime)

    exported = persistence.materialize_export(ep)

    assert exported is not None and exported.is_file()
    assert exported.name == "episode-state.json"
    assert not (ep / persistence.REL).exists()
    assert persistence.load(ep)["current_state"] == "STORYBOARD_LOCKED"


def test_mysql_transition_updates_typed_state_without_writing_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    episodes = FakeEpisodes(_mysql_row())
    states = FakeStates(_mysql_state(), _mysql_history())
    _wire(monkeypatch, episodes, states)
    data = persistence.load(ep)

    updated = persistence.transition(
        ep,
        data,
        "VISUAL_CALIBRATED",
        transition_mode="advance",
        source="test",
        reason="visual gate",
        at="2026-09-18T00:20:00+00:00",
    )

    assert updated["current_state"] == "VISUAL_CALIBRATED"
    assert states.transitions[-1][1:4] == (
        "STORYBOARD_LOCKED",
        2,
        "VISUAL_CALIBRATED",
    )
    assert not (ep / persistence.REL).exists()
