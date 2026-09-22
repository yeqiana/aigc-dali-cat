from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_checkpoint  # noqa: E402


def test_mysql_load_ignores_stale_workspace_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    stale = runtime_checkpoint.write_path(ep)
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text('{"last_completed":"STALE","step_runs":[]}', encoding="utf-8")
    authoritative = runtime_checkpoint.ensure_shape({
        "last_completed": "MYSQL",
        "step_runs": [],
    })
    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "mode",
        lambda: "mysql",
    )
    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "load",
        lambda _ep: authoritative,
    )

    assert runtime_checkpoint.load(ep)["last_completed"] == "MYSQL"


def test_mysql_save_does_not_materialize_checkpoint_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    saved = []
    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "mode",
        lambda: "mysql",
    )
    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "persist",
        lambda _ep, data: saved.append(dict(data)) or {"mysql_written": True},
    )

    runtime_checkpoint.save(
        ep, runtime_checkpoint.ensure_shape({"last_completed": "MYSQL"})
    )

    assert saved[-1]["last_completed"] == "MYSQL"
    assert not runtime_checkpoint.write_path(ep).exists()


def test_mysql_record_step_updates_authority_without_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    state = runtime_checkpoint.ensure_shape({"last_completed": "INIT"})
    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "mode",
        lambda: "mysql",
    )
    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "load",
        lambda _ep: dict(state),
    )

    def persist(_ep, data):
        state.clear()
        state.update(data)
        return {"mysql_written": True}

    monkeypatch.setattr(
        runtime_checkpoint.runtime_checkpoint_persistence,
        "persist",
        persist,
    )

    runtime_checkpoint.record_step(ep, step="UNIT", status="PASS")

    assert state["step_runs"][-1]["step"] == "UNIT"
    assert not runtime_checkpoint.write_path(ep).exists()
