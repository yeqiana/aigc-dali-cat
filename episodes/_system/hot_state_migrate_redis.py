#!/usr/bin/env python3
"""Backfill rebuildable Episode hot state into Redis before redis-only cutover.

The migration is intentionally non-destructive: compatibility files are never
removed.  Redis values are written and read back in dual mode; after a
successful cutover the normal readers become Redis-authoritative and stop
falling back to these files.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_discovery
import hot_state_bridge
import runtime_workspace
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file


SOURCES: dict[str, Path] = {
    "NEXT_ACTION": Path("meta/runtime/next-action.json"),
    "DRIVER_STATE": Path("meta/runtime/driver.json"),
    "DRIVER_HEARTBEAT": Path("meta/runtime/driver-beacon.json"),
    "CIRCUIT_BREAKER": Path("meta/runtime/circuit-breaker.json"),
    "INFLIGHT": Path("meta/runtime/in-flight-codex.json"),
    "HOST_REQUEST_CURRENT": Path("meta/runtime/product-host-request.json"),
    "QUEUE": Path("meta/production-queue.json"),
    "EFFECTIVE_CONFIG": Path("meta/runtime/effective-config.json"),
    "RUNTIME_CAPABILITIES": Path("meta/runtime/runtime-capabilities.json"),
    "RUNNER_STATE": Path("meta/runtime-runner-state.json"),
    "RUNTIME_ROUTE": Path("meta/runtime-route.json"),
    "RESUME_TOKEN": Path("meta/runtime-resume-token.json"),
    "RESUME_CAPSULE": Path("meta/runtime/resume-capsule.json"),
    "FAST_PATH": Path("meta/runtime/fast-path-state.json"),
    "FULL_AUTO_STATUS": Path("meta/runtime/full-auto-status.json"),
    "TRACE_CURRENT": Path("meta/runtime/trace-current.json"),
    "TRANSPORT_STATE": Path("meta/transport-state.json"),
    "BATCH_CAPABILITY": Path("meta/batch-provider-capability.json"),
    "CODEX_BATCH_CAPABILITY": Path("meta/codex-subscription-batch-capability.json"),
}


def scan(episodes_root: Path = ROOT / "episodes") -> list[dict]:
    rows: list[dict] = []
    for ep in episode_discovery.iter_episode_roots(episodes_root):
        episode = Path(ep).resolve()
        for kind, rel in SOURCES.items():
            path = runtime_workspace.resolve_read_path(episode, rel)
            if not path.is_file():
                continue
            payload = story_json.read_json(path, default=None, require_object=False)
            if not isinstance(payload, dict):
                raise ValueError(f"hot-state source must be object: {path}")
            rows.append({
                "episode": episode,
                "kind": kind,
                "rel": rel,
                "path": path,
                "payload": payload,
                "source_kind": runtime_workspace.source_kind(episode, rel),
            })
    return rows


def apply(rows: list[dict], *, reconcile: bool) -> dict:
    written = reconciled = 0
    by_kind: dict[str, int] = {}
    for row in rows:
        result = hot_state_bridge.mirror(row["episode"], row["kind"], row["payload"])
        if result.get("redis_written") is not True:
            raise RuntimeError(
                f"Redis mirror failed: {row['episode']} {row['kind']}: {result}"
            )
        written += 1
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
        if reconcile:
            loaded = hot_state_bridge.read(row["episode"], row["kind"])
            if loaded.get("redis_read") is not True or loaded.get("value") != row["payload"]:
                raise ValueError(
                    f"Redis hot-state reconcile mismatch: {row['episode']} {row['kind']}"
                )
            reconciled += 1
    return {"written": written, "reconciled": reconciled, "by_kind": by_kind}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reconcile", action="store_true")
    ap.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = ap.parse_args(argv)

    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    # Backfill must run in dual semantics: files remain readable while every
    # discovered value is copied and read back from Redis.
    os.environ["STORYOS_HOT_STATE_MODE"] = "dual"

    rows = scan()
    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "files": len(rows),
        "runtime_env_keys": list(loaded),
        "secret_values_printed": False,
        "source_kinds": {
            name: sum(1 for row in rows if row["source_kind"] == name)
            for name in sorted({row["source_kind"] for row in rows})
        },
    }
    if args.apply:
        summary["result"] = apply(rows, reconcile=args.reconcile)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
