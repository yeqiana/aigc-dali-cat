from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_checkpoint  # noqa: E402
import workflow_observability  # noqa: E402


def test_checkpoint_authority_sha_is_canonical():
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}
    assert runtime_checkpoint.authority_sha256(a) == runtime_checkpoint.authority_sha256(b)


def test_materialize_export_uses_authority_when_compat_file_absent(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    data = runtime_checkpoint.ensure_shape({"last_completed": "MYSQL"})
    monkeypatch.setattr(runtime_checkpoint, "load", lambda _ep, _default=None: data)

    path = runtime_checkpoint.materialize_export(ep)

    assert path is not None
    assert path.is_file()
    assert "MYSQL" in path.read_text(encoding="utf-8")


def test_observability_snapshot_hashes_checkpoint_authority(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        workflow_observability.runtime_checkpoint,
        "load",
        lambda _ep, _default=None: {"last_completed": "MYSQL"},
    )
    monkeypatch.setattr(
        workflow_observability.episode_state_persistence,
        "load",
        lambda _ep: {"current_state": "IDEA_LOCKED"},
    )

    rows, _fingerprint = workflow_observability.source_snapshot(ep)

    mapped = {row["path"]: row["sha256"] for row in rows}
    assert mapped[runtime_checkpoint.REL.as_posix()] == runtime_checkpoint.authority_sha256(
        {"last_completed": "MYSQL"}
    )
    assert mapped["meta/episode-state.json"] is not None
