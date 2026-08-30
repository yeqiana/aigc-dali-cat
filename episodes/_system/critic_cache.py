#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SHA-bound reusable critic evidence index for Story OS V2.1.

The cache is recovery/acceleration evidence only and never an episode stage source.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

REL = Path("meta/critic-cache.json")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_key(critic_type: str, contract_version: str, inputs: dict) -> str:
    return canonical_hash({"critic_type": critic_type, "contract_version": contract_version, "inputs": inputs})


def read_cache(ep: Path) -> dict:
    path = ep / REL
    if not path.is_file():
        return {"schema_version": 1, "note": "Acceleration evidence only; NOT a stage source.", "entries": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("critic cache root must be object")
    data.setdefault("entries", {})
    return data


def write_cache(ep: Path, data: dict) -> None:
    path = ep / REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def get(ep: Path, key: str) -> dict | None:
    row = (read_cache(ep).get("entries") or {}).get(key)
    return row if isinstance(row, dict) else None


def put(ep: Path, *, critic_type: str, contract_version: str, inputs: dict, evidence_path: str, evidence_sha256: str, passed: bool) -> str:
    data = read_cache(ep)
    key = make_key(critic_type, contract_version, inputs)
    data["entries"][key] = {
        "critic_type": critic_type,
        "contract_version": contract_version,
        "inputs": inputs,
        "evidence_path": evidence_path,
        "evidence_sha256": evidence_sha256,
        "passed": bool(passed),
        "cached_at": now(),
    }
    data["updated_at"] = now()
    write_cache(ep, data)
    return key


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    p = sub.add_parser("key"); p.add_argument("critic_type"); p.add_argument("contract_version"); p.add_argument("inputs_json")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        a = make_key("story", "1", {"a": "b", "x": 1})
        b = make_key("story", "1", {"x": 1, "a": "b"})
        assert a == b and len(a) == 64
        print("CRITIC CACHE SELF-TEST PASS")
        return 0
    if args.cmd == "key":
        print(make_key(args.critic_type, args.contract_version, json.loads(args.inputs_json)))
        return 0
    ep = Path(args.episode_dir).resolve()
    print(json.dumps(read_cache(ep), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
