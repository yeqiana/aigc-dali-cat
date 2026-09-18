from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_ledger  # noqa: E402
import production_ledger_persistence as persistence  # noqa: E402


def _mode(monkeypatch, value: str) -> None:
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": value},
    )


def test_json_authority_reads_complete_document(monkeypatch, tmp_path):
    _mode(monkeypatch, "json")
    meta = tmp_path / "meta"
    meta.mkdir()
    payload = {"frames": {"01": {"status": "LOCKED"}}, "policy": {"x": 1}}
    (meta / "production-ledger.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    assert production_ledger.load_authority(tmp_path) == payload
    assert production_ledger.authority_exists(tmp_path) is True
    assert production_ledger.authority_sha256(tmp_path)


def test_dual_authority_keeps_complete_document(monkeypatch, tmp_path):
    _mode(monkeypatch, "dual")
    meta = tmp_path / "meta"
    meta.mkdir()
    payload = {"frames": {"01": {"reviews": [{"decision": "pass"}]}}}
    (meta / "production-ledger.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    assert production_ledger.load_authority(tmp_path) == payload


def test_mysql_authority_fails_closed_even_with_stale_file(monkeypatch, tmp_path):
    _mode(monkeypatch, "mysql")
    meta = tmp_path / "meta"
    meta.mkdir()
    (meta / "production-ledger.json").write_text(
        '{"frames":{"01":{"status":"LOCKED"}}}', encoding="utf-8"
    )
    with pytest.raises(
        persistence.ProductionLedgerAuthorityIncomplete,
        match="PRODUCTION_LEDGER_MYSQL_CUTOVER_INCOMPLETE",
    ):
        production_ledger.load_authority(tmp_path)
    with pytest.raises(persistence.ProductionLedgerAuthorityIncomplete):
        production_ledger.authority_exists(tmp_path)
    with pytest.raises(persistence.ProductionLedgerAuthorityIncomplete):
        production_ledger.authority_sha256(tmp_path)
