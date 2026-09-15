from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import derived_freshness
import runtime_resume_capsule
import workflow_observability


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_shared_freshness_detects_source_sha_drift():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        _write(ep / "meta/episode-state.json", {"current_state": "IDEA_LOCKED"})
        rows, fingerprint = derived_freshness.snapshot(ep, ["meta/episode-state.json"])
        data = {"source_files": rows, "source_fingerprint": fingerprint}
        assert derived_freshness.is_fresh(ep, data, ["meta/episode-state.json"])
        _write(ep / "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        assert not derived_freshness.is_fresh(ep, data, ["meta/episode-state.json"])


def test_resume_capsule_read_rebuilds_after_source_drift():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        _write(ep / "meta/episode-state.json", {"current_state": "IDEA_LOCKED"})
        first = runtime_resume_capsule.compile_capsule(ep, write=True)
        _write(ep / "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        second = runtime_resume_capsule.load_fresh(ep, write=True)
        assert second["source_fingerprint"] != first["source_fingerprint"]
        assert second["current_state"] == "STORYBOARD_LOCKED"


def test_workflow_observability_read_rebuilds_after_ledger_drift():
    test_root = ROOT / "episodes/_tests"
    test_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=test_root) as td:
        ep = Path(td)
        _write(ep / "meta/episode-state.json", {"current_state": "VISUAL_CALIBRATED"})
        _write(ep / "meta/production-ledger.json", {"frames": {}})
        first = workflow_observability.collect(ep, write=True)
        _write(ep / "meta/production-ledger.json", {"frames": {"01": {"status": "PASSED"}}})
        second = workflow_observability.load_fresh(ep, write=True)
        assert second["source_fingerprint"] != first["source_fingerprint"]
        assert second["production"]["ledger_status_counts"] == {"PASSED": 1}
