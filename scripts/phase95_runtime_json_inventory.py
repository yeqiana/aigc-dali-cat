#!/usr/bin/env python3
"""只读盘点 Runtime/Episode JSON 的数量、大小与存储归属。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from episodes._system.episode_storage_policy import classify


TARGETS = ("MYSQL", "REDIS", "FILE", "EXPORT_ONLY", "UNKNOWN")


def _episode_relative(path: Path, root: Path) -> tuple[str, str]:
    """返回分类相对路径与扫描范围标签。"""
    parts = path.relative_to(root).parts
    if "meta" in parts:
        meta_index = parts.index("meta")
        rel = Path(*parts[meta_index:])
        scope = str(Path(*parts[:meta_index])) or "."
        return rel.as_posix(), scope
    return path.relative_to(root).as_posix(), "."


def inventory(root: Path) -> dict:
    counts = Counter()
    bytes_by_target = Counter()
    export_only_count = 0
    export_only_bytes = 0
    excluded_count = 0
    excluded_bytes = 0
    families = Counter()
    largest: list[dict] = []
    unknown: list[dict] = []
    files = list(root.rglob("*.json")) if root.exists() else []
    for path in files:
        size = path.stat().st_size
        top_scope = path.relative_to(root).parts[0] if path.relative_to(root).parts else ""
        if top_scope in {"_external", "_tests"}:
            excluded_count += 1
            excluded_bytes += size
            continue
        rel, scope = _episode_relative(path, root)
        decision = classify(rel)
        counts[decision.target] += 1
        bytes_by_target[decision.target] += size
        if decision.legacy_file == "EXPORT_ONLY":
            export_only_count += 1
            export_only_bytes += size
        families[decision.family] += 1
        item = {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "scope": scope,
            "bytes": size,
            "target": decision.target,
            "family": decision.family,
            "reason": decision.reason,
        }
        largest.append(item)
        if decision.target == "UNKNOWN":
            unknown.append(item)
    largest.sort(key=lambda item: item["bytes"], reverse=True)
    return {
        "root": str(root),
        "scanned_json_files": len(files),
        "json_files": len(largest),
        "total_bytes": sum(item["bytes"] for item in largest),
        "excluded_non_production": {"files": excluded_count, "bytes": excluded_bytes},
        "targets": {target: counts.get(target, 0) for target in TARGETS},
        "bytes_by_target": {target: bytes_by_target.get(target, 0) for target in TARGETS},
        "export_only": {"files": export_only_count, "bytes": export_only_bytes},
        "families": dict(families.most_common()),
        "unknown": sorted(unknown, key=lambda item: item["path"]),
        "largest": largest[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps([inventory(root) for root in args.root], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
