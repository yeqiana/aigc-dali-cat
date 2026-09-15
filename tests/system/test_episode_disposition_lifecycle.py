from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import episode_lifecycle
import episode_state
import next_action
import raw_candidate_budget
import scheduler_core


def _episode(td: str) -> Path:
    ep = Path(td)
    (ep / "meta").mkdir(parents=True, exist_ok=True)
    state, manifest, gates = episode_state.initial_documents(
        episode_id="T", series="S", title="T", frame_count=1)
    for rel, data in (("episode-state.json", state), ("release-manifest.json", manifest), ("story-gates.json", gates)):
        (ep / "meta" / rel).write_text(json.dumps(data), encoding="utf-8")
    return ep


def test_terminate_preserves_stage_and_is_irreversible():
    with tempfile.TemporaryDirectory() as td:
        ep = _episode(td)
        data = episode_lifecycle.terminate(ep, target="ABANDONED", source="direct_user:test", reason="stop episode")
        assert data["current_state"] == "IDEA_LOCKED"
        assert data["disposition"] == "ABANDONED"
        assert data["disposition_history"][-1]["stage_at_termination"] == "IDEA_LOCKED"
        with pytest.raises(ValueError, match="already terminated"):
            episode_lifecycle.terminate(ep, target="VOIDED", source="direct_user:test", reason="change mind")


def test_terminal_episode_has_no_next_work_and_cannot_transition():
    test_root = ROOT / "episodes/_tests"
    test_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=test_root) as td:
        ep = _episode(td)
        episode_lifecycle.terminate(ep, target="VOIDED", source="direct_user:test", reason="invalid episode")
        action = next_action.derive(ep)
        assert action["action"] == "EPISODE_TERMINATED"
        assert action["work_pending"] is False
        assert action["hard_stop"] is True
        with pytest.raises(RuntimeError, match="EPISODE_TERMINATED"):
            episode_state.transition_cmd(argparse.Namespace(
                episode_dir=str(ep), target="STORYBOARD_LOCKED", note="must not advance", rewind=False))


def test_terminal_episode_blocks_queue_budget_and_ledger_writes():
    with tempfile.TemporaryDirectory() as td:
        ep = _episode(td)
        # Initialize before termination so the test proves late writes are blocked.
        from production_ledger_core import init_ledger, save_json
        ledger = init_ledger(ep)
        ok, _ = raw_candidate_budget.claim(ep, 1, "original", token="before-terminal")
        assert ok
        episode_lifecycle.terminate(ep, target="ABANDONED", source="direct_user:test", reason="stop production")
        with pytest.raises(RuntimeError, match="EPISODE_TERMINATED"):
            scheduler_core.save_queue(ep, {"schema_version": 1, "items": [], "waves": []})
        with pytest.raises(RuntimeError, match="EPISODE_TERMINATED"):
            raw_candidate_budget.claim(ep, 1, "original", token="late-claim")
        with pytest.raises(RuntimeError, match="EPISODE_TERMINATED"):
            raw_candidate_budget.commit(ep, "before-terminal")
        with pytest.raises(RuntimeError, match="EPISODE_TERMINATED"):
            save_json(ep / "meta/production-ledger.json", ledger)
