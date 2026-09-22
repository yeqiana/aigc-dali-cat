from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_dag


def test_release_recovery_reuses_prepare_auto_and_preserves_context(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    with mock.patch("release_preflight.cmd_prepare_auto", return_value=0) as prepare:
        rc, note = runtime_dag.run_release_preflight_recovery(ep, codex="codex.exe", timeout=321)
    assert rc == 0
    assert note == "RELEASE PREFLIGHT AUTO RECOVERY PASS"
    args = prepare.call_args.args[0]
    assert args.episode_dir == str(ep)
    assert args.codex == "codex.exe"
    assert args.timeout == 321


def test_release_recovery_preserves_nonzero_host_or_gate_result(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    with mock.patch("release_preflight.cmd_prepare_auto", return_value=20):
        rc, note = runtime_dag.run_release_preflight_recovery(ep)
    assert rc == 20
    assert "rc=20" in note


def test_release_recovery_exception_fails_closed(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    with mock.patch("release_preflight.cmd_prepare_auto", side_effect=RuntimeError("boom")):
        rc, note = runtime_dag.run_release_preflight_recovery(ep)
    assert rc == 4
    assert "FAIL" in note and "boom" in note


def test_release_recovery_runs_before_publish_ready_postcondition():
    source = (SYSTEM / "runtime_dag.py").read_text(encoding="utf-8-sig")
    recovery = source.index('if rc==0 and s.step_id=="RELEASE":')
    postcondition = source.index('if rc==0 and s.target_state:', recovery)
    assert recovery < postcondition
    block = source[recovery:postcondition]
    assert "run_release_preflight_recovery" in block
