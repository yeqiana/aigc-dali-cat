#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"runtimes"/"runtime-contract.json"
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("detect"); sub.add_parser("contract")
    p=sub.add_parser("show"); p.add_argument("runtime",choices=["CODEX","WORK","WEB"])
    a=ap.parse_args()
    if a.cmd=="detect":
        print("CODEX"); return 0
    if a.cmd=="contract":
        print(CONTRACT.read_text(encoding="utf-8")); return 0
    print((ROOT/"runtimes"/f"{a.runtime}.md").read_text(encoding="utf-8")); return 0
if __name__=="__main__": raise SystemExit(main())
