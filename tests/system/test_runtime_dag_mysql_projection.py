from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import workflow_step_protocol as proto  # noqa: E402


def _checkpoint():
    return {
        "updated_at": "2026-09-18T00:10:00+00:00",
        "step_runs": [{
            "step": "CREATIVE_STORY",
            "status": "PASS",
            "attempt": 2,
            "started_at": "2026-09-18T00:00:00+00:00",
            "finished_at": "2026-09-18T00:10:00+00:00",
            "elapsed_seconds": 600.0,
            "input_hash": "in",
            "output_hash": "out",
            "note": "ok",
            "returncode": 0,
        }],
    }


def test_mysql_dag_state_is_derived_from_checkpoint_not_stale_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    stale = ep / proto.DAG_REL
    stale.parent.mkdir(parents=True)
    stale.write_text('{"steps":{"STALE":{"attempt":99}},"history":[]}', encoding="utf-8")
    monkeypatch.setattr(
        proto.runtime_checkpoint_persistence, "mode", lambda: "mysql"
    )
    monkeypatch.setattr(proto.runtime_checkpoint, "load", lambda _ep, _default: _checkpoint())

    state = proto.load_state(ep)

    assert "STALE" not in state["steps"]
    assert state["steps"]["CREATIVE_STORY"]["attempt"] == 2
    assert state["steps"]["CREATIVE_STORY"]["input_hash"] == "in"
    assert state["steps"]["CREATIVE_STORY"]["returncode"] == 0


def test_mysql_save_result_does_not_write_dag_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(
        proto.runtime_checkpoint_persistence, "mode", lambda: "mysql"
    )
    result = proto.StepResult(
        "CREATIVE_STORY", "PASS", 1, "a", "b", 0.1, "in", "out", "ok", 0
    )

    proto.save_result(ep, result)

    assert not proto.runtime_workspace.workspace_path(ep, proto.DAG_REL).exists()
