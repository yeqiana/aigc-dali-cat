#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atomic candidate budget + candidate lifecycle for Story OS V2.6.0."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import runtime_atomic_store as atomic

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/runtime/raw-candidate-budget.json")
CFG = ROOT / "runtimes/runtime-fast-path-v251.json"
KINDS = {"original", "repair", "exception"}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def limits() -> dict:
    try:
        return _read_json(CFG).get("raw_candidate_budget") or {"original": 2, "repair": 2, "exception": 2}
    except Exception:
        return {"original": 2, "repair": 2, "exception": 2}

def frame_count(ep: Path) -> int:
    ep = Path(ep)
    for rel in ("meta/episode-state.json", "meta/release-manifest.json"):
        d = _read_json(ep / rel)
        for key in ("frame_count", "body_frame_count"):
            raw = d.get(key)
            if isinstance(raw, int) and raw > 0:
                return raw
        release = d.get("release") or {}
        raw = release.get("body_frame_count")
        if isinstance(raw, int) and raw > 0:
            return raw
    ledger = _read_json(ep / "meta/production-ledger.json")
    frames = ledger.get("frames") or {}
    if isinstance(frames, dict) and frames:
        return len(frames)
    return 20

def episode_limit(ep: Path) -> int:
    cfg = _read_json(CFG)
    fixed = ((cfg.get("episode_candidate_budget") or {}).get("max_total_content_candidates"))
    if isinstance(fixed, int) and fixed > 0:
        return fixed
    count = frame_count(Path(ep))
    return min(60, max(20, count + 15))

def default_state() -> dict:
    return {
        "schema_version": 3,
        "module_version": "2.6.0",
        "updated_at": now(),
        "frames": {},
        "events": [],
    }

def _upgrade_state(d: dict) -> dict:
    old_schema = int(d.get("schema_version") or 0)
    d.setdefault("frames", {})
    d.setdefault("events", [])
    if old_schema < 3:
        # V2.5.1.1 had no commit lifecycle. Existing retained claims already consumed
        # content budget, so migrate them conservatively as committed.
        for _frame, kinds in (d.get("frames") or {}).items():
            for _kind, bucket in (kinds or {}).items():
                bucket.setdefault("claims", {})
                for _token, row in (bucket.get("claims") or {}).items():
                    if isinstance(row, dict):
                        row.setdefault("committed", True)
                        row.setdefault("committed_at", row.get("at") or row.get("claimed_at") or now())
    d["schema_version"] = 3
    d["module_version"] = "2.6.0"
    return d

def load(ep: Path) -> dict:
    d = atomic.read_json(Path(ep).resolve() / REL, default_state())
    if not isinstance(d, dict):
        d = default_state()
    return _upgrade_state(d)

def kind_for_queue_item(item: dict) -> str:
    return "repair" if str((item or {}).get("kind") or "").lower() == "repair" else "original"

def _all_claims(d: dict):
    for frame, kinds in (d.get("frames") or {}).items():
        for kind, bucket in (kinds or {}).items():
            for token, row in ((bucket or {}).get("claims") or {}).items():
                yield frame, kind, bucket, token, row

def _find_token(d: dict, token: str):
    for row in _all_claims(d):
        if row[3] == token:
            return row
    return None

def _reserved_total(d: dict) -> int:
    return sum(1 for *_prefix, row in _all_claims(d) if isinstance(row, dict))

def claim(ep, frame, kind, reason="", token=None):
    ep = Path(ep).resolve()
    if kind not in KINDS:
        raise ValueError(f"kind must be {sorted(KINDS)}")
    key = f"{int(frame):02d}"
    token = str(token or "").strip() or f"{key}:{kind}:{int(dt.datetime.now().timestamp()*1000000)}"
    result = {}

    def mutate(d: dict):
        _upgrade_state(d)
        found = _find_token(d, token)
        if found:
            f, k, bucket, _, row = found
            result.update({
                "frame": f, "kind": k, "used": int(bucket.get("used") or 0),
                "limit": int(limits().get(k, 2)), "decision": "REUSE_CLAIM",
                "token": token, "committed": bool((row or {}).get("committed")),
            })
            return

        bucket = d["frames"].setdefault(key, {}).setdefault(kind, {"used": 0, "claims": {}})
        bucket.setdefault("claims", {})
        per_kind_limit = int(limits().get(kind, 2))
        if int(bucket.get("used") or 0) >= per_kind_limit:
            result.update({
                "frame": key, "kind": kind, "used": int(bucket.get("used") or 0),
                "limit": per_kind_limit, "decision": "STOP_IMAGE_LOOP", "token": token,
            })
            return

        total_limit = episode_limit(ep)
        total_now = _reserved_total(d)
        if total_now >= total_limit:
            result.update({
                "frame": key, "kind": kind, "used": int(bucket.get("used") or 0),
                "limit": per_kind_limit, "episode_used": total_now,
                "episode_limit": total_limit, "decision": "EPISODE_IMAGE_LOOP_GUARD", "token": token,
            })
            return

        bucket["used"] = int(bucket.get("used") or 0) + 1
        bucket["claims"][token] = {
            "claimed_at": now(), "reason": reason, "committed": False, "committed_at": None
        }
        d["updated_at"] = now()
        d["events"].append({"at": now(), "event": "claim", "frame": key, "kind": kind, "token": token})
        result.update({
            "frame": key, "kind": kind, "used": bucket["used"], "limit": per_kind_limit,
            "episode_used": total_now + 1, "episode_limit": total_limit,
            "decision": "ALLOW", "token": token, "committed": False,
        })

    atomic.update_json(ep / REL, default_state, mutate)
    return result.get("decision") in {"ALLOW", "REUSE_CLAIM"}, result

