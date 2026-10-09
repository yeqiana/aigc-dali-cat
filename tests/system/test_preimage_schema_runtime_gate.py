from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_dag
import preimage_storage_preflight
import storage_config


def test_hosted_preimage_refuses_missing_v2_schema_before_materialization(monkeypatch):
    monkeypatch.setattr(storage_config, "episode_meta_store_config",
                        lambda: {"mode": "mysql"})
    with patch.object(preimage_storage_preflight, "inspect", return_value={
            "schema_check_passed": False, "status": "V2_SCHEMA_MISSING"}) as probe:
        with pytest.raises(RuntimeError, match="PREIMAGE_V2_SCHEMA_BLOCKED:V2_SCHEMA_MISSING"):
            runtime_dag._assert_preimage_storage_schema()
    probe.assert_called_once()


def test_hosted_preimage_dual_mode_must_verify_schema(monkeypatch):
    monkeypatch.setattr(storage_config, "episode_meta_store_config",
                        lambda: {"mode": "dual"})
    with patch.object(preimage_storage_preflight, "inspect", return_value={
            "schema_check_passed": False, "status": "V2_TABLES_MISSING"}):
        with pytest.raises(RuntimeError, match="V2_TABLES_MISSING"):
            runtime_dag._assert_preimage_storage_schema()


def test_json_only_preimage_skips_mysql_v2_probe(monkeypatch):
    monkeypatch.setattr(storage_config, "episode_meta_store_config",
                        lambda: {"mode": "json"})
    with patch.object(preimage_storage_preflight, "inspect") as probe:
        runtime_dag._assert_preimage_storage_schema()
    probe.assert_not_called()


def test_v2_structural_admission_does_not_serve_as_review_authority(monkeypatch):
    monkeypatch.setattr(storage_config, "episode_meta_store_config",
                        lambda: {"mode": "mysql"})
    with patch.object(preimage_storage_preflight, "inspect", return_value={
            "schema_check_passed": True,
            "production_authority_granted": False,
            "status": "V2_SCHEMA_PRESENT_UNATTESTED"}):
        runtime_dag._assert_preimage_storage_schema()


def test_both_hosted_preimage_materializers_have_early_schema_guard():
    source = (SYSTEM / "runtime_dag.py").read_text(encoding="utf-8-sig")
    for stage in ('PREIMAGE_FRAME_CONTRACT_COMPILE', 'PREIMAGE_VERIFY'):
        start = source.index('host_step=="' + stage + '"')
        portion = source[start:start + 400]
        assert "_assert_preimage_storage_schema()" in portion
        assert portion.index("_assert_preimage_storage_schema()") < portion.index(
            "preimage_directing_materializer.ensure(ep)")
