#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS runtime-log retention policy and Git hygiene audit.

High-volume worker/trace logs are local derived diagnostics, not Story/Release
authority. This module never deletes files or mutates Git; it reports historical
tracked raw logs so maintainers can untrack/GC them deliberately.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import story_json

ROOT = Path(__file__).resolve().parents[2]
LOCAL_ONLY_PATTERNS = (
    "episodes/**/meta/image-workers/**",
    "episodes/**/meta/rolling-review-workers/**",
    "episodes/**/meta/scoped-workers/**",
    "episodes/**/meta/codex-auto-run.jsonl",
    "episodes/**/meta/runtime/trace-events.jsonl",
    "episodes/**/meta/runtime/node-execution.jsonl",
    "episodes/**/meta/runtime/authority-commit.jsonl",
    "episodes/**/meta/episode-performance-ledger.json",
    "episodes/**/meta/workflow-run.jsonl",
)

# W-14: Codex emits user-environment diagnostics (plugins/MCP/telemetry/shell
# snapshot/hooks) into the same stdout stream as the image backend. Keep that raw
# stream untouched for audit, but never let unrelated warnings become image
# provider 401/429/network evidence. Matching is intentionally line-scoped.
CODEX_NOISE_RULES = {
    "legacy_notify": ("legacy_notify", "hook_runtime"),
    "powershell_shell_snapshot": ("shell snapshot not supported yet for powershell",),
    "mcp": (" mcp ", "mcp_", '"mcp'),
    "plugin": ("plugin",),
    "telemetry": ("telemetry", "opentelemetry"),
    "websocket_prewarm": ("websocket prewarm", "prewarm websocket"),
}


def _codex_noise_kind(line: str) -> str | None:
    low = str(line or "").lower()
    for kind, markers in CODEX_NOISE_RULES.items():
        if any(marker in low for marker in markers):
            return kind
    return None


def codex_noise_summary(text: str) -> dict:
    counts: dict[str, int] = {}
    total_lines = 0
    noise_lines = 0
    for line in str(text or "").splitlines():
        total_lines += 1
        kind = _codex_noise_kind(line)
        if kind is None:
            continue
        counts[kind] = counts.get(kind, 0) + 1
        noise_lines += 1
    return {
        "schema_version": 1,
        "policy": "raw_log_preserved_provider_classification_filtered",
        "total_lines": total_lines,
        "noise_lines": noise_lines,
        "provider_relevant_lines": max(0, total_lines - noise_lines),
        "counts": counts,
    }


def provider_relevant_codex_text(text: str) -> str:
    """Return a classifier-only view; the raw worker log remains unchanged."""
    return "\n".join(
        line for line in str(text or "").splitlines()
        if _codex_noise_kind(line) is None
    )


def write_codex_noise_summary(log_path: Path, text: str) -> dict:
    summary = codex_noise_summary(text)
    sidecar = Path(str(log_path) + ".noise.json")
    story_json.write_json(sidecar, summary)
    return summary


def tracked_local_logs(root: Path = ROOT) -> list[Path]:
    if not (root / ".git").exists():
        return []
    cmd = ["git", "-C", str(root), "ls-files", "--", *LOCAL_ONLY_PATTERNS]
    cp = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if cp.returncode != 0:
        return []
    return [root / line.strip() for line in cp.stdout.splitlines() if line.strip()]


def audit(root: Path = ROOT) -> dict:
    tracked = tracked_local_logs(root)
    existing = [p for p in tracked if p.is_file()]
    total = sum(p.stat().st_size for p in existing)
    return {
        "schema_version": 1,
        "policy": "local_derived_not_git_authority",
        "tracked_historical_count": len(tracked),
        "tracked_existing_count": len(existing),
        "tracked_existing_bytes": total,
        "paths": [p.relative_to(root).as_posix() for p in existing],
        "action": "historical tracked logs may be git rm --cached then git gc; do not delete formal review JSON/SHA evidence",
    }


def self_test() -> None:
    assert "episodes/**/meta/image-workers/**" in LOCAL_ONLY_PATTERNS
    assert "episodes/**/meta/workflow-run.jsonl" in LOCAL_ONLY_PATTERNS
    assert "episodes/**/meta/runtime/node-execution.jsonl" in LOCAL_ONLY_PATTERNS
    assert "episodes/**/meta/runtime/authority-commit.jsonl" in LOCAL_ONLY_PATTERNS
    assert "episodes/**/meta/episode-performance-ledger.json" in LOCAL_ONLY_PATTERNS
    sample = "WARN plugin request 429\nimage generation failed: 503 Service Unavailable\nlegacy_notify os error 206"
    assert codex_noise_summary(sample)["noise_lines"] == 2
    assert "503 Service Unavailable" in provider_relevant_codex_text(sample)
    assert "429" not in provider_relevant_codex_text(sample)
    print("RUNTIME LOG POLICY V2.6.1.1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["audit", "self-test"], nargs="?", default="audit")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
