"""Runtime Primary 持久化（P9.34.3，阻塞项 #7 前置）。

把 RuntimePrimaryRecord 落盘为 meta/runtime/runtime-primary.json，作为生产归属
切换的事实证据。本模块只读写文件，不做切换决策；切换由 CLI 依据
RuntimePrimaryRegistry.promote_to 完成。

安全姿态：
    - 默认只读写，不切换；CLI --apply 才落盘切换。
    - 原子写（tmp + os.replace），不写凭据。
    - 文件缺失时返回 V2_RUNTIME initial（诚实默认，不猜测）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from platform.gateway.runtime_primary_registry import (
    RuntimePrimaryRecord,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNTIME_PRIMARY_PATH = PROJECT_ROOT / "meta" / "runtime" / "runtime-primary.json"


def load_runtime_primary(path=None) -> RuntimePrimaryRecord:
    """读取当前生产归属；文件缺失时返回 V2_RUNTIME initial。"""
    target = Path(path) if path else DEFAULT_RUNTIME_PRIMARY_PATH
    if not target.exists():
        return RuntimePrimaryRecord(
            primary_runtime="V2_RUNTIME",
            previous_runtime=None,
            reason="initial_runtime",
            updated_at="",
        )
    data = json.loads(target.read_text(encoding="utf-8"))
    return RuntimePrimaryRecord(
        primary_runtime=data["primary_runtime"],
        previous_runtime=data.get("previous_runtime"),
        reason=data.get("reason", ""),
        updated_at=data.get("updated_at", ""),
    )


def save_runtime_primary(record: RuntimePrimaryRecord, path=None) -> Path:
    """原子落盘 RuntimePrimaryRecord，返回写入路径。"""
    target = Path(path) if path else DEFAULT_RUNTIME_PRIMARY_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "primary_runtime": record.primary_runtime,
        "previous_runtime": record.previous_runtime,
        "reason": record.reason,
        "updated_at": record.updated_at,
    }
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(tmp, target)
    return target
