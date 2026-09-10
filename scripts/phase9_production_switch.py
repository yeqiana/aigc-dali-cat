"""Phase9 生产归属切换执行器（P9.34.3，阻塞项 #7）。

把生产归属从 V2_RUNTIME 切到 V3_RUNTIME，落到 RuntimePrimaryRegistry 并持久化为
meta/runtime/runtime-primary.json。默认 dry-run 只打印将发生的变化，--apply 才落盘。

安全姿态：
    - 默认 dry-run，不改变 meta/runtime/runtime-primary.json。
    - 只支持 --to V3_RUNTIME（回退由 Canary rollback 负责，不在此处）。
    - 不删除 V2 runtime、不改 episode state / release 资产、不写凭据。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_ENV_ERROR = 3


def _bootstrap_story_platform() -> None:
    """把 import platform 指向仓库内 platform 包，而不是 stdlib platform。"""
    target = (PROJECT_ROOT / "platform" / "__init__.py").resolve()
    existing = sys.modules.get("platform")
    existing_file = getattr(existing, "__file__", None)
    if existing_file:
        try:
            if Path(existing_file).resolve() == target:
                return
        except OSError:
            pass

    root = str(PROJECT_ROOT)
    while root in sys.path:
        sys.path.remove(root)
    sys.path.insert(0, root)

    spec = importlib.util.spec_from_file_location(
        "platform",
        target,
        submodule_search_locations=[str(target.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Story OS platform package from " + str(target))
    module = importlib.util.module_from_spec(spec)
    sys.modules["platform"] = module
    spec.loader.exec_module(module)


_bootstrap_story_platform()

from platform.gateway.runtime_primary_persistence import (  # noqa: E402
    DEFAULT_RUNTIME_PRIMARY_PATH,
    load_runtime_primary,
    save_runtime_primary,
)
from platform.gateway.runtime_primary_registry import RuntimePrimaryRegistry  # noqa: E402


def plan_switch(current, target: str, reason: str):
    """纯函数：返回 (new_record, changed)。目标相同则 changed=False。"""
    registry = RuntimePrimaryRegistry(current.primary_runtime)
    new_record = registry.promote_to(target, reason=reason)
    changed = new_record.primary_runtime != current.primary_runtime
    return new_record, changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Story OS V3 Phase9 生产归属切换执行器")
    parser.add_argument("action", choices=("status", "switch"))
    parser.add_argument("--to", default="V3_RUNTIME", choices=("V3_RUNTIME",))
    parser.add_argument("--primary-file", default=str(DEFAULT_RUNTIME_PRIMARY_PATH))
    parser.add_argument("--reason", default="production_migration_finalized")
    parser.add_argument("--apply", action="store_true", help="真正落盘切换；默认 dry-run 只打印")
    args = parser.parse_args(argv)

    current = load_runtime_primary(args.primary_file)

    if args.action == "status":
        print("当前生产归属：primary=" + current.primary_runtime
              + " previous=" + str(current.previous_runtime)
              + " reason=" + current.reason
              + " updated_at=" + current.updated_at)
        return EXIT_OK

    new_record, changed = plan_switch(current, args.to, args.reason)
    if not changed:
        print("[NO-OP] 生产归属已经是 " + current.primary_runtime)
        return EXIT_OK

    if args.apply:
        path = save_runtime_primary(new_record, args.primary_file)
        print("[APPLY] 生产归属已切换 " + current.primary_runtime
              + " -> " + new_record.primary_runtime)
        print("  evidence=" + str(path))
    else:
        print("[DRY-RUN] 生产归属将切换 " + current.primary_runtime
              + " -> " + new_record.primary_runtime)
        print("  加 --apply 才真正落盘切换")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
