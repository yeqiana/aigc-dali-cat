"""Phase9 生产归属切换执行器（P9.34.3）的离线回归测试。

不碰真实切换，锁住持久化与切换语义：
1. load 缺文件返回 V2_RUNTIME initial；
2. save + load roundtrip；
3. plan_switch V2 -> V3 产生 previous=V2；
4. plan_switch V3 -> V3 不变；
5. CLI status / switch dry-run / switch --apply。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from platform.gateway.runtime_primary_persistence import (  # noqa: E402
    load_runtime_primary,
    save_runtime_primary,
)
from platform.gateway.runtime_primary_registry import RuntimePrimaryRecord  # noqa: E402
from scripts.phase9_production_switch import main, plan_switch  # noqa: E402


def test_load_missing_returns_v2_initial(tmp_path):
    record = load_runtime_primary(tmp_path / "nope.json")
    assert record.primary_runtime == "V2_RUNTIME"
    assert record.previous_runtime is None
    assert record.reason == "initial_runtime"


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "primary.json"
    record = RuntimePrimaryRecord(
        primary_runtime="V3_RUNTIME",
        previous_runtime="V2_RUNTIME",
        reason="production_migration_finalized",
        updated_at="2026-09-10T00:00:00+00:00",
    )
    save_runtime_primary(record, path)
    loaded = load_runtime_primary(path)
    assert loaded == record
    assert not (tmp_path / "primary.json.tmp").exists()


def test_plan_switch_v2_to_v3():
    current = RuntimePrimaryRecord("V2_RUNTIME", None, "initial_runtime", "")
    new_record, changed = plan_switch(current, "V3_RUNTIME", "production_migration_finalized")
    assert changed is True
    assert new_record.primary_runtime == "V3_RUNTIME"
    assert new_record.previous_runtime == "V2_RUNTIME"


def test_plan_switch_already_v3_is_noop():
    current = RuntimePrimaryRecord("V3_RUNTIME", "V2_RUNTIME", "x", "")
    new_record, changed = plan_switch(current, "V3_RUNTIME", "production_migration_finalized")
    assert changed is False
    assert new_record.primary_runtime == "V3_RUNTIME"


def test_cli_status_reads_file(tmp_path):
    path = tmp_path / "primary.json"
    save_runtime_primary(
        RuntimePrimaryRecord("V2_RUNTIME", None, "initial_runtime", "2026-09-10T00:00:00+00:00"),
        path,
    )
    assert main(["status", "--primary-file", str(path)]) == 0


def test_cli_switch_dry_run_does_not_write(tmp_path):
    path = tmp_path / "primary.json"
    assert main(["switch", "--primary-file", str(path)]) == 0
    assert not path.exists()


def test_cli_switch_apply_writes(tmp_path):
    path = tmp_path / "primary.json"
    assert main(["switch", "--primary-file", str(path), "--apply"]) == 0
    assert load_runtime_primary(path).primary_runtime == "V3_RUNTIME"