def commit(ep, token, reason="candidate_file_committed"):
    ep = Path(ep).resolve()
    token = str(token or "").strip()
    result = {}

    def mutate(d: dict):
        _upgrade_state(d)
        found = _find_token(d, token)
        if not found:
            result.update({"decision": "TOKEN_NOT_FOUND", "token": token})
            return
        frame, kind, _bucket, _tok, row = found
        if row.get("committed") is True:
            result.update({"decision": "ALREADY_COMMITTED", "token": token, "frame": frame, "kind": kind})
            return
        row["committed"] = True
        row["committed_at"] = now()
        row["commit_reason"] = reason
        d["updated_at"] = now()
        d.setdefault("events", []).append({"at": now(), "event": "commit", "frame": frame, "kind": kind, "token": token})
        result.update({"decision": "COMMITTED", "token": token, "frame": frame, "kind": kind})

    atomic.update_json(ep / REL, default_state, mutate)
    return result.get("decision") in {"COMMITTED", "ALREADY_COMMITTED"}, result

def release(ep, token, reason="technical_failure_before_candidate_commit"):
    ep = Path(ep).resolve()
    token = str(token or "").strip()
    result = {}

    def mutate(d: dict):
        _upgrade_state(d)
        found = _find_token(d, token)
        if not found:
            result.update({"decision": "TOKEN_NOT_FOUND", "token": token})
            return
        frame, kind, bucket, _tok, row = found
        if row.get("committed") is True:
            result.update({"decision": "COMMITTED_NOT_RELEASED", "token": token, "frame": frame, "kind": kind})
            return
        bucket.get("claims", {}).pop(token, None)
        bucket["used"] = max(0, int(bucket.get("used") or 0) - 1)
        d["updated_at"] = now()
        d.setdefault("events", []).append({"at": now(), "event": "release", "frame": frame, "kind": kind, "token": token, "reason": reason})
        result.update({"decision": "RELEASED", "token": token, "frame": frame, "kind": kind, "used": bucket["used"]})

    atomic.update_json(ep / REL, default_state, mutate)
    return result.get("decision") == "RELEASED", result

def self_test():
    import tempfile, threading
    with tempfile.TemporaryDirectory(prefix="candidate budget 并发 ") as td:
        ep = Path(td)
        results = []
        def one(i):
            results.append(claim(ep, i + 1, "original", token=f"q{i}"))
        threads = [threading.Thread(target=one, args=(i,)) for i in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(results) == 5 and all(x[0] for x in results)
        ok, row = commit(ep, "q0")
        assert ok and row["decision"] == "COMMITTED"
        ok, row = release(ep, "q0")
        assert not ok and row["decision"] == "COMMITTED_NOT_RELEASED"
        ok, _ = release(ep, "q1")
        assert ok
    print("RAW CANDIDATE BUDGET V2.6.0 ATOMIC LIFECYCLE SELF-TEST PASS")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("claim"); p.add_argument("episode_dir"); p.add_argument("--frame", required=True, type=int)
    p.add_argument("--kind", required=True, choices=sorted(KINDS)); p.add_argument("--reason", default=""); p.add_argument("--token")
    p = sub.add_parser("commit"); p.add_argument("episode_dir"); p.add_argument("--token", required=True); p.add_argument("--reason", default="candidate_file_committed")
    p = sub.add_parser("release"); p.add_argument("episode_dir"); p.add_argument("--token", required=True); p.add_argument("--reason", default="technical_failure_before_candidate_commit")
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return 0
    if a.cmd == "show": print(json.dumps(load(Path(a.episode_dir)), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "claim":
        ok, row = claim(a.episode_dir, a.frame, a.kind, a.reason, a.token)
    elif a.cmd == "commit":
        ok, row = commit(a.episode_dir, a.token, a.reason)
    else:
        ok, row = release(a.episode_dir, a.token, a.reason)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
