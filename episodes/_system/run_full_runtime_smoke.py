#!/usr/bin/env python3
"""Compatibility CLI for measured, non-authoritative runtime regression evidence."""
import argparse
import json
from runtime_smoke_runner import run_smoke


def run(output="runtime-smoke-report.json"):
    return run_smoke(output)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="runtime-smoke-report.json")
    args=parser.parse_args()
    report=run(args.output)
    print(json.dumps(report,ensure_ascii=True,indent=2))
    raise SystemExit(0 if report["result"]=="PASS" else 1)
