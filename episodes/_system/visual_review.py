#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility dispatcher: legacy Visual Profile Review vs Story OS V2.1 four-admission Visual Lock."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def version_tuple(raw):
    try: return tuple(int(x) for x in str(raw or "").split("."))
    except Exception: return (0,)


def is_v21(ep: Path) -> bool:
    versions=[]
    for rel in ("meta/episode-state.json","meta/release-manifest.json","meta/story-gates.json"):
        p=ep/rel
        if p.is_file():
            try: versions.append(version_tuple(read_json(p).get("tool_version")))
            except Exception: pass
    if not (versions and max(versions) >= (2,1,0)):
        return False
    gates = ep / "meta/story-gates.json"
    if not gates.is_file():
        return False
    try:
        calibration = ((read_json(gates).get("visual") or {}).get("calibration") or {})
        return calibration.get("policy") == "four_admission_v21"
    except Exception:
        return False


def review_required(ep: Path) -> bool:
    if is_v21(ep):
        return True
    import visual_review_legacy as legacy
    return legacy.review_required(ep)


def verify(ep: Path) -> list[str]:
    if is_v21(ep):
        from visual_lock_v21 import verify as v
        return v(ep)
    import visual_review_legacy as legacy
    return legacy.verify(ep)


def forward(script: str, args: list[str]) -> int:
    return subprocess.call([sys.executable, str(SYSTEM/script), *args], cwd=ROOT)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("run-critic");p.add_argument("episode_dir");p.add_argument("--attempt",type=int,default=1);p.add_argument("--codex");p.add_argument("--timeout",type=int,default=900)
    p=sub.add_parser("verify");p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":
        rc=forward("visual_lock_v21.py",["self-test"])
        if rc:return rc
        return forward("visual_review_legacy.py",["self-test"])
    ep=Path(a.episode_dir).resolve()
    target="visual_lock_v21.py" if is_v21(ep) else "visual_review_legacy.py"
    if a.cmd=="verify": return forward(target,["verify",str(ep)])
    args=["run-critic",str(ep),"--attempt",str(a.attempt),"--timeout",str(a.timeout)]
    if a.codex:args += ["--codex",a.codex]
    return forward(target,args)


if __name__=="__main__": raise SystemExit(main())
