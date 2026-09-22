#!/usr/bin/env python3
"""只读审计 Production Queue 的实际 authority，不执行迁移。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
for path in (ROOT, SYSTEM):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import production_queue_store  # noqa: E402


def audit(episodes_root: Path) -> dict:
    rows = []
    for state_path in sorted(episodes_root.rglob("meta/episode-state.json")):
        episode = state_path.parent.parent
        status = production_queue_store.migration_status(episode)
        rows.append({
            "episode": str(episode.relative_to(episodes_root)).replace("\\", "/"),
            "authority": status.get("authority"),
            "effective_storage_mode": status.get("effective_storage_mode"),
            "activation_state": status.get("activation_state"),
            "cutover_ready": bool(status.get("cutover_ready")),
            "legacy_present": production_queue_store.legacy_path(episode).is_file(),
            "workspace_present": production_queue_store.workspace_candidate(episode).is_file(),
        })
    return {
        "episodes_root": str(episodes_root),
        "episode_count": len(rows),
        "authority_counts": dict(Counter(row["authority"] for row in rows)),
        "storage_mode_counts": dict(Counter(row["effective_storage_mode"] for row in rows)),
        "legacy_pinned": [row for row in rows if row["authority"] == "legacy_episode"],
        "invalid": [row for row in rows if row["authority"] == "invalid_fail_closed"],
        "read_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-root", type=Path, default=ROOT / "episodes")
    args = parser.parse_args()
    print(json.dumps(audit(args.episodes_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
