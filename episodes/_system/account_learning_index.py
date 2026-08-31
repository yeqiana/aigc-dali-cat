#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate post-publish learning packets into account-level evidence for the next story.

The index is descriptive evidence, not creative authority.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "account-learning-index.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def discover() -> list[dict]:
    rows = []
    root = ROOT / "episodes"
    if not root.is_dir():
        return rows
    for p in root.rglob("meta/next-story-learning.json"):
        if "_system" in p.parts:
            continue
        try:
            d = read_json(p)
            if d.get("evidence_only") is not True:
                continue
            d["_path"] = p.relative_to(ROOT).as_posix()
            rows.append(d)
        except Exception:
            continue
    rows.sort(key=lambda x: str(x.get("published_at") or ""), reverse=True)
    return rows


def numeric_values(rows: list[dict], field: str) -> list[float]:
    vals = []
    for row in rows:
        value = (row.get("latest_rates") or {}).get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            vals.append(float(value))
    return vals


def metric_values(rows: list[dict], field: str) -> list[float]:
    vals = []
    for row in rows:
        value = (row.get("latest_metrics") or {}).get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            vals.append(float(value))
    return vals


def top_by(rows: list[dict], source: str, field: str, limit: int = 3) -> list[dict]:
    candidates = []
    for row in rows:
        value = (row.get(source) or {}).get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            candidates.append((float(value), row))
    candidates.sort(key=lambda x: x[0], reverse=True)
    out = []
    for value, row in candidates[:limit]:
        ep = row.get("source_episode") or {}
        out.append({
            "episode_id": ep.get("id"),
            "title": ep.get("title"),
            "published_at": row.get("published_at"),
            "value": value,
            "concept_binding": row.get("concept_binding") or {},
        })
    return out


def rebuild(limit: int = 5) -> dict:
    all_rows = discover()
    recent = all_rows[:max(1, limit)]
    rate_fields = ["like_rate","comment_rate","share_rate","save_rate","follow_rate","profile_visit_rate","completion_rate"]
    medians = {}
    for field in rate_fields:
        vals = numeric_values(recent, field)
        if vals:
            medians[field] = round(statistics.median(vals), 6)
    views = metric_values(recent, "views")
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "evidence_only": True,
        "direct_creative_authority": False,
        "sample_size": len(recent),
        "recent_limit": limit,
        "account_baseline": {
            "median_rates": medians,
            "median_views": round(statistics.median(views), 3) if views else None,
            "note": "Account-relative descriptive baseline; not a platform universal threshold.",
        },
        "top_observed": {
            "views": top_by(recent, "latest_metrics", "views"),
            "save_rate": top_by(recent, "latest_rates", "save_rate"),
            "comment_rate": top_by(recent, "latest_rates", "comment_rate"),
            "share_rate": top_by(recent, "latest_rates", "share_rate"),
            "completion_rate": top_by(recent, "latest_rates", "completion_rate"),
        },
        "recent_episodes": [
            {
                "source_episode": row.get("source_episode") or {},
                "published_at": row.get("published_at"),
                "latest_checkpoint": row.get("latest_checkpoint"),
                "latest_metrics": row.get("latest_metrics") or {},
                "latest_rates": row.get("latest_rates") or {},
                "concept_binding": row.get("concept_binding") or {},
                "learning_path": row.get("_path"),
            }
            for row in recent
        ],
        "next_story_input": {
            "use": "Evidence for topic/concept selection and mechanism diversity.",
            "do_not": [
                "Do not mechanically repeat the top-view episode.",
                "Do not treat one weak post as proof that high-ambition concepts are bad.",
                "Do not override Story/Concept gates with engagement data.",
            ],
        },
    }
    write_json(REPORT, report)
    return report


def self_test() -> None:
    rows = [{"latest_rates":{"like_rate":0.1}},{"latest_rates":{"like_rate":0.2}}]
    assert numeric_values(rows, "like_rate") == [0.1,0.2]
    print("ACCOUNT LEARNING INDEX V2.1 PHASE10 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rebuild"); p.add_argument("--limit", type=int, default=5)
    sub.add_parser("show")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test":
        self_test(); return 0
    if a.cmd == "rebuild":
        print(json.dumps(rebuild(a.limit), ensure_ascii=False, indent=2)); return 0
    if not REPORT.is_file():
        rebuild()
    print(REPORT.read_text(encoding="utf-8")); return 0


if __name__ == "__main__":
    raise SystemExit(main())
