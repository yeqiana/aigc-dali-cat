#!/usr/bin/env python3
"""Emit one immutable, synthetic P3 Story Semantic Critic contract smoke."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
AGENTS = SYSTEM / "agents"
if str(AGENTS) not in sys.path:
    sys.path.insert(0, str(AGENTS))

import story_semantic_critic_adapter as critic


def main() -> int:
    report = critic.fixture_shadow_smoke()
    report.update({
        "schema_version": 1,
        "kind": "p3_story_semantic_critic_shadow_fixture_smoke",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "decision_schema": "episodes/_system/agents/critic_decision.schema.json",
        "decision_schema_sha256": critic.sha256_file(SYSTEM / "agents" / "critic_decision.schema.json"),
        "note": "Synthetic fixture only; no real Critic model, Story Review, Episode Authority, Gate, or Episode state was changed.",
    })
    base = ROOT / "reports" / "p3-story-semantic-critic-shadow-fixture-20260927.json"
    path = base if not base.exists() else base.with_name("p3-story-semantic-critic-shadow-fixture-retry1-20260927.json")
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError:
        print(f"immutable fixture report already exists: {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "path": path.relative_to(ROOT).as_posix()}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
