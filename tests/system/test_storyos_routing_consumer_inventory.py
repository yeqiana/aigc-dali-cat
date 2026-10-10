"""Module consumer inventory is static, read-only and conservative."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("routing_audit", ROOT / "scripts/storyos_routing_consumer_inventory.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_import_scanner_ignores_string_matches():
    assert mod.imported_modules("import runtime_scheduler\ns='import runtime_router'") == {"runtime_scheduler"}


def test_consumer_count_and_dynamic_warning(tmp_path):
    (tmp_path / "runtime_scheduler.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "work.py").write_text("from runtime_scheduler import authorize\n", encoding="utf-8")
    (tmp_path / "idle.py").write_text("x='runtime_scheduler'\n", encoding="utf-8")
    report = mod.inventory(tmp_path, {"runtime_scheduler": "dispatch"})
    assert report["parse_errors"] == {}
    row = report["modules"][0]
    assert row["static_consumers"] == ["work.py"]
    assert row["static_consumer_count"] == 1
    assert report["absence_of_static_consumers_proves_unused"] is False


def test_real_router_inventory_has_no_parse_errors():
    report = mod.inventory(mod.SYSTEM)
    assert report["parse_errors"] == {}
    assert {r["module"] for r in report["modules"]} == set(mod.ROLES)
