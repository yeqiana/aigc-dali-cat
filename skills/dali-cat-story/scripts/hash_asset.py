from __future__ import annotations
import argparse
from pathlib import Path
from _common import sha256_file

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("files",nargs="+",type=Path);a=ap.parse_args()
    for p in a.files:
        p=p.resolve()
        if not p.is_file():print(f"MISSING {p}");continue
        print(f"{sha256_file(p)}  {p}")
    return 0
if __name__=="__main__":raise SystemExit(main())
