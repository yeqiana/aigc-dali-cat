from __future__ import annotations
import sys
from pathlib import Path
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import consumer_inventory as inv

def test_ast_consumer_inventory_detects_both_low_level_and_facade(tmp_path):
    d=tmp_path/"episodes"/"_system"
    d.mkdir(parents=True)
    (d/"sample.py").write_text(
        "import codex_user_runner as cu\n"
        "from codex_user_runner import execute_codex as remote\n"
        "cu.run_codex(['codex','exec','-'])\n"
        "remote(None)\n",encoding="utf8")
    rows=inv.scan(tmp_path)
    assert [x["entrypoint"] for x in rows]==["run_codex","execute_codex"]
    assert rows[1]["migration_priority"]=="DIRECT_TASK_BYPASS"

def test_inventory_covers_existing_direct_task_consumers_read_only():
    root=Path(__file__).resolve().parents[2]
    rows=inv.scan(root)
    assert any(x["entrypoint"]=="run_codex" for x in rows)
    assert not any(x["entrypoint"] in {"execute_task", "execute_codex"} for x in rows)
    assert len([x for x in rows if x["entrypoint"]=="execute_model_task"])==3
    assert any(x["file"].endswith("world_prepare_model_producer.py") for x in rows)

def test_legacy_runner_implementation_is_not_mistaken_for_a_consumer():
    root=Path(__file__).resolve().parents[2]
    assert not any(x["file"].endswith("/codex_user_runner.py") for x in inv.scan(root))

def test_preimage_agents_have_no_direct_task_bypass():
    root=Path(__file__).resolve().parents[2]
    rows=inv.scan(root)
    migrated={x["file"] for x in rows if x["entrypoint"]=="execute_model_task"}
    assert len(migrated)==3
    assert any(x.endswith("world_prepare_model_producer.py") for x in migrated)
    assert any(x.endswith("character_finalize_model_producer.py") for x in migrated)
    assert any(x.endswith("visual_narrative_prepare_model_producer.py") for x in migrated)
    assert not [x for x in rows if x["migration_priority"]=="DIRECT_TASK_BYPASS"]

def test_operational_run_codex_callers_migrated_but_cli_diagnostics_remain():
    root=Path(__file__).resolve().parents[2]
    rows=inv.scan(root)
    by_method={}
    for row in rows:
        by_method.setdefault(row["entrypoint"],[]).append(row)
    assert len(by_method.get("execute_model_task",[]))==3
    assert len(by_method.get("run_model_codex",[]))==10
    assert len(by_method.get("run_codex",[]))==2
    assert all(x["file"].endswith("codex_subscription_image.py") for x in by_method["run_codex"])
    assert not [r for r in rows if r["migration_priority"]=="DIRECT_TASK_BYPASS"]
