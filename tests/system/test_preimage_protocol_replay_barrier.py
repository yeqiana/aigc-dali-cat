from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import preimage_protocol  # noqa: E402


def test_replayed_authority_commit_rebuilds_preimage_barrier(monkeypatch, tmp_path):
    ep = tmp_path
    (ep / "meta/runtime").mkdir(parents=True)
    task = {
        "task_id": "task-1",
        "node_id": "character_finalize",
        "candidate_output": "meta/runtime/preimage-candidates/character.json",
        "authority_scope": ["character.finalize"],
    }
    candidate = {
        "payload": {"character.finalize": {"identity": "locked"}},
        "authority_scope": ["character.finalize"],
    }
    monkeypatch.setattr(preimage_protocol.tasks, "validate_patch_scopes", lambda _rows: None)
    monkeypatch.setattr(preimage_protocol.tasks, "read_candidate", lambda _ep, _task: candidate)
    monkeypatch.setattr(preimage_protocol.tasks, "verify_candidate", lambda _candidate, _task: [])
    monkeypatch.setattr(preimage_protocol.preimage_authority_snapshot, "stale_owned", lambda _ep, _snapshot: False)
    monkeypatch.setattr(preimage_protocol.preimage_authority_snapshot, "sha", lambda _path: "a" * 64)
    monkeypatch.setattr(
        preimage_protocol.authority_commit,
        "commit_transaction",
        lambda *args, **kwargs: {"status": "REPLAYED", "replayed": True, "output_sha": "b" * 64},
    )
    monkeypatch.setattr(
        preimage_protocol.preimage_authority_snapshot,
        "build",
        lambda _ep, write, kind: {"snapshot_id": "committed-snapshot"},
    )

    result = preimage_protocol.commit_candidates(ep, {"snapshot_id": "input-snapshot"}, [task])

    assert result["status"] == "PASS"
    assert result["replayed"] is True
    assert result["barrier"]["status"] == "READY"
    assert preimage_protocol.barrier_ready(ep) is True
