from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_checkpoint
import runtime_dag


def test_validate_target_uses_in_process_gate_apis_not_python_subprocesses():
    with patch.object(runtime_dag.validate_episode, "validate_episode", return_value=[]), \
            patch.object(runtime_dag.machine_gate, "validate", return_value=[]), \
            patch.object(runtime_dag.evidence_gate, "run_gate", return_value=(True, [])), \
            patch.object(runtime_dag, "run", side_effect=AssertionError("subprocess gate path used")):
        assert runtime_dag.validate_target(ROOT, "STORYBOARD_LOCKED") == (True, "PASS")


def test_checkpoint_uses_in_process_writer_not_python_subprocess():
    with tempfile.TemporaryDirectory(prefix="storyos-checkpoint-") as raw:
        ep = Path(raw)
        path = ep / runtime_checkpoint.REL
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(runtime_checkpoint.ensure_shape({})), encoding="utf-8")
        with patch.object(runtime_dag, "run", side_effect=AssertionError("subprocess checkpoint path used")):
            runtime_dag.checkpoint(ep, "UNIT", "PASS", 0.1, "ok", attempt=1)
        data = runtime_checkpoint.load(ep, {})
        assert runtime_checkpoint.read_path(ep) != path
        assert data["step_runs"][-1]["step"] == "UNIT"
        assert data["step_runs"][-1]["status"] == "PASS"
