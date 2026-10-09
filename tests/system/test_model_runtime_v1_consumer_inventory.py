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
    assert any(x["entrypoint"]=="execute_task" for x in rows)
    assert any(x["entrypoint"]=="execute_codex" for x in rows)
    assert any(x["file"].endswith("world_prepare_model_producer.py") for x in rows)

def test_legacy_runner_implementation_is_not_mistaken_for_a_consumer():
    root=Path(__file__).resolve().parents[2]
    assert not any(x["file"].endswith("/codex_user_runner.py") for x in inv.scan(root))
