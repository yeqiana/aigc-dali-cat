"""The grandfathered historical Episode failures are not a blanket exemption."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import ci_episode_legacy_regression as gate


def _baseline(tmp_path, monkeypatch):
    episodes = ["episodes/00_独立篇/example"]
    debt = "episodes/00_独立篇/example | [FAIL] missing_path: historical asset"
    data = {
        "schema_version": 1,
        "baseline_commit": gate.BASE_SHA,
        "validators": {name: {
            "checked_episodes": episodes,
            "failures": {debt: 1},
            "failure_count": 1,
            "strict_exit_code": 1,
        } for name in gate.VALIDATORS},
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(gate, "BASELINE", path)
    return data, debt


def test_exact_historical_debt_remains_visible_but_does_not_regress(tmp_path, monkeypatch, capsys):
    data, _ = _baseline(tmp_path, monkeypatch)
    monkeypatch.setattr(gate, "_record", lambda _root, name: data["validators"][name])
    assert gate.check() == 0
    output = capsys.readouterr().out
    assert "HISTORICAL_UNRESOLVED" in output
    assert "do NOT grant PUBLISH_READY" in output


def test_new_review_failure_is_blocked(tmp_path, monkeypatch, capsys):
    data, debt = _baseline(tmp_path, monkeypatch)
    def altered(_root, name):
        row = dict(data["validators"][name])
        row["failures"] = {debt: 1,
                           "episodes/00_独立篇/example | [FAIL] verified_review_authority: unverified": 1}
        row["failure_count"] = 2
        return row
    monkeypatch.setattr(gate, "_record", altered)
    assert gate.check() == 1
    assert "NEW_FAILURE" in capsys.readouterr().out


def test_omitted_episode_is_blocked(tmp_path, monkeypatch, capsys):
    data, debt = _baseline(tmp_path, monkeypatch)
    def altered(_root, name):
        row = dict(data["validators"][name])
        row["checked_episodes"] = []
        row["failures"] = {}
        row["failure_count"] = 0
        row["strict_exit_code"] = 0
        return row
    monkeypatch.setattr(gate, "_record", altered)
    assert gate.check() == 1
    assert "omitted=" in capsys.readouterr().out


def test_unrecognized_baseline_revision_fails_closed(tmp_path, monkeypatch):
    data, _ = _baseline(tmp_path, monkeypatch)
    data["baseline_commit"] = "0" * 40
    gate.BASELINE.write_text(json.dumps(data), encoding="utf-8")
    import pytest
    with pytest.raises(RuntimeError, match="unrecognized pinned baseline"):
        gate.check()
