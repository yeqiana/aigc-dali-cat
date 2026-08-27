from __future__ import annotations

import argparse
from pathlib import Path
import validate_all

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("repo",nargs="?",default=".",type=Path);ap.add_argument("--release",action="store_true")
    a=ap.parse_args();repo=a.repo.resolve();manifests=sorted((repo/"episodes").rglob("episode.yaml")) if (repo/"episodes").exists() else []
    if not manifests:
        print("[PASS] 未发现 episode.yaml；旧剧集保持兼容。新篇建议开始使用 manifest。")
        return 0
    failed=0
    for m in manifests:
        print(f"\n=== {m.relative_to(repo)} ===")
        r=validate_all.validate(m,release=a.release);r.print();failed+=0 if r.ok else 1
    print(f"\nchecked={len(manifests)} failed={failed}")
    return 1 if failed else 0
if __name__=="__main__":raise SystemExit(main())
