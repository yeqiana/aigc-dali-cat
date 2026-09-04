#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 10 publish facts + post-publish data review.

Important: post-publish facts live outside release-manifest.json so the Phase8
Final Candidate Snapshot remains frozen and verifiable after publication.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
EVENT_REL = Path("meta/publish-event.json")
METRICS_REL = Path("meta/post-publish-metrics.json")
REVIEW_REL = Path("meta/post-publish-review.json")
LEARNING_REL = Path("meta/next-story-learning.json")
STATE_REL = Path("meta/data-review-state.json")
CHECKPOINTS = ("6h", "24h", "48h", "7d")
CHECKPOINT_ORDER = {name: i for i, name in enumerate(CHECKPOINTS)}
REQUIRED_FOR_DATA_REVIEWED = ("48h",)
MANIFEST_MUTATION_POLICY = "FORBIDDEN_AFTER_SNAPSHOT"
CUMULATIVE_KEYS = {
    "views", "likes", "comments", "shares", "saves", "favorites",
    "followers_gained", "followers_lost", "profile_visits",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def resolve_ep(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def state(ep: Path) -> str:
    p = ep / "meta/episode-state.json"
    if not p.is_file():
        raise ValueError("meta/episode-state.json missing")
    return str(read_json(p).get("current_state") or "")


def run_cmd(args: list[object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(x) for x in args],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def gate_transition(ep: Path, target: str, note: str) -> None:
    for cmd in (
        [sys.executable, SYSTEM / "validate_episode.py", ep, "--target", target],
        [sys.executable, SYSTEM / "machine_gate.py", ep, "--target", target],
        [sys.executable, SYSTEM / "evidence_gate.py", ep, "--target", target],
    ):
        cp = run_cmd(cmd)
        if cp.returncode != 0:
            raise ValueError(f"{Path(str(cmd[1])).name} target {target} failed:\n{cp.stdout[-3000:]}")
    cp = run_cmd([sys.executable, SYSTEM / "episode_state.py", "transition", ep, target, "--note", note])
    if cp.returncode != 0:
        raise ValueError(f"episode transition to {target} failed:\n{cp.stdout[-3000:]}")


def snapshot_sha(ep: Path) -> str | None:
    p = ep / "meta/final-candidate-snapshot.json"
    return str(read_json(p).get("snapshot_sha256") or "") if p.is_file() else None


def required(ep: Path) -> bool:
    p = ep / "meta/story-gates.json"
    if not p.is_file():
        return False
    try:
        gates = read_json(p)
        cfg = ((gates.get("post_publish") or {}).get("data_review") or {})
        return cfg.get("enabled") is True
    except Exception:
        return False


def enable(ep: Path) -> dict:
    p = ep / "meta/story-gates.json"
    if not p.is_file():
        raise ValueError("meta/story-gates.json missing")
    gates = read_json(p)
    post = gates.setdefault("post_publish", {})
    cfg = post.setdefault("data_review", {})
    cfg.update({
        "schema_version": 1,
        "enabled": True,
        "checkpoints": list(CHECKPOINTS),
        "required_for_data_reviewed": list(REQUIRED_FOR_DATA_REVIEWED),
        "learning_packet_is_authority": False,
        "release_manifest_mutation_after_snapshot": False,
    })
    write_json(p, gates)
    return cfg


def mark_published(
    ep: Path,
    *,
    published_at: str | None,
    platform: str | None,
    post_id: str | None,
    post_url: str | None,
    force: bool,
) -> dict:
    enable(ep)
    current = state(ep)
    if current not in {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}:
        raise ValueError(f"mark-published requires PUBLISH_READY or later, got {current}")
    event_path = ep / EVENT_REL
    existing = read_json(event_path) if event_path.is_file() else {}
    actual_time = published_at or existing.get("published_at") or now()
    if existing.get("published_at") and existing.get("published_at") != actual_time and not force:
        raise ValueError("publish-event already has a different published_at; use --force only for factual correction")
    manifest = read_json(ep / "meta/release-manifest.json")
    publication = manifest.get("publication") or {}
    event = {
        "schema_version": 1,
        "recorded_at": now(),
        "published_at": actual_time,
        "platform": platform or existing.get("platform") or publication.get("platform") or "douyin",
        "post_id": post_id if post_id is not None else existing.get("post_id"),
        "post_url": post_url if post_url is not None else existing.get("post_url"),
        "final_candidate_snapshot_sha256": snapshot_sha(ep),
        "release_manifest_immutable_after_snapshot": True,
        "note": "Post-publish facts are intentionally stored outside release-manifest.json.",
    }
    write_json(event_path, event)
    if current == "PUBLISH_READY":
        gate_transition(ep, "PUBLISHED", "Phase10 actual publication facts recorded without mutating frozen release manifest")
    return event


def parse_metric_pairs(pairs: list[str]) -> dict:
    out: dict[str, float | int] = {}
    for raw in pairs:
        if "=" not in raw:
            raise ValueError(f"metric must be key=value: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("metric key cannot be empty")
        try:
            number = float(value)
        except ValueError as exc:
            raise ValueError(f"metric value must be numeric: {raw}") from exc
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"metric must be finite and >=0: {raw}")
        out[key] = int(number) if number.is_integer() else number
    return out


def normalize_metrics(data: dict) -> dict:
    out = {}
    for key, value in data.items():
        if isinstance(value, bool):
            raise ValueError(f"metric {key} must not be boolean")
        if isinstance(value, (int, float)):
            number = float(value)
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"metric {key} must be finite and >=0")
            out[str(key)] = int(number) if number.is_integer() else number
    if not out:
        raise ValueError("no numeric metrics supplied")
    return out


def load_metrics_input(metrics_file: str | None, pairs: list[str]) -> dict:
    merged = {}
    if metrics_file:
        p = Path(metrics_file).expanduser().resolve()
        data = read_json(p)
        # Accept either flat object or {"metrics": {...}}
        source = data.get("metrics") if isinstance(data.get("metrics"), dict) else data
        merged.update(normalize_metrics(source))
    merged.update(parse_metric_pairs(pairs))
    return normalize_metrics(merged)


def metrics_store(ep: Path) -> dict:
    p = ep / METRICS_REL
    if p.is_file():
        d = read_json(p)
        d.setdefault("checkpoints", {})
        return d
    event = read_json(ep / EVENT_REL) if (ep / EVENT_REL).is_file() else {}
    return {
        "schema_version": 1,
        "published_at": event.get("published_at"),
        "platform": event.get("platform"),
        "checkpoints": {},
        "note": "Raw platform observations; no creative authority.",
    }


def previous_checkpoint(store: dict, checkpoint: str) -> tuple[str, dict] | None:
    current_idx = CHECKPOINT_ORDER[checkpoint]
    candidates = []
    for cp, row in (store.get("checkpoints") or {}).items():
        if cp in CHECKPOINT_ORDER and CHECKPOINT_ORDER[cp] < current_idx and isinstance(row, dict):
            candidates.append((CHECKPOINT_ORDER[cp], cp, row))
    if not candidates:
        return None
    _, cp, row = max(candidates)
    return cp, row


def record(ep: Path, checkpoint: str, metrics: dict, source: str) -> dict:
    if checkpoint not in CHECKPOINT_ORDER:
        raise ValueError(f"checkpoint must be one of {CHECKPOINTS}")
    if state(ep) not in {"PUBLISHED", "DATA_REVIEWED"}:
        raise ValueError("metrics can only be recorded after PUBLISHED")
    if not (ep / EVENT_REL).is_file():
        raise ValueError("publish-event missing; run mark-published first")
    store = metrics_store(ep)
    corrections = []
    prev = previous_checkpoint(store, checkpoint)
    if prev:
        prev_cp, prev_row = prev
        old = prev_row.get("metrics") or {}
        for key in CUMULATIVE_KEYS & metrics.keys() & old.keys():
            if float(metrics[key]) < float(old[key]):
                corrections.append({
                    "metric": key,
                    "previous_checkpoint": prev_cp,
                    "previous_value": old[key],
                    "current_value": metrics[key],
                    "note": "Platform counters can be revised; decrease retained as factual correction.",
                })
    row = {
        "checkpoint": checkpoint,
        "captured_at": now(),
        "source": source,
        "metrics": metrics,
        "counter_corrections": corrections,
    }
    store["checkpoints"][checkpoint] = row
    store["updated_at"] = now()
    write_json(ep / METRICS_REL, store)
    return row


def safe_rate(numerator: object, denominator: object) -> float | None:
    try:
        n = float(numerator)
        d = float(denominator)
        if d <= 0:
            return None
        return round(n / d, 6)
    except (TypeError, ValueError):
        return None


def derive_rates(metrics: dict) -> dict:
    views = metrics.get("views")
    mapping = {
        "like_rate": "likes",
        "comment_rate": "comments",
        "share_rate": "shares",
        "save_rate": "saves" if "saves" in metrics else "favorites",
        "follow_rate": "followers_gained",
        "profile_visit_rate": "profile_visits",
    }
    out = {}
    for rate, key in mapping.items():
        value = safe_rate(metrics.get(key), views)
        if value is not None:
            out[rate] = value
    if "completion_rate" in metrics:
        out["completion_rate"] = round(float(metrics["completion_rate"]), 6)
    return out


# STORY_OS_V2_5_PROPAGATION_CORE
def metric_triplets(metrics: dict, previous_metrics: dict | None, rates: dict) -> dict:
    # Absolute -> delta -> efficiency/rate. Missing facts stay missing.
    out = {}
    for key in ("views","likes","comments","saves","favorites","shares","followers_gained","followers_lost","profile_visits"):
        if key not in metrics:
            continue
        row = {"absolute": metrics[key]}
        if previous_metrics and key in previous_metrics:
            row["delta_vs_previous"] = metrics[key] - previous_metrics[key]
        rate_key = {
            "likes":"like_rate",
            "comments":"comment_rate",
            "saves":"save_rate",
            "favorites":"save_rate",
            "shares":"share_rate",
            "followers_gained":"follow_rate",
            "profile_visits":"profile_visit_rate"
        }.get(key)
        if rate_key and rate_key in rates:
            row["rate_per_view"] = rates[rate_key]
            row["per_1000_views"] = round(rates[rate_key] * 1000, 3)
        out[key] = row
    return out


def funnel_groups(metrics: dict, rates: dict) -> dict:
    return {
        "L1_entry": {
            "views": metrics.get("views"),
            "swipe_away_rate": metrics.get("swipe_away_rate"),
            "cover_click_rate": metrics.get("cover_click_rate"),
            "recommendation_traffic_rate": metrics.get("recommendation_traffic_rate"),
        },
        "L2_depth": {
            "avg_browsed_images": metrics.get("avg_browsed_images"),
            "completion_rate": metrics.get("completion_rate"),
            "copy_expand_rate": metrics.get("copy_expand_rate"),
        },
        "L3A_recognition": {
            "likes": metrics.get("likes"),
            "comments": metrics.get("comments"),
            "saves": metrics.get("saves", metrics.get("favorites")),
            "like_rate": rates.get("like_rate"),
            "comment_rate": rates.get("comment_rate"),
            "save_rate": rates.get("save_rate"),
        },
        "L3B_propagation": {
            "shares": metrics.get("shares"),
            "share_rate": rates.get("share_rate"),
            "shares_per_1000_views": (
                round(rates["share_rate"] * 1000, 3)
                if rates.get("share_rate") is not None else None
            ),
        },
        "L4_author_chain": {
            "profile_visits": metrics.get("profile_visits"),
            "followers_gained": metrics.get("followers_gained"),
            "followers_lost": metrics.get("followers_lost"),
            "profile_visit_rate": rates.get("profile_visit_rate"),
            "follow_rate": rates.get("follow_rate"),
        },
    }


def concept_binding(ep: Path) -> dict:
    p = ep / "meta/concept-ambition-review.json"
    if not p.is_file():
        return {}
    d = read_json(p)
    return {
        "selected_id": d.get("selected_id"),
        "selected_title": d.get("selected_title"),
        "selected_band": d.get("selected_band"),
        "concept_voltage": d.get("concept_voltage") or ((d.get("selected") or {}).get("concept_voltage")),
    }


def review(ep: Path) -> dict:
    store = metrics_store(ep)
    checkpoints = store.get("checkpoints") or {}
    if not checkpoints:
        raise ValueError("no post-publish metrics recorded")
    rows = []
    previous = None
    for cp in CHECKPOINTS:
        raw = checkpoints.get(cp)
        if not isinstance(raw, dict):
            continue
        metrics = raw.get("metrics") or {}
        rates = derive_rates(metrics)
        growth = {}
        if previous:
            prev_cp, prev_metrics, prev_rates = previous
            for key in ("views", "likes", "comments", "shares", "saves", "followers_gained"):
                if key in metrics and key in prev_metrics:
                    growth[f"{key}_delta"] = metrics[key] - prev_metrics[key]
            if "views" in metrics and "views" in prev_metrics and float(prev_metrics["views"]) > 0:
                growth["views_growth_ratio"] = round((float(metrics["views"]) - float(prev_metrics["views"])) / float(prev_metrics["views"]), 6)
            for key, value in rates.items():
                if key in prev_rates:
                    growth[f"{key}_delta"] = round(value - prev_rates[key], 6)
        prev_metrics_for_triplet = previous[1] if previous else None
        rows.append({
            "checkpoint": cp,
            "captured_at": raw.get("captured_at"),
            "metrics": metrics,
            "rates": rates,
            "growth_vs_previous": growth,
            "metric_triplets": metric_triplets(metrics, prev_metrics_for_triplet, rates),
            "funnel": funnel_groups(metrics, rates),
            "counter_corrections": raw.get("counter_corrections") or [],
        })
        previous = (cp, metrics, rates)

    latest = rows[-1]
    rate_items = sorted(
        [(k, v) for k, v in (latest.get("rates") or {}).items() if k.endswith("_rate") and k != "completion_rate"],
        key=lambda x: x[1],
        reverse=True,
    )
    factual_signals = []
    if rate_items:
        factual_signals.append({
            "type": "highest_observed_engagement_rate",
            "metric": rate_items[0][0],
            "value": rate_items[0][1],
            "note": "Descriptive only; not a universal benchmark.",
        })
    if "completion_rate" in latest.get("rates", {}):
        factual_signals.append({
            "type": "completion_rate_observed",
            "value": latest["rates"]["completion_rate"],
            "note": "Use comparatively against the account's own history.",
        })
    event = read_json(ep / EVENT_REL)
    manifest = read_json(ep / "meta/release-manifest.json")
    result = {
        "schema_version": 1,
        "generated_at": now(),
        "episode": (manifest.get("episode") or {}),
        "published_at": event.get("published_at"),
        "platform": event.get("platform"),
        "completed_checkpoints": [x["checkpoint"] for x in rows],
        "latest_checkpoint": latest["checkpoint"],
        "checkpoints": rows,
        "factual_signals": factual_signals,
        "authority": "descriptive post-publish evidence only",
    }
    write_json(ep / REVIEW_REL, result)

    learning = {
        "schema_version": 1,
        "generated_at": now(),
        "source_episode": (manifest.get("episode") or {}),
        "published_at": event.get("published_at"),
        "platform": event.get("platform"),
        "latest_checkpoint": latest["checkpoint"],
        "latest_metrics": latest["metrics"],
        "latest_rates": latest["rates"],
        "factual_signals": factual_signals,
        "concept_binding": concept_binding(ep),
        "evidence_only": True,
        "direct_creative_authority": False,
        "next_story_use": [
            "Compare against the account's other completed episodes.",
            "Use as evidence when selecting mechanisms/hooks, not as a rule that forces repetition.",
            "Do not lower Concept Ambition merely because a prior high-ambition episode underperformed.",
        ],
    }
    write_json(ep / LEARNING_REL, learning)
    return result


def verify(ep: Path, *, require_48h: bool = False) -> list[str]:
    errors = []
    if not (ep / EVENT_REL).is_file():
        errors.append("meta/publish-event.json missing")
        return errors
    event = read_json(ep / EVENT_REL)
    if not isinstance(event.get("published_at"), str) or not event.get("published_at", "").strip():
        errors.append("publish-event.published_at missing")
    if not (ep / METRICS_REL).is_file():
        if require_48h:
            errors.append("meta/post-publish-metrics.json missing")
        return errors
    store = read_json(ep / METRICS_REL)
    cps = store.get("checkpoints") or {}
    if require_48h and "48h" not in cps:
        errors.append("48h checkpoint required for DATA_REVIEWED")
    if (ep / REVIEW_REL).is_file():
        review_data = read_json(ep / REVIEW_REL)
        completed = review_data.get("completed_checkpoints") or []
        if require_48h and "48h" not in completed:
            errors.append("post-publish review is stale or missing 48h")
    elif require_48h:
        errors.append("meta/post-publish-review.json missing")
    if require_48h and not (ep / LEARNING_REL).is_file():
        errors.append("meta/next-story-learning.json missing")
    return errors


def complete(ep: Path) -> dict:
    current = state(ep)
    if current not in {"PUBLISHED", "DATA_REVIEWED"}:
        raise ValueError(f"complete requires PUBLISHED or DATA_REVIEWED, got {current}")
    result = review(ep)
    errors = verify(ep, require_48h=True)
    if errors:
        raise ValueError("; ".join(errors))
    completed = result.get("completed_checkpoints") or []
    data_state = {
        "schema_version": 1,
        "completed_at": now(),
        "report_path": rel(ep / REVIEW_REL),
        "learning_path": rel(ep / LEARNING_REL),
        "metrics_path": rel(ep / METRICS_REL),
        "completed_checkpoints": completed,
        "required_for_data_reviewed": list(REQUIRED_FOR_DATA_REVIEWED),
        "release_manifest_mutated": False,
        "final_candidate_snapshot_remains_frozen": True,
    }
    write_json(ep / STATE_REL, data_state)
    if current == "PUBLISHED":
        gate_transition(ep, "DATA_REVIEWED", "Phase10 48h minimum data review complete; learning packet generated")
    return data_state


def self_test() -> None:
    assert CHECKPOINTS == ("6h", "24h", "48h", "7d")
    assert REQUIRED_FOR_DATA_REVIEWED == ("48h",)
    assert derive_rates({"views": 100, "likes": 10, "comments": 2})["like_rate"] == 0.1
    _rates = derive_rates({"views":1000,"shares":5,"followers_gained":2})
    assert metric_triplets({"views":1000,"shares":5}, None, _rates)["shares"]["per_1000_views"] == 5.0
    assert funnel_groups({"views":1000,"shares":5}, _rates)["L3B_propagation"]["shares"] == 5
    assert MANIFEST_MUTATION_POLICY == "FORBIDDEN_AFTER_SNAPSHOT"
    print("POST PUBLISH REVIEW V2.1 PHASE10 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("enable"); p.add_argument("episode_dir")
    p = sub.add_parser("mark-published"); p.add_argument("episode_dir"); p.add_argument("--published-at"); p.add_argument("--platform"); p.add_argument("--post-id"); p.add_argument("--post-url"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("record"); p.add_argument("episode_dir"); p.add_argument("checkpoint", choices=CHECKPOINTS); p.add_argument("--metrics-file"); p.add_argument("--metric", action="append", default=[]); p.add_argument("--source", default="manual")
    p = sub.add_parser("review"); p.add_argument("episode_dir")
    p = sub.add_parser("complete"); p.add_argument("episode_dir")
    p = sub.add_parser("verify"); p.add_argument("episode_dir"); p.add_argument("--require-48h", action="store_true")
    p = sub.add_parser("show"); p.add_argument("episode_dir"); p.add_argument("--kind", choices=["event","metrics","review","learning","state"], default="review")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test":
        self_test(); return 0
    ep = resolve_ep(a.episode_dir)
    try:
        if a.cmd == "enable":
            print(json.dumps(enable(ep), ensure_ascii=False, indent=2)); return 0
        if a.cmd == "mark-published":
            print(json.dumps(mark_published(ep, published_at=a.published_at, platform=a.platform, post_id=a.post_id, post_url=a.post_url, force=a.force), ensure_ascii=False, indent=2)); return 0
        if a.cmd == "record":
            metrics = load_metrics_input(a.metrics_file, a.metric)
            print(json.dumps(record(ep, a.checkpoint, metrics, a.source), ensure_ascii=False, indent=2)); return 0
        if a.cmd == "review":
            print(json.dumps(review(ep), ensure_ascii=False, indent=2)); return 0
        if a.cmd == "complete":
            print(json.dumps(complete(ep), ensure_ascii=False, indent=2)); return 0
        if a.cmd == "verify":
            errors = verify(ep, require_48h=a.require_48h)
            if errors:
                for e in errors: print("FAIL:", e)
                return 2
            print("POST PUBLISH REVIEW VERIFY PASS"); return 0
        rels = {"event":EVENT_REL,"metrics":METRICS_REL,"review":REVIEW_REL,"learning":LEARNING_REL,"state":STATE_REL}
        p = ep / rels[a.kind]
        print(p.read_text(encoding="utf-8") if p.is_file() else "{}"); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("POST PUBLISH ERROR:", exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
